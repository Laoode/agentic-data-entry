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
from tests.integration.postgres import POSTGRES_TEST_URL

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SERVER_DIR = _PROJECT_ROOT / "mcp-ledger"
_PG_URL = POSTGRES_TEST_URL

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
        pytest.skip("The isolated PostgreSQL test database is unavailable")
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
        assert {tool.name for tool in tools} == GSHEETS_PARITY_TOOLS | {
            "tool_get_sheet_snapshot",
            "tool_append_rows_checked",
            "tool_aggregate_sheet",
            "tool_register_table",
            "tool_update_table",
            "tool_search_resources",
            "tool_inspect_resource",
        }


async def test_checked_append_uses_snapshot_and_replays_receipt():
    """The MCP boundary preserves revisions, scope and committed replay."""
    async with ledger_server() as client:
        await _call(client, "tool_create_sheet", {"title": "Claims"})
        snapshot = await _call(client, "tool_get_sheet_snapshot", {"sheet": "Claims"})
        operation = {
            "sheet_id": snapshot["sheet_id"],
            "expected_revision": snapshot["revision"],
            "idempotency_key": "claim-1",
            "rows": [["Transport", 185000]],
        }
        receipt = await _call(
            client, "tool_append_rows_checked", {"operation": operation}
        )
        replay = await _call(
            client, "tool_append_rows_checked", {"operation": operation}
        )
        assert receipt == replay
        assert receipt["status"] == "committed"
        after = await _call(
            client, "tool_get_sheet_snapshot", {"sheet": "Claims", "range": "B1:B1"}
        )
        assert after["values"] == [[185000]]
        assert after["revision"] == receipt["after_revision"]
        stale = await client.call_tool(
            "tool_append_rows_checked",
            {"operation": operation | {"idempotency_key": "claim-2"}},
            raise_on_error=False,
        )
        assert stale.is_error
        oversized = await client.call_tool(
            "tool_get_sheet_snapshot",
            {"sheet": "Claims", "range": "A:Z"},
            raise_on_error=False,
        )
        assert oversized.is_error


async def test_aggregate_evidence_keeps_source_revision_and_labels():
    """MCP returns labelled sums from one versioned source without raw records."""
    async with ledger_server() as client:
        await _call(client, "tool_create_sheet", {"title": "Journal"})
        await _call(
            client,
            "tool_append_rows",
            {"sheet": "Journal", "data": [["Debit", "Credit"], [42500000, 41050000]]},
        )
        query = {
            "table_range": "A1:B2",
            "metrics": [
                {"column": column, "operation": "sum"} for column in ("Debit", "Credit")
            ],
        }
        evidence = await _call(
            client, "tool_aggregate_sheet", {"sheet": "Journal", "query": query}
        )
        assert evidence["source"]["revision"] == 1
        assert evidence["source"]["range"] == "Journal!A1:B2"
        assert evidence["query"]["metrics"] == query["metrics"]
        assert evidence["matched_rows"] == 1
        assert [metric["value"] for metric in evidence["groups"][0]["metrics"]] == [
            "42500000",
            "41050000",
        ]
        assert "values" not in evidence
        await _call(
            client,
            "tool_update_cells",
            {"sheet": "Journal", "range": "B2", "data": [[42500000]]},
        )
        after = await _call(
            client, "tool_aggregate_sheet", {"sheet": "Journal", "query": query}
        )
        assert after["source"]["revision"] == 2
        assert after["groups"][0]["metrics"][1]["value"] == "42500000"


async def test_new_read_tools_reject_oversized_evidence():
    """Large cell text cannot bypass a read tool's context budget."""
    async with ledger_server() as client:
        await _call(client, "tool_create_sheet", {"title": "Large text"})
        await _call(
            client,
            "tool_append_rows",
            {"sheet": "Large text", "data": [["Category", "Amount"], ["x" * 65536, 1]]},
        )
        snapshot = await client.call_tool(
            "tool_get_sheet_snapshot", {"sheet": "Large text"}, raise_on_error=False
        )
        assert snapshot.is_error
        aggregate = await client.call_tool(
            "tool_aggregate_sheet",
            {
                "sheet": "Large text",
                "query": {
                    "table_range": "A1:B2",
                    "metrics": [{"column": "Amount", "operation": "sum"}],
                    "group_by": ["Category"],
                },
            },
            raise_on_error=False,
        )
        assert aggregate.is_error


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


async def test_catalogue_tools_register_discover_inspect_and_update():
    """MCP discovery preserves registered identities and source freshness."""
    async with ledger_server() as client:
        await _call(client, "tool_create_sheet", {"title": "Claims"})
        await _call(
            client,
            "tool_update_cells",
            {
                "sheet": "Claims",
                "range": "A1:B2",
                "data": [["Employee", "Amount"], ["A", 185000]],
            },
        )
        snapshot = await _call(client, "tool_get_sheet_snapshot", {"sheet": "Claims"})
        definition = {
            "sheet_id": snapshot["sheet_id"],
            "expected_sheet_revision": snapshot["revision"],
            "table_range": "A1:B2",
            "name": "Employee claims",
            "aliases": ["taxi reimbursement"],
        }
        registered = await _call(
            client, "tool_register_table", {"definition": definition}
        )
        assert registered["status"] == "committed"
        found = await _call(
            client,
            "tool_search_resources",
            {
                "query": {
                    "intent": "taxi reimbursement",
                    "required_columns": ["Amount"],
                },
            },
        )
        assert found["candidates"][0]["table_id"] == registered["table_id"]
        inspected = await _call(
            client, "tool_inspect_resource", {"table_id": registered["table_id"]}
        )
        assert inspected["freshness"] == "current"
        assert len(inspected["columns"]) == 2
        definition["name"] = "Travel claims"
        updated = await _call(
            client,
            "tool_update_table",
            {
                "change": {
                    "table_id": registered["table_id"],
                    "expected_catalogue_revision": 1,
                    "definition": definition,
                }
            },
        )
        assert updated["table_id"] == registered["table_id"]
        assert updated["catalogue_revision"] == 2


async def test_wide_catalogue_schema_remains_discoverable_and_paginated():
    """Large valid schemas cannot turn catalogue commits into response failures."""
    async with ledger_server() as client:
        await _call(client, "tool_create_sheet", {"title": "Wide"})
        headers = [f"{index:03d}" + "x" * 253 for index in range(256)]
        await _call(
            client,
            "tool_update_cells",
            {
                "sheet": "Wide",
                "range": "A1:IV1",
                "data": [headers],
            },
        )
        snapshot = await _call(
            client, "tool_get_sheet_snapshot", {"sheet": "Wide", "range": "A1:A1"}
        )
        registered = await _call(
            client,
            "tool_register_table",
            {
                "definition": {
                    "sheet_id": snapshot["sheet_id"],
                    "expected_sheet_revision": snapshot["revision"],
                    "table_range": "A1:IV1",
                    "name": "Wide claims",
                }
            },
        )
        assert registered["status"] == "committed"
        found = await _call(
            client,
            "tool_search_resources",
            {"query": {"intent": "Wide claims", "limit": 1}},
        )
        assert found["candidates"][0]["table_id"] == registered["table_id"]
        assert found["candidates"][0]["column_count"] == 256
        assert len(found["candidates"][0]["columns"]) == 16
        pages = []
        for offset in range(0, 256, 64):
            page = await _call(
                client,
                "tool_inspect_resource",
                {
                    "table_id": registered["table_id"],
                    "column_offset": offset,
                    "column_limit": 64,
                },
            )
            pages.extend(column["name"] for column in page["columns"])
            assert page["has_more_columns"] is (offset < 192)
        assert pages == headers
