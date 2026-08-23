"""Contract tests for Klaudia's FastMCP client boundary."""

import json
import sys

import pytest

from klaudia.interfaces.tool_registry import MCPToolRegistry


def _write_server(tmp_path):
    """Write a small FastMCP server used by registry subprocess tests.

    Args:
        tmp_path: Pytest temporary directory.

    Returns:
        Path to the generated server module.
    """
    server_path = tmp_path / "server.py"
    server_path.write_text(
        """
from fastmcp import FastMCP

mcp = FastMCP("registry-test", strict_input_validation=True)

@mcp.tool
def greet(name: str) -> dict[str, str]:
    return {"message": f"hello {name}"}

if __name__ == "__main__":
    mcp.run(transport="stdio")
""".strip()
    )
    return server_path


async def test_stdio_registry_discovers_and_calls_fastmcp_tool(tmp_path):
    """The registry discovers schemas and preserves JSON tool output."""
    server_path = _write_server(tmp_path)
    registry = MCPToolRegistry.from_stdio(
        "test",
        command=sys.executable,
        args=[str(server_path)],
    )

    await registry.connect()
    try:
        assert [tool.name for tool in registry.tools] == ["greet"]
        assert "ctx" not in registry.tools[0].args
        response = await registry.tools[0].ainvoke({"name": "Klaudia"})
        assert json.loads(response) == {"message": "hello Klaudia"}
    finally:
        await registry.disconnect()


async def test_registry_connection_failure_is_not_silenced(tmp_path):
    """A dead subprocess fails application startup instead of hiding the error."""
    registry = MCPToolRegistry.from_stdio(
        "broken",
        command=sys.executable,
        args=[str(tmp_path / "missing.py")],
    )

    with pytest.raises(RuntimeError, match="connection failed"):
        await registry.connect()
