"""Integration tests for the Data Entry Team wiring and single-turn execution.

Requires MCP-GSheets running on port 8002 and a valid LLM_API_KEY.
Tests verify that:
1. Tool registry connects and discovers GSheets tools
2. Tools are correctly partitioned to read/sheet/write agents
3. A single-turn write_agent can call append_rows (1 LLM round-trip)
4. A single-turn read_agent can call get_sheet_data (1 LLM round-trip)
"""

import json
import os
import time
import uuid

import pytest
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.sse import sse_client

from config.settings import Settings
from klaudia.core.supervisor.agents.data_entry_team.agents import make_data_entry_team
from klaudia.core.supervisor.agents.data_entry_team.prompts import (
    READ_AGENT_PROMPT,
    WRITE_AGENT_PROMPT,
)
from klaudia.core.supervisor.tools.wrappers import (
    get_read_tools,
    get_sheet_tools,
    get_write_tools,
)
from klaudia.interfaces.tool_registry import MCPToolRegistry


SHEET_ID = "1sYmDi2o55tZktSbgy60rIwZa-3gPqH_b5U7iN4jTCIo"
SSE_GSHEETS = "http://localhost:8002/sse"
AGENT_TEST_MODEL = os.environ.get("AGENT_TEST_MODEL", "gemini-3-flash-preview")

pytestmark = pytest.mark.skipif(
    not Settings().llm_api_key,
    reason="LLM_API_KEY not set",
)


@pytest.fixture
async def registry():
    reg = MCPToolRegistry("mcp-gsheets", SSE_GSHEETS)
    await reg.connect()
    try:
        yield reg
    finally:
        await reg.disconnect()


@pytest.fixture
def llm():
    s = Settings()
    return ChatGoogleGenerativeAI(
        model=AGENT_TEST_MODEL,
        google_api_key=s.llm_api_key,
        temperature=0.0,
    )


async def _sheet_call(name: str, args: dict):
    async with sse_client(SSE_GSHEETS) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(name, args)
            assert not res.isError, f"{name}: {res.content}"
            if not res.content:
                return {}
            if len(res.content) == 1:
                return json.loads(res.content[0].text)
            return [json.loads(c.text) for c in res.content]


@pytest.fixture
async def temp_sheet():
    title = f"team_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    await _sheet_call("tool_create_sheet", {"spreadsheet_id": SHEET_ID, "title": title})
    yield title
    try:
        await _sheet_call("tool_delete_sheet", {"spreadsheet_id": SHEET_ID, "sheet": title})
    except AssertionError:
        pass


# --- Test 1: Tool partitioning ---


@pytest.mark.asyncio
async def test_tool_partitioning(registry):
    """Each wrapper returns only its intended subset of tools."""
    read = {t.name for t in get_read_tools(registry)}
    sheet = {t.name for t in get_sheet_tools(registry)}
    write = {t.name for t in get_write_tools(registry)}

    assert "tool_get_sheet_data" in read
    assert "tool_create_sheet" in sheet
    assert "tool_append_rows" in write

    assert not (read & write), "read and write tools overlap"
    assert not (read & sheet), "read and sheet tools overlap"
    assert not (sheet & write), "sheet and write tools overlap"


# --- Test 2: Write agent single-turn ---


@pytest.mark.asyncio
async def test_write_agent_appends_row(registry, llm, temp_sheet):
    """Write agent should call append_rows and land 1 row in the sheet."""
    write_agent = create_react_agent(
        llm, tools=get_write_tools(registry), prompt=WRITE_AGENT_PROMPT
    )
    task = (
        f"Append exactly one row to spreadsheet '{SHEET_ID}' sheet '{temp_sheet}'. "
        "The row must be: ['INDOMARET', 'Indomie', '15540']. "
        "Call tool_append_rows once, then stop."
    )
    result = await write_agent.ainvoke({"messages": [("user", task)]})

    tool_msgs = [m for m in result["messages"] if getattr(m, "name", None) == "tool_append_rows"]
    assert tool_msgs, "write_agent never called tool_append_rows"

    got = await _sheet_call(
        "tool_get_sheet_data",
        {"spreadsheet_id": SHEET_ID, "sheet": temp_sheet, "range": "A1:C1"},
    )
    assert got.get("values") == [["INDOMARET", "Indomie", "15540"]], f"row not persisted: {got}"


# --- Test 3: Read agent single-turn ---


@pytest.mark.asyncio
async def test_read_agent_reads_seeded_data(registry, llm, temp_sheet):
    """Read agent should call get_sheet_data and surface the seeded value."""
    await _sheet_call(
        "tool_append_rows",
        {
            "spreadsheet_id": SHEET_ID,
            "sheet": temp_sheet,
            "data": [["ALFAMART", "Aqua", "8000"]],
        },
    )

    read_agent = create_react_agent(
        llm, tools=get_read_tools(registry), prompt=READ_AGENT_PROMPT
    )
    task = (
        f"Read cells A1:C1 from spreadsheet '{SHEET_ID}' sheet '{temp_sheet}'. "
        "Report the exact cell values."
    )
    result = await read_agent.ainvoke({"messages": [("user", task)]})

    tool_msgs = [m for m in result["messages"] if getattr(m, "name", None) == "tool_get_sheet_data"]
    assert tool_msgs, "read_agent never called tool_get_sheet_data"

    joined = " ".join(str(getattr(m, "content", "")) for m in result["messages"]).upper()
    assert "ALFAMART" in joined, f"read_agent didn't surface seeded value: {joined[:400]}"


# --- Test 4: Multi-turn sheet resolution (regression) ---


@pytest.mark.asyncio
async def test_team_resolves_sheet_from_prior_turn(registry, llm, temp_sheet):
    """Team subgraph must remember the sheet referenced in earlier turns.

    Regression for context loss bug: data_entry_team_node previously forwarded
    only state["messages"][-1] to the team subgraph. Multi-turn requests like
    "recap sheet X" → "tambahkan header" landed on the wrong (default) sheet
    because the team had no memory of which sheet "X" was.
    """
    await _sheet_call(
        "tool_append_rows",
        {
            "spreadsheet_id": SHEET_ID,
            "sheet": temp_sheet,
            "data": [["INDOMARET", "Indomie", "15540"]],
        },
    )

    team = make_data_entry_team(llm, registry)

    conversation = [
        ("user", f"Hi, bisa kamu recap isi sheet '{temp_sheet}' itu apa?"),
        (
            "assistant",
            f"Sheet '{temp_sheet}' berisi 1 baris: INDOMARET, Indomie, 15540.",
        ),
        ("user", "Tolong rapikan, tambahkan header Merchant, Nama Barang, Harga di baris paling atas."),
    ]

    await team.ainvoke({"messages": conversation})

    got = await _sheet_call(
        "tool_get_sheet_data",
        {"spreadsheet_id": SHEET_ID, "sheet": temp_sheet, "range": "A1:C2"},
    )
    values = got.get("values") or []
    assert values, f"sheet '{temp_sheet}' is empty after team turn: {got}"

    header = [str(c).strip().lower() for c in values[0]]
    assert header == ["merchant", "nama barang", "harga"], (
        f"header not written to '{temp_sheet}' (got {values[0]!r}). "
        "Team likely wrote to the wrong sheet — context from earlier turn was lost."
    )


# --- Test 5: Non-destructive header addition (regression) ---


@pytest.mark.asyncio
async def test_team_adds_header_without_wiping_data(registry, llm, temp_sheet):
    """Adding a header above existing data must preserve the data row.

    Regression for the destructive-write bug: write_agent previously chained
    tool_clear_range + tool_update_cells with a header-only payload and wiped
    the existing rows. The fix is Pattern C — add_rows(start_row=0) followed
    by update_cells('A1', header) — which inserts a blank top row instead of
    clearing the sheet. The original data must remain at A2 untouched.
    """
    await _sheet_call(
        "tool_append_rows",
        {
            "spreadsheet_id": SHEET_ID,
            "sheet": temp_sheet,
            "data": [["INDOMARET", "Indomie", "15540"]],
        },
    )

    team = make_data_entry_team(llm, registry)

    conversation = [
        (
            "user",
            f"Tolong tambahkan header Merchant, Nama Barang, Harga di baris paling "
            f"atas sheet '{temp_sheet}'. Jangan hapus data yang sudah ada.",
        ),
    ]

    await team.ainvoke({"messages": conversation})

    got = await _sheet_call(
        "tool_get_sheet_data",
        {"spreadsheet_id": SHEET_ID, "sheet": temp_sheet, "range": "A1:C2"},
    )
    values = got.get("values") or []
    assert len(values) >= 2, (
        f"sheet '{temp_sheet}' lost data after header add (got {values!r}). "
        "Team likely used clear_range + update_cells with a header-only payload."
    )

    header = [str(c).strip().lower() for c in values[0]]
    data_row = [str(c).strip() for c in values[1]]
    assert header == ["merchant", "nama barang", "harga"], (
        f"header row missing or wrong (got {values[0]!r})"
    )
    assert data_row == ["INDOMARET", "Indomie", "15540"], (
        f"original data row was wiped or shifted (got {values[1]!r}). "
        "Pattern C (add_rows + update_cells) should preserve existing data at A2."
    )
