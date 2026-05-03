"""Integration tests for the SQL Agent (ReAct + MCP-SQLite tools).

Requires MCP-SQLite running on port 8001 and a valid LLM_API_KEY in .env.
Seeds the DB with a document+page+extraction, then exercises the ReAct
loop end-to-end so both tool wiring and LLM reasoning are validated.
"""

import json
import os

import pytest
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.sse import sse_client

from config.settings import Settings
from klaudia.core.supervisor.agents.sql_agent.prompts import SQL_AGENT_PROMPT
from klaudia.core.supervisor.llm import build_chat_llm
from klaudia.core.supervisor.tools.wrappers import get_sql_tools
from klaudia.interfaces.tool_registry import MCPToolRegistry


def _have_llm_creds(s: Settings) -> bool:
    return bool(s.google_cloud_project) if s.google_genai_use_vertexai else bool(s.llm_api_key)


pytestmark = pytest.mark.skipif(
    not _have_llm_creds(Settings()),
    reason="No Gemini credentials (set LLM_API_KEY or GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT)",
)


@pytest.fixture
async def registry():
    reg = MCPToolRegistry("mcp-sqlite", "http://localhost:8001/sse")
    await reg.connect()
    try:
        yield reg
    finally:
        await reg.disconnect()


AGENT_TEST_MODEL = os.environ.get("AGENT_TEST_MODEL", "gemini-3-flash-preview")


@pytest.fixture
def llm():
    s = Settings()
    return build_chat_llm(
        model=AGENT_TEST_MODEL,
        temperature=0.0,
        use_vertexai=s.google_genai_use_vertexai,
        llm_api_key=s.llm_api_key,
        google_cloud_project=s.google_cloud_project,
        google_cloud_location=s.google_cloud_location,
    )


async def _seed() -> tuple[int, int]:
    """Seed a document/page/extraction via a standalone MCP client. Returns (doc_id, page_id)."""
    extraction = {
        "info": {"store_name": "ALFAMART", "store_location": "Jl. Ciputat Raya"},
        "items": [{"item_name": "Aqua 600ml", "quantity": "2", "price_per_unit": "4000"}],
        "returned_items": [],
        "payment": {"grand_total": "8000", "currency": "IDR"},
    }
    async with sse_client("http://localhost:8001/sse") as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()

            async def call(name: str, args: dict) -> dict:
                res = await s.call_tool(name, args)
                assert not res.isError, f"{name}: {res.content}"
                return json.loads(res.content[0].text)

            doc = await call(
                "tool_create_document",
                {
                    "session_id": 1,
                    "user_id": 1,
                    "file_type": "image",
                    "file_name": "sql-agent-fixture.jpg",
                    "total_pages": 1,
                },
            )
            page = await call(
                "tool_create_page",
                {"metadata_file_id": doc["id"], "page_number": 1},
            )
            await call(
                "tool_save_extraction",
                {"page_id": page["id"], "extraction_json": json.dumps(extraction)},
            )
            return doc["id"], page["id"]


def _tool_calls(result: dict) -> list[tuple[str, str]]:
    """Return (tool_name, content) pairs from a ReAct result."""
    pairs = []
    for m in result["messages"]:
        name = getattr(m, "name", None)
        if name and name.startswith("tool_"):
            pairs.append((name, str(m.content)))
    return pairs


@pytest.mark.asyncio
async def test_sql_agent_answers_store_name_question(registry, llm):
    """Agent should retrieve extraction and name ALFAMART."""
    doc_id, _ = await _seed()

    agent = create_react_agent(llm, tools=get_sql_tools(registry), prompt=SQL_AGENT_PROMPT)
    result = await agent.ainvoke(
        {
            "messages": [
                (
                    "user",
                    f"Fetch the extraction for document id {doc_id} page 1 and tell me the store_name field.",
                )
            ]
        }
    )
    raw_content = result["messages"][-1].content
    content = raw_content if isinstance(raw_content, str) else str(raw_content)
    calls = _tool_calls(result)
    assert calls, "agent never invoked a read tool"
    combined = (content + " ".join(c for _, c in calls)).upper()
    assert "ALFAMART" in combined, f"ALFAMART missing from agent trace: final={content!r}, calls={calls}"


@pytest.mark.asyncio
async def test_sql_agent_handles_missing_document(registry, llm):
    """For an unknown id the agent must invoke a lookup tool and surface a not-found signal."""
    agent = create_react_agent(llm, tools=get_sql_tools(registry), prompt=SQL_AGENT_PROMPT)
    result = await agent.ainvoke(
        {
            "messages": [
                ("user", "Please look up document id 999999 and tell me what you find."),
            ]
        }
    )
    calls = _tool_calls(result)
    assert calls, "agent never invoked a read tool"
    # The MCP tool returns {"error": "Document 999999 not found"} — the word "error" or "not found"
    # should surface in at least one tool output.
    joined = " ".join(c for _, c in calls).lower()
    assert "not found" in joined or "error" in joined, (
        f"tool responses didn't signal missing doc: {calls}"
    )
