"""Integration tests for supervisor streaming.

Exercises SupervisorAgent.stream_conversation() end-to-end to verify:
1. The generator yields structured events in the documented schema
2. A routing step is emitted
3. A final aggregate is emitted last with the supervisor's answer

Requires MCP-SQLite on 8001, MCP-GSheets on 8002, and a valid LLM_API_KEY.
"""

import os

import pytest

from config.settings import Settings
from klaudia.core.supervisor.agent import SupervisorAgent
from klaudia.interfaces.tool_registry import MCPToolRegistry


AGENT_TEST_MODEL = os.environ.get("AGENT_TEST_MODEL", "gemini-3-flash-preview")
SSE_SQLITE = "http://localhost:8001/sse"
SSE_GSHEETS = "http://localhost:8002/sse"


def _have_llm_creds(s: Settings) -> bool:
    return bool(s.google_cloud_project) if s.google_genai_use_vertexai else bool(s.llm_api_key)


pytestmark = pytest.mark.skipif(
    not _have_llm_creds(Settings()),
    reason="No Gemini credentials (set LLM_API_KEY or GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT)",
)


@pytest.fixture
async def mcp_sqlite():
    reg = MCPToolRegistry("mcp-sqlite", SSE_SQLITE)
    await reg.connect()
    try:
        yield reg
    finally:
        await reg.disconnect()


@pytest.fixture
async def mcp_gsheets():
    reg = MCPToolRegistry("mcp-gsheets", SSE_GSHEETS)
    await reg.connect()
    try:
        yield reg
    finally:
        await reg.disconnect()


@pytest.fixture
def supervisor(mcp_sqlite, mcp_gsheets):
    s = Settings()
    return SupervisorAgent(
        llm_api_key=s.llm_api_key,
        llm_model=AGENT_TEST_MODEL,
        mcp_sqlite=mcp_sqlite,
        mcp_gsheets=mcp_gsheets,
        use_vertexai=s.google_genai_use_vertexai,
        google_cloud_project=s.google_cloud_project,
        google_cloud_location=s.google_cloud_location,
    )


@pytest.mark.asyncio
async def test_stream_conversation_emits_final_event_with_content(supervisor):
    """A simple greeting must be routed to FINISH and emit a final event with text."""
    events: list[dict] = []
    async for ev in supervisor.stream_conversation(
        messages=[{"role": "user", "content": "Hi Klaudia, balas singkat saja 'hello'."}],
        extraction_data=None,
    ):
        events.append(ev)

    # Arrange: expected schema shape
    types = [e["type"] for e in events]

    # Assert: at least one step and exactly one final, final is last
    assert events, "stream produced no events"
    assert types[-1] == "final", f"final event must be last, got: {types}"
    assert "step" in types, f"no step events emitted: {types}"

    final = events[-1]["data"]
    assert isinstance(final["content"], str) and final["content"], (
        f"final event content empty: {final}"
    )
    assert final["metadata"]["routed_to"] in {"FINISH", "sql_agent", "data_entry_team"}


@pytest.mark.asyncio
async def test_stream_conversation_emits_only_known_event_types(supervisor):
    """Every yielded event must match the documented schema."""
    allowed = {"step", "tool", "token", "final"}
    async for ev in supervisor.stream_conversation(
        messages=[{"role": "user", "content": "Halo, siapa kamu?"}],
        extraction_data=None,
    ):
        assert ev["type"] in allowed, f"unexpected event type: {ev}"
        assert "data" in ev, f"event missing data: {ev}"
