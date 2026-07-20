import asyncio
import logging
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


_ANY_ITEM_SCHEMA: dict[str, Any] = {"type": "string"}


def _normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON schema that Gemini's function-declaration parser accepts.

    Gemini (via langchain-google-genai) requires every `type: array` to carry a
    non-empty `items` schema. FastMCP emits `items: {}` for `list[Any]`, and
    langchain-google-genai drops empty dicts (see `_dict_to_genai_schema`
    truthiness check). We replace missing/empty `items` with a permissive
    `{"type": "string"}` so tools like `tool_append_rows(data: list[list[Any]])`
    survive the Gemini round-trip.
    """
    if not isinstance(schema, dict):
        return schema

    out = dict(schema)
    if out.get("type") == "array":
        items = out.get("items")
        if not isinstance(items, dict) or not items:
            out["items"] = dict(_ANY_ITEM_SCHEMA)

    for key in ("items", "additionalProperties"):
        value = out.get(key)
        if isinstance(value, dict):
            out[key] = _normalize_schema(value)

    for key in ("properties", "definitions", "$defs"):
        nested = out.get(key)
        if isinstance(nested, dict):
            out[key] = {k: _normalize_schema(v) for k, v in nested.items()}

    for key in ("anyOf", "oneOf", "allOf"):
        values = out.get(key)
        if isinstance(values, list):
            out[key] = [_normalize_schema(v) for v in values]

    return out


class MCPToolRegistry:
    """Connects to an MCP server (SSE or stdio) and exposes tools as LangChain tools.

    Default constructor accepts a SSE URL (legacy positional form so existing
    call sites and tests keep working). For stdio transport, use
    ``MCPToolRegistry.from_stdio(...)`` which spawns the MCP server as a
    subprocess and pipes JSON-RPC over stdin/stdout. Stdio avoids the SSE
    idle-timeout class of failures (Errno 32 broken pipe) we saw in
    production traces because there is no long-lived HTTP stream to drop.
    """

    def __init__(
        self,
        name: str,
        url: str | None = None,
        *,
        stdio_command: str | None = None,
        stdio_args: list[str] | None = None,
        stdio_cwd: str | None = None,
        stdio_env: dict[str, str] | None = None,
    ) -> None:
        if not url and not stdio_command:
            raise ValueError(
                "MCPToolRegistry needs either url (SSE) or stdio_command (stdio)"
            )
        self._name = name
        self._url = url
        self._stdio_command = stdio_command
        self._stdio_args = stdio_args or []
        self._stdio_cwd = stdio_cwd
        self._stdio_env = stdio_env
        self._session: ClientSession | None = None
        self._tools: list[BaseTool] = []
        self._task: asyncio.Task | None = None
        self._ready = asyncio.Event()
        self._shutdown = asyncio.Event()

    @classmethod
    def from_stdio(
        cls,
        name: str,
        command: str,
        args: list[str],
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> "MCPToolRegistry":
        """Build a registry that spawns the MCP server via stdio subprocess."""
        return cls(
            name,
            stdio_command=command,
            stdio_args=args,
            stdio_cwd=cwd,
            stdio_env=env,
        )

    async def connect(self) -> None:
        """Connect to MCP server and discover tools via a background task."""
        self._task = asyncio.create_task(self._run())
        await self._ready.wait()

    async def _run(self) -> None:
        """Background task that owns the connection lifecycle (SSE or stdio)."""
        try:
            if self._url:
                transport_label = f"sse {self._url}"
                async with sse_client(self._url) as (read_stream, write_stream):
                    await self._serve(read_stream, write_stream, transport_label)
            else:
                params = StdioServerParameters(
                    command=self._stdio_command,
                    args=self._stdio_args,
                    cwd=self._stdio_cwd,
                    env=self._stdio_env,
                )
                transport_label = (
                    f"stdio {self._stdio_command} {' '.join(self._stdio_args)}"
                )
                async with stdio_client(params) as (read_stream, write_stream):
                    await self._serve(read_stream, write_stream, transport_label)

            logger.info(f"MCP {self._name}: disconnected ({transport_label})")
        except Exception as e:
            logger.error(f"MCP {self._name}: connection failed: {e}")
            self._ready.set()  # Unblock waiter even on failure

    async def _serve(self, read_stream: Any, write_stream: Any, label: str) -> None:
        """Initialise an MCP session on the given streams and keep it alive."""
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            self._session = session

            tools_response = await session.list_tools()
            for tool_info in tools_response.tools:
                self._tools.append(self._wrap_tool(tool_info))
            logger.info(
                f"MCP {self._name}: connected via {label}, "
                f"{len(self._tools)} tools discovered"
            )

            self._ready.set()
            await self._shutdown.wait()

    def _wrap_tool(self, tool_info: Any) -> BaseTool:
        """Wrap an MCP tool as a LangChain StructuredTool with a real args schema."""
        session = self._session
        tool_name = tool_info.name
        input_schema = getattr(tool_info, "inputSchema", None) or {}
        # Pass the MCP JSON schema directly — langchain ArgsSchema accepts dict.
        # This preserves nested `items` that Pydantic drops for bare `list`.
        args_schema = _normalize_schema(input_schema)

        async def _call(**kwargs: Any) -> str:
            # Strip None values so MCP tools see only explicit args.
            clean = {k: v for k, v in kwargs.items() if v is not None}
            result = await session.call_tool(tool_name, clean)
            if result.content:
                # Concatenate all text content blocks (some tools emit one per row).
                return "\n".join(c.text for c in result.content if hasattr(c, "text"))
            return ""

        return StructuredTool.from_function(
            coroutine=_call,
            name=tool_name,
            description=tool_info.description or f"MCP tool: {tool_name}",
            args_schema=args_schema,
        )

    @property
    def tools(self) -> list[BaseTool]:
        return self._tools

    async def disconnect(self) -> None:
        self._shutdown.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (asyncio.TimeoutError, Exception):
                self._task.cancel()
        logger.info(f"MCP {self._name}: shutdown complete")
