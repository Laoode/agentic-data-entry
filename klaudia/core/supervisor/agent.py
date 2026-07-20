import json
import logging
import time
from typing import Any, AsyncIterator, Optional

from langchain_core.messages import AIMessage
from langgraph.graph import START, StateGraph

from klaudia.core.supervisor._content import coerce_to_text, strip_internal_markers
from klaudia.core.supervisor.agents.data_entry_team.agents import (
    make_data_entry_team_node,
)
from klaudia.core.supervisor.agents.sql_agent.agent import make_sql_agent_node
from klaudia.core.supervisor.llm import build_chat_llm
from klaudia.core.supervisor.router import make_supervisor_node
from klaudia.core.supervisor.state import SupervisorState
from klaudia.interfaces.tool_registry import MCPToolRegistry
from klaudia.models.message import AgentResponse

logger = logging.getLogger(__name__)

_FALLBACK_NAMES = (
    "data_entry_team",
    "sql_agent",
    "read_agent",
    "sheet_agent",
    "write_agent",
)


def _resolve_final_content(messages: list[Any]) -> str:
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, AIMessage):
        text = coerce_to_text(last.content)
        if text:
            return text
    for msg in reversed(messages):
        if getattr(msg, "name", None) in _FALLBACK_NAMES:
            text = strip_internal_markers(coerce_to_text(getattr(msg, "content", "")))
            if text:
                return text
    return ""


def _parse_tool_json_output(raw: Any) -> list[dict]:
    """Parse MCP tool_list_sheets output into a list of sheet dicts.

    The MCP server serialises each sheet as a separate JSON object and
    concatenates them with spaces — NOT a JSON array. json.loads() fails with
    "Extra data" on this format. We use JSONDecoder.raw_decode() to walk through.
    Handles:
        - Already a Python list      → return as-is
        - Proper JSON array string   → json.loads
        - Concatenated JSON objects  → iterative raw_decode
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    if not isinstance(raw, str):
        return []

    stripped = raw.strip()
    if not stripped:
        return []

    # Fast path: proper JSON array
    try:
        result = json.loads(stripped)
        if isinstance(result, list):
            return result
        return [result] if isinstance(result, dict) else []
    except json.JSONDecodeError:
        pass

    # Slow path: space/newline-separated JSON objects
    objects: list[dict] = []
    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(stripped):
        remaining = stripped[pos:].lstrip()
        if not remaining:
            break
        whitespace_skipped = len(stripped[pos:]) - len(remaining)
        try:
            obj, end = decoder.raw_decode(remaining)
            if isinstance(obj, dict):
                objects.append(obj)
            pos += whitespace_skipped + end
        except json.JSONDecodeError:
            break

    return objects


class SupervisorAgent:
    """Klaudia supervisor: LangGraph hierarchical agent teams."""

    def __init__(
        self,
        llm_api_key: str,
        llm_model: str,
        mcp_sqlite: MCPToolRegistry,
        mcp_gsheets: MCPToolRegistry,
        langfuse: Optional[Any] = None,
        provider: str = "google",
        use_vertexai: bool = False,
        google_cloud_project: str = "",
        google_cloud_location: str = "global",
        openai_base_url: str = "",
        openai_api_key: str = "",
        disable_thinking: bool = True,
        temperature: float = 0.5,
        thinking_level_routing: str = "minimal",
        thinking_level_worker: str = "minimal",
    ) -> None:
        # Shared across both LLM variants. For provider="openai" the Gemini
        # kwargs (use_vertexai/project/location) are ignored, and vice-versa.
        _llm_kwargs = dict(
            model=llm_model,
            provider=provider,
            temperature=temperature,
            use_vertexai=use_vertexai,
            llm_api_key=llm_api_key,
            google_cloud_project=google_cloud_project,
            google_cloud_location=google_cloud_location,
            openai_base_url=openai_base_url,
            openai_api_key=openai_api_key,
            disable_thinking=disable_thinking,
        )
        # Two pre-bound LLM variants — no thinking config scattered across files.
        # routing_llm: minimal thinking for classification + summarization tasks.
        # worker_llm:  minimal thinking for tool-augmented reasoning (write/read/sql).
        self._routing_llm = build_chat_llm(
            **_llm_kwargs, thinking_level=thinking_level_routing
        )
        self._worker_llm = build_chat_llm(
            **_llm_kwargs, thinking_level=thinking_level_worker
        )

        self._mcp_sqlite = mcp_sqlite
        self._mcp_gsheets = mcp_gsheets
        self._langfuse = langfuse

        # Sheet list cache — populated programmatically via tool_list_sheets.
        # Injected into system prompt every turn so workers resolve sheet names
        # without burning an agent LLM hop on tool_list_sheets at runtime.
        self._sheets_cache: str = ""
        self._sheets_fetched_at: float = 0.0
        self._list_sheets_tool = next(
            (t for t in mcp_gsheets.tools if t.name == "tool_list_sheets"), None
        )

        self._graph = self._build_graph()

    # Sheet list cache helpers
    # ------------------------------------------------------------------

    def invalidate_sheets_cache(self) -> None:
        """Force a cache miss on the next get_available_sheets() call.

        Called automatically by make_data_entry_team_node whenever the team
        reports [SHEET_DONE] (create/rename/delete). Ensures the next turn's
        system prompt reflects the post-mutation sheet layout.
        """
        self._sheets_fetched_at = 0.0

    async def get_available_sheets(self, ttl: float = 10.0) -> str:
        """Return a formatted sheet list, refreshed at most every ttl seconds.

        Python calls tool_list_sheets directly — no LLM involvement, no agent
        hop. Fails soft: returns stale cache (or empty string) on error.
        """
        now = time.monotonic()
        if self._sheets_cache and (now - self._sheets_fetched_at) < ttl:
            return self._sheets_cache

        if self._list_sheets_tool is None:
            return self._sheets_cache

        try:
            raw = await self._list_sheets_tool.ainvoke({})
            sheets = _parse_tool_json_output(raw)
            if sheets:
                lines = [
                    f"  - Index {s.get('index', i)}: {s.get('title', '?')}"
                    for i, s in enumerate(sheets)
                ]
                self._sheets_cache = "\n".join(lines)
                self._sheets_fetched_at = now
            else:
                logger.warning(
                    "tool_list_sheets returned empty/unparseable output: %r", raw
                )
            # self._sheets_fetched_at = now
        except Exception as exc:
            logger.warning("Sheet list cache refresh failed: %s", exc)

        return self._sheets_cache

    # ------------------------------------------------------------------

    def _graph_config(
        self,
        session_id: Optional[int],
        user_id: Optional[int],
        run_name: str,
    ) -> dict[str, Any]:
        config: dict[str, Any] = {"recursion_limit": 50}
        if self._langfuse is not None:
            lf_cfg = self._langfuse.langchain_config(
                session_id=session_id,
                user_id=user_id,
                run_name=run_name,
                tags=["klaudia", "supervisor"],
            )
            config.update(lf_cfg)
        return config

    def _build_graph(self):
        # routing_llm → supervisor node + team_supervisor (classification tasks)
        # worker_llm  → sql_agent + worker agents (tool-augmented reasoning)
        supervisor_node = make_supervisor_node(self._routing_llm)
        sql_agent_node = make_sql_agent_node(self._worker_llm, self._mcp_sqlite)
        data_entry_node = make_data_entry_team_node(
            routing_llm=self._routing_llm,
            worker_llm=self._worker_llm,
            mcp_gsheets=self._mcp_gsheets,
            on_sheet_mutation=self.invalidate_sheets_cache,
        )

        builder = StateGraph(SupervisorState)
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("sql_agent", sql_agent_node)
        builder.add_node("data_entry_team", data_entry_node)
        builder.add_edge(START, "supervisor")

        return builder.compile()

    async def process_conversation(
        self,
        messages: list[dict[str, Any]],
        extraction_data: dict[str, Any] | None = None,
        session_id: int | None = None,
        user_id: int | None = None,
        sheets_context: str = "",
        files_context: str = "",
        date_context: str = "",
    ) -> AgentResponse:
        state = {
            "messages": messages,
            "extraction_data": extraction_data,
            "session_id": session_id or 0,
            "sheets_context": sheets_context,
            "files_context": files_context,
            "date_context": date_context,
            "pending_worker": None,
        }
        config = self._graph_config(
            session_id, user_id, run_name="klaudia.supervisor.invoke"
        )
        result = await self._graph.ainvoke(state, config)

        content = _resolve_final_content(result["messages"])
        if not content:
            logger.warning("Supervisor produced no user-facing content")

        tools_used = [
            getattr(msg, "name", None)
            for msg in result["messages"]
            if getattr(msg, "name", None)
            and getattr(msg, "name") not in ("user", "system")
        ]

        return AgentResponse(
            content=content,
            tools_called=tools_used,
            metadata={"routed_to": result.get("next", "FINISH")},
        )

    async def stream_conversation(
        self,
        messages: list[dict[str, Any]],
        extraction_data: dict[str, Any] | None = None,
        session_id: int | None = None,
        user_id: int | None = None,
        sheets_context: str = "",
        files_context: str = "",
        date_context: str = "",
    ) -> AsyncIterator[dict[str, Any]]:
        state = {
            "messages": messages,
            "extraction_data": extraction_data,
            "session_id": session_id or 0,
            "sheets_context": sheets_context,
            "files_context": files_context,
            "date_context": date_context,
            "pending_worker": None,
        }

        final_chunks: list[str] = []
        tools_used: list[str] = []
        routed_to = "FINISH"
        observed_messages: list[Any] = []

        stream_config = self._graph_config(
            session_id, user_id, run_name="klaudia.supervisor.stream"
        )

        async for mode, payload in self._graph.astream(
            state,
            config=stream_config,
            stream_mode=["messages", "updates"],
        ):
            if mode == "messages":
                msg_chunk, metadata = payload
                tags = metadata.get("tags", []) or []
                if "nostream" in tags or "final_answer" not in tags:
                    continue
                text = getattr(msg_chunk, "content", "")
                if isinstance(text, str) and text:
                    final_chunks.append(text)
                    yield {"type": "token", "data": {"text": text}}
                continue

            if mode == "updates":
                for node, update in payload.items():
                    if not isinstance(update, dict):
                        continue
                    nxt = update.get("next")
                    if nxt is not None:
                        routed_to = nxt
                    yield {"type": "step", "data": {"node": node, "next": nxt}}
                    for msg in update.get("messages", []) or []:
                        observed_messages.append(msg)
                        name = getattr(msg, "name", None)
                        if name and name not in ("user", "system"):
                            tools_used.append(name)
                            yield {"type": "tool", "data": {"name": name}}

        streamed = "".join(final_chunks).strip()
        content = streamed or _resolve_final_content(observed_messages)

        yield {
            "type": "final",
            "data": {
                "content": content,
                "tools_called": tools_used,
                "metadata": {"routed_to": routed_to},
            },
        }
