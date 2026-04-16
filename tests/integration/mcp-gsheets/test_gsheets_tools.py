"""End-to-end MCP-GSheets tool invocation tests.

Requires the MCP-GSheets server running on port 8002 (via ./startup.sh)
with service_account.json configured and access to SHEET_ID.

Each test creates a unique throwaway sheet tab inline and deletes it before
exiting to avoid polluting the shared spreadsheet.
"""

import json
import time
import uuid
from contextlib import asynccontextmanager

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client


SSE_URL = "http://localhost:8002/sse"
SHEET_ID = "1sYmDi2o55tZktSbgy60rIwZa-3gPqH_b5U7iN4jTCIo"


async def _call(session: ClientSession, name: str, args: dict):
    """Call a tool and return the first content block as JSON."""
    result = await session.call_tool(name, args)
    assert not result.isError, f"{name} errored: {result.content}"
    assert result.content, f"{name} returned no content"
    return json.loads(result.content[0].text)


async def _call_many(session: ClientSession, name: str, args: dict) -> list:
    """Call a tool and return ALL content blocks (MCP-GSheets returns one per row/item)."""
    result = await session.call_tool(name, args)
    assert not result.isError, f"{name} errored: {result.content}"
    return [json.loads(c.text) for c in result.content]


@asynccontextmanager
async def _session():
    async with sse_client(SSE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@asynccontextmanager
async def _temp_sheet(session: ClientSession):
    title = f"test_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    await _call(session, "tool_create_sheet", {"spreadsheet_id": SHEET_ID, "title": title})
    try:
        yield title
    finally:
        try:
            await _call(session, "tool_delete_sheet", {"spreadsheet_id": SHEET_ID, "sheet": title})
        except AssertionError:
            pass


@pytest.mark.asyncio
async def test_tools_registered():
    async with _session() as s:
        tools = await s.list_tools()
        names = {t.name for t in tools.tools}
    required = {
        "tool_get_spreadsheet_info",
        "tool_list_sheets",
        "tool_create_sheet",
        "tool_delete_sheet",
        "tool_append_rows",
        "tool_update_cells",
        "tool_get_sheet_data",
        "tool_clear_range",
    }
    assert not (required - names), f"missing tools: {required - names}"


@pytest.mark.asyncio
async def test_get_spreadsheet_info():
    async with _session() as s:
        info = await _call(s, "tool_get_spreadsheet_info", {"spreadsheet_id": SHEET_ID})
    assert isinstance(info, dict) and info


@pytest.mark.asyncio
async def test_list_sheets_contains_temp():
    async with _session() as s:
        async with _temp_sheet(s) as title:
            sheets = await _call_many(s, "tool_list_sheets", {"spreadsheet_id": SHEET_ID})
    titles = [sh.get("title") for sh in sheets]
    assert title in titles, f"{title} not in {titles}"


@pytest.mark.asyncio
async def test_append_and_read_roundtrip():
    rows = [["store", "item", "total"], ["INDOMARET", "Indomie", "15540"]]
    async with _session() as s:
        async with _temp_sheet(s) as title:
            await _call(
                s,
                "tool_append_rows",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "data": rows},
            )
            got = await _call(
                s,
                "tool_get_sheet_data",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "range": "A1:C2"},
            )
    assert got["values"] == rows


@pytest.mark.asyncio
async def test_update_cells_overwrites():
    async with _session() as s:
        async with _temp_sheet(s) as title:
            await _call(
                s,
                "tool_append_rows",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "data": [["a", "b"]]},
            )
            await _call(
                s,
                "tool_update_cells",
                {
                    "spreadsheet_id": SHEET_ID,
                    "sheet": title,
                    "range": "A1:B1",
                    "data": [["x", "y"]],
                },
            )
            got = await _call(
                s,
                "tool_get_sheet_data",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "range": "A1:B1"},
            )
    assert got["values"][0] == ["x", "y"]


@pytest.mark.asyncio
async def test_clear_range_empties_cells():
    async with _session() as s:
        async with _temp_sheet(s) as title:
            await _call(
                s,
                "tool_append_rows",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "data": [["keep", "drop"]]},
            )
            await _call(
                s,
                "tool_clear_range",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "range": "B1:B1"},
            )
            got = await _call(
                s,
                "tool_get_sheet_data",
                {"spreadsheet_id": SHEET_ID, "sheet": title, "range": "A1:B1"},
            )
    row = got["values"][0]
    assert row[0] == "keep"
    assert len(row) == 1 or row[1] in ("", None)
