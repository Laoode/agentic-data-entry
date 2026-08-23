"""End-to-end mcp-ledger test: the gsheets tool surface backed by Postgres.

Spawns the real server over stdio (production transport) and exercises the
full sheet lifecycle the data-entry agents use. Skipped when Postgres is
unreachable.
"""

import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from contextlib import asynccontextmanager
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SERVER_DIR = _PROJECT_ROOT / "mcp-ledger"
_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql://klaudia:klaudia@localhost:5432/klaudia"
)

GSHEETS_PARITY_TOOLS = {
    "tool_get_sheet_data",
    "tool_get_sheet_formulas",
    "tool_list_sheets",
    "tool_get_spreadsheet_info",
    "tool_get_multiple_sheet_data",
    "tool_update_cells",
    "tool_batch_update_cells",
    "tool_append_rows",
    "tool_add_rows",
    "tool_add_columns",
    "tool_clear_range",
    "tool_create_sheet",
    "tool_rename_sheet",
    "tool_copy_sheet",
    "tool_delete_sheet",
    "tool_batch_update",
}


async def _pg_available() -> bool:
    import asyncpg

    try:
        conn = await asyncpg.connect(_PG_URL, timeout=3)
        await conn.close()
        return True
    except Exception:
        return False


async def _call(client: Client, tool: str, args: dict, expect_list: bool = False):
    """Parse tool output like the app does: FastMCP emits list results as
    one text block per element (see B13 in the app's tool parsing). A
    one-element list is indistinguishable from a scalar dict on the wire,
    so list-returning tools pass expect_list=True."""
    result = await client.call_tool(tool, args, raise_on_error=False)
    texts = [c.text for c in result.content if getattr(c, "text", None)]
    if not texts:
        return []
    if len(texts) > 1:
        return [json.loads(t) for t in texts]
    parsed = json.loads(texts[0])
    if expect_list and isinstance(parsed, dict):
        return [parsed]
    return parsed


@asynccontextmanager
async def ledger_server():
    """Fresh server subprocess + isolated workspace per test.

    Not a pytest fixture on purpose: the subprocess must enter and exit in the
    same task as each test.
    """
    if not await _pg_available():
        pytest.skip(f"Postgres not reachable at {_PG_URL}")
    workspace = f"test-{uuid.uuid4().hex[:8]}"
    transport = StdioTransport(
        command=sys.executable,
        args=["main.py", "--transport", "stdio"],
        cwd=str(_SERVER_DIR),
        env={**os.environ, "DATABASE_URL": _PG_URL, "LEDGER_WORKSPACE": workspace},
    )
    async with Client(transport, mode="auto") as client:
        yield client


async def test_tool_surface_matches_gsheets():
    async with ledger_server() as ledger_session:
        tools = await ledger_session.list_tools()
        assert {tool.name for tool in tools} == GSHEETS_PARITY_TOOLS


async def test_sheet_lifecycle():
    async with ledger_server() as ledger_session:
        s = ledger_session

        assert await _call(s, "tool_list_sheets", {}, expect_list=True) == []

        created = await _call(s, "tool_create_sheet", {"title": "Jul"})
        assert created["title"] == "Jul"
        assert created["sheetId"] >= 1

        listed = await _call(s, "tool_list_sheets", {}, expect_list=True)
        assert [t["title"] for t in listed] == ["Jul"]

        header = ["Date", "Merchant", "Total"]
        await _call(
            s,
            "tool_append_rows",
            {"sheet": "Jul", "data": [header, ["2026-07-01", "ALFAMIDI", 15000]]},
        )
        appended = await _call(
            s,
            "tool_append_rows",
            {"sheet": "Jul", "data": [["2026-07-02", "INDOMARET", 23500]]},
        )
        assert appended["updates"]["updatedRows"] == 1

        data = await _call(s, "tool_get_sheet_data", {"sheet": "Jul"})
        assert data["values"] == [
            ["Date", "Merchant", "Total"],
            ["2026-07-01", "ALFAMIDI", 15000],
            ["2026-07-02", "INDOMARET", 23500],
        ]

        ranged = await _call(
            s, "tool_get_sheet_data", {"sheet": "Jul", "range": "B2:C3"}
        )
        assert ranged["values"] == [["ALFAMIDI", 15000], ["INDOMARET", 23500]]

        await _call(
            s,
            "tool_update_cells",
            {"sheet": "Jul", "range": "C2", "data": [[16000]]},
        )
        fixed = await _call(s, "tool_get_sheet_data", {"sheet": "Jul", "range": "C2"})
        assert fixed["values"] == [[16000]]


async def test_fuzzy_sheet_name_resolution():
    async with ledger_server() as ledger_session:
        s = ledger_session
        await _call(s, "tool_create_sheet", {"title": "Expenses - Jul"})
        await _call(
            s,
            "tool_append_rows",
            {"sheet": "expenses-jul", "data": [["x"]]},
        )
        data = await _call(s, "tool_get_sheet_data", {"sheet": "EXPENSES - JUL"})
        assert data["values"] == [["x"]]
        assert data["range"].startswith("Expenses - Jul")


async def test_copy_rename_delete():
    async with ledger_server() as ledger_session:
        s = ledger_session
        await _call(s, "tool_create_sheet", {"title": "Jun"})
        await _call(s, "tool_append_rows", {"sheet": "Jun", "data": [["h"], ["v"]]})

        copied = await _call(
            s, "tool_copy_sheet", {"src_sheet": "Jun", "dst_sheet": "Jun-Backup"}
        )
        assert copied["copy"]["title"] == "Jun-Backup"
        backup = await _call(s, "tool_get_sheet_data", {"sheet": "Jun-Backup"})
        assert backup["values"] == [["h"], ["v"]]

        await _call(
            s, "tool_rename_sheet", {"sheet": "Jun-Backup", "new_name": "Archive"}
        )
        titles = [
            t["title"] for t in await _call(s, "tool_list_sheets", {}, expect_list=True)
        ]
        assert "Archive" in titles and "Jun-Backup" not in titles

        await _call(s, "tool_delete_sheet", {"sheet": "Archive"})
        titles = [
            t["title"] for t in await _call(s, "tool_list_sheets", {}, expect_list=True)
        ]
        assert "Archive" not in titles


async def test_multiple_sheet_data_and_info():
    async with ledger_server() as ledger_session:
        s = ledger_session
        await _call(s, "tool_create_sheet", {"title": "A"})
        await _call(s, "tool_create_sheet", {"title": "B"})
        await _call(s, "tool_append_rows", {"sheet": "A", "data": [["a1"]]})
        await _call(s, "tool_append_rows", {"sheet": "B", "data": [["b1"]]})

        multi = await _call(
            s,
            "tool_get_multiple_sheet_data",
            {"queries": [{"sheet": "A"}, {"sheet": "B"}, {"sheet": "missing"}]},
        )
        assert multi[0]["data"] == [["a1"]]
        assert multi[1]["data"] == [["b1"]]
        assert "error" in multi[2]

        info = await _call(s, "tool_get_spreadsheet_info", {})
        assert {t["title"] for t in info["sheets"]} == {"A", "B"}
        assert info["sheets"][0]["gridProperties"]["rowCount"] >= 1


async def test_error_shapes_for_missing_sheet():
    async with ledger_server() as ledger_session:
        s = ledger_session
        result = await s.call_tool(
            "tool_get_sheet_data",
            {"sheet": "nope"},
            raise_on_error=False,
        )
        assert result.is_error or "not found" in str(result.content).lower()


async def test_batch_update_structural_ops():
    async with ledger_server() as ledger_session:
        s = ledger_session
        out = await _call(
            s,
            "tool_batch_update",
            {"requests": [{"addSheet": {"properties": {"title": "FromBatch"}}}]},
        )
        assert out["replies"][0]["addSheet"]["properties"]["title"] == "FromBatch"

        sheets = await _call(s, "tool_list_sheets", {}, expect_list=True)
        sheet_id = next(t["sheetId"] for t in sheets if t["title"] == "FromBatch")
        out = await _call(
            s,
            "tool_batch_update",
            {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]},
        )
        assert out["replies"][0] == {}
