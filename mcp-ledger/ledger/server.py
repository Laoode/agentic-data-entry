"""Ledger MCP server: the Google Sheets tool surface backed by Postgres.

Drop-in replacement for mcp-gsheets: identical tool names, parameter
names, and response shapes, so the data-entry agents, prompts, and the
e2e dataset run unchanged. `spreadsheet_id` maps to a ledger workspace
(default from LEDGER_WORKSPACE, mirroring the old SHEET_ID fallback).
"""

import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from ledger import grid as g
from ledger.store import (
    DEFAULT_WORKSPACE,
    LedgerStore,
    SheetExistsError,
    SheetNotFoundError,
)

load_dotenv()

LEDGER_TITLE = os.environ.get("LEDGER_TITLE", "Klaudia Ledger")


@asynccontextmanager
async def ledger_lifespan(server: FastMCP) -> AsyncIterator[LedgerStore]:
    dsn = os.environ.get("DATABASE_URL", "")
    if not dsn:
        raise RuntimeError("mcp-ledger requires DATABASE_URL (Postgres DSN)")
    store = LedgerStore(dsn)
    await store.connect()
    try:
        yield store
    finally:
        await store.close()


HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("FASTMCP_PORT", "8003"))

mcp = FastMCP(
    name="mcp-ledger",
    instructions=(
        "Ledger MCP Server for data entry operations. "
        "Provides tools for reading, writing, and managing spreadsheet-style "
        "ledger tabs stored in Postgres. Use for receipt data entry, automated "
        "data input, and sheet management. A default workspace is configured; "
        "tools use it automatically when spreadsheet_id is omitted."
    ),
    lifespan=ledger_lifespan,
    host=HOST,
    port=PORT,
)


def _store(ctx: Context) -> LedgerStore:
    return ctx.request_context.lifespan_context


def _workspace(spreadsheet_id: Optional[str]) -> str:
    return spreadsheet_id or DEFAULT_WORKSPACE


async def _resolve_title(store: LedgerStore, workspace: str, name: str) -> str:
    """Resolve an LLM-supplied tab name to the exact stored title.

    Handles case differences and dash-spacing normalization, mirroring
    mcp-gsheets' fuzzy resolution.
    """
    sheets = await store.list_sheets(workspace)

    def _norm(s: str) -> str:
        return re.sub(r"\s*-\s*", "-", s.strip().lower())

    for sheet in sheets:
        if sheet["title"] == name:
            return name
    for sheet in sheets:
        if sheet["title"].strip().lower() == name.strip().lower():
            return sheet["title"]
    name_norm = _norm(name)
    for sheet in sheets:
        if _norm(sheet["title"]) == name_norm:
            return sheet["title"]
    return name  # let the store raise SheetNotFoundError with the raw name


def _range_label(sheet: str, notation: Optional[str]) -> str:
    return f"{sheet}!{notation}" if notation else sheet


# ── Read operations ──────────────────────────────────────────────────────────


@mcp.tool()
async def tool_get_sheet_data(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    range: Optional[str] = None,
    include_grid_data: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get data from a sheet tab in the ledger.

    Args:
        sheet: The name of the sheet tab.
        spreadsheet_id: Optional workspace id. If omitted, uses the default.
        range: Optional cell range in A1 notation (e.g., 'A1:C10').
        include_grid_data: Accepted for compatibility; ignored.

    Returns:
        Dict with spreadsheetId, range, and values (2D array).
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    values = g.slice_range(await store.get_grid(workspace, title), range)
    return {
        "spreadsheetId": workspace,
        "range": _range_label(title, range),
        "values": values,
    }


@mcp.tool()
async def tool_get_sheet_formulas(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    range: Optional[str] = None,
    ctx: Context = None,
) -> list[list[Any]]:
    """
    Get formulas from a sheet tab. The ledger stores plain values, so this
    returns the same grid as tool_get_sheet_data.

    Args:
        sheet: The name of the sheet tab.
        spreadsheet_id: Optional workspace id.
        range: Optional cell range in A1 notation.

    Returns:
        2D array of values.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    return g.slice_range(await store.get_grid(workspace, title), range)


@mcp.tool()
async def tool_list_sheets(
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    List all sheet tabs in the ledger workspace.

    Args:
        spreadsheet_id: Optional workspace id.

    Returns:
        List of dicts with title, sheetId, and index.
    """
    return await _store(ctx).list_sheets(_workspace(spreadsheet_id))


@mcp.tool()
async def tool_get_spreadsheet_info(
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get workspace title and all sheet tabs with their dimensions.

    Args:
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with spreadsheetId, title, and sheets list.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    sheets = []
    for sheet in await store.list_sheets(workspace):
        sheet_grid = await store.get_grid(workspace, sheet["title"])
        sheets.append(
            {
                "title": sheet["title"],
                "sheetId": sheet["sheetId"],
                "gridProperties": {
                    "rowCount": len(sheet_grid),
                    "columnCount": max((len(r) for r in sheet_grid), default=0),
                },
            }
        )
    return {"spreadsheetId": workspace, "title": LEDGER_TITLE, "sheets": sheets}


@mcp.tool()
async def tool_get_multiple_sheet_data(
    queries: list[dict[str, str]],
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    Get data from multiple sheet tabs in one call.

    Args:
        queries: List of dicts. Required key: 'sheet'. Optional keys:
                 'spreadsheet_id', 'range' (A1 notation; omit for all data).

    Returns:
        List of results, each containing the query params plus 'data' or
        'error'.
    """
    store = _store(ctx)
    results: list[dict[str, Any]] = []
    for query in queries:
        sheet = query.get("sheet")
        if not sheet:
            results.append({**query, "error": "Missing required key: 'sheet'"})
            continue
        workspace = _workspace(query.get("spreadsheet_id"))
        try:
            title = await _resolve_title(store, workspace, sheet)
            values = g.slice_range(
                await store.get_grid(workspace, title), query.get("range") or None
            )
            results.append({**query, "data": values})
        except SheetNotFoundError as exc:
            results.append({**query, "error": str(exc)})
    return results


# ── Write operations ─────────────────────────────────────────────────────────


@mcp.tool()
async def tool_update_cells(
    sheet: str,
    range: str,
    data: list[list[Any]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Update cells in a sheet tab.

    Args:
        sheet: The name of the sheet tab.
        range: Cell range in A1 notation (e.g., 'A1:C10').
        data: 2D array of values to write.
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with updatedRange and updatedCells.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    await store.mutate_grid(
        workspace, title, lambda old: g.write_range(old, range, data)
    )
    cells = sum(len(row) for row in data)
    return {
        "spreadsheetId": workspace,
        "updatedRange": _range_label(title, range),
        "updatedRows": len(data),
        "updatedCells": cells,
    }


@mcp.tool()
async def tool_batch_update_cells(
    sheet: str,
    ranges: dict[str, list[list[Any]]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Batch update multiple ranges in a sheet tab.

    Args:
        sheet: The name of the sheet tab.
        ranges: Dict mapping A1 range strings to 2D arrays of values.
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with totalUpdatedCells.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)

    def _apply(old: list[list[Any]]) -> list[list[Any]]:
        new = old
        for range_str, values in ranges.items():
            new = g.write_range(new, range_str, values)
        return new

    await store.mutate_grid(workspace, title, _apply)
    total = sum(len(row) for values in ranges.values() for row in values)
    return {"spreadsheetId": workspace, "totalUpdatedCells": total}


@mcp.tool()
async def tool_append_rows(
    sheet: str,
    data: list[list[Any]],
    spreadsheet_id: Optional[str] = None,
    range: str = "A:Z",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Append rows after the last row containing data.

    Args:
        sheet: The name of the sheet tab.
        data: 2D array of values to append.
        spreadsheet_id: Optional workspace id.
        range: Accepted for compatibility; append always follows the data.

    Returns:
        Dict with updates.updatedRows, mirroring the Sheets append response.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    start_row = {"value": 0}

    def _apply(old: list[list[Any]]) -> list[list[Any]]:
        start_row["value"] = g.last_data_row(old)
        return g.write_range(old, f"A{start_row['value'] + 1}", data)

    await store.mutate_grid(workspace, title, _apply)
    first = start_row["value"] + 1
    updated_range = f"{title}!A{first}:{g.index_to_col(max((len(r) for r in data), default=1) - 1)}{first + len(data) - 1}"
    return {
        "spreadsheetId": workspace,
        "updates": {
            "updatedRange": updated_range,
            "updatedRows": len(data),
            "updatedCells": sum(len(row) for row in data),
        },
    }


@mcp.tool()
async def tool_add_rows(
    sheet: str,
    count: int,
    spreadsheet_id: Optional[str] = None,
    start_row: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Insert empty rows into a sheet tab.

    Args:
        sheet: The name of the sheet tab.
        count: Number of rows to insert.
        spreadsheet_id: Optional workspace id.
        start_row: 0-based row index to insert at (default 0).

    Returns:
        Confirmation dict.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    start = start_row if start_row is not None else 0
    await store.mutate_grid(
        workspace, title, lambda old: g.insert_rows(old, start, count)
    )
    return {"spreadsheetId": workspace, "insertedRows": count, "startIndex": start}


@mcp.tool()
async def tool_add_columns(
    sheet: str,
    count: int,
    spreadsheet_id: Optional[str] = None,
    start_column: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Insert empty columns into a sheet tab.

    Args:
        sheet: The name of the sheet tab.
        count: Number of columns to insert.
        spreadsheet_id: Optional workspace id.
        start_column: 0-based column index to insert at (default 0).

    Returns:
        Confirmation dict.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    start = start_column if start_column is not None else 0
    await store.mutate_grid(
        workspace, title, lambda old: g.insert_cols(old, start, count)
    )
    return {"spreadsheetId": workspace, "insertedColumns": count, "startIndex": start}


@mcp.tool()
async def tool_clear_range(
    sheet: str,
    range: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Clear values from a range (dimensions are preserved).

    Args:
        sheet: The name of the sheet tab.
        range: Cell range in A1 notation to clear.
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with clearedRange.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    await store.mutate_grid(workspace, title, lambda old: g.clear_range(old, range))
    return {"spreadsheetId": workspace, "clearedRange": _range_label(title, range)}


# ── Sheet management ─────────────────────────────────────────────────────────


@mcp.tool()
async def tool_create_sheet(
    title: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Create a new empty sheet tab.

    Args:
        title: Title for the new sheet tab.
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with sheetId, title, index, and spreadsheetId.
    """
    workspace = _workspace(spreadsheet_id)
    try:
        created = await _store(ctx).create_sheet(workspace, title)
    except SheetExistsError as exc:
        return {"error": str(exc)}
    return {**created, "spreadsheetId": workspace}


@mcp.tool()
async def tool_rename_sheet(
    sheet: str,
    new_name: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Rename a sheet tab.

    Args:
        sheet: Current sheet name.
        new_name: New sheet name.
        spreadsheet_id: Optional workspace id.

    Returns:
        Confirmation dict, or error if the sheet is missing.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    try:
        await store.rename_sheet(workspace, title, new_name)
    except SheetNotFoundError as exc:
        return {"error": str(exc)}
    return {"spreadsheetId": workspace, "renamed": {"from": title, "to": new_name}}


@mcp.tool()
async def tool_copy_sheet(
    src_sheet: str,
    dst_sheet: str,
    src_spreadsheet: Optional[str] = None,
    dst_spreadsheet: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Copy a sheet tab, including its data.

    Args:
        src_sheet: Source sheet name.
        dst_sheet: Name for the copied sheet.
        src_spreadsheet: Optional source workspace id.
        dst_spreadsheet: Optional destination workspace id.

    Returns:
        Dict describing the copy, or error.
    """
    store = _store(ctx)
    src_ws = _workspace(src_spreadsheet)
    dst_ws = _workspace(dst_spreadsheet)
    title = await _resolve_title(store, src_ws, src_sheet)
    try:
        src_grid = await store.get_grid(src_ws, title)
        created = await store.create_sheet(dst_ws, dst_sheet, grid=src_grid)
    except (SheetNotFoundError, SheetExistsError) as exc:
        return {"error": str(exc)}
    return {"copy": {**created, "spreadsheetId": dst_ws}}


@mcp.tool()
async def tool_delete_sheet(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Delete a sheet tab and its data.

    Args:
        sheet: Name of the sheet to delete.
        spreadsheet_id: Optional workspace id.

    Returns:
        Confirmation dict, or error if the sheet is missing.
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    title = await _resolve_title(store, workspace, sheet)
    try:
        await store.delete_sheet(workspace, title)
    except SheetNotFoundError as exc:
        return {"error": str(exc)}
    return {"spreadsheetId": workspace, "deleted": title}


@mcp.tool()
async def tool_batch_update(
    requests: list[dict[str, Any]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Execute batch structural operations. Supported request types:
    addSheet, deleteSheet, updateSheetProperties (rename). Other Sheets
    batchUpdate request types are not supported by the ledger backend.

    Args:
        requests: List of request objects.
        spreadsheet_id: Optional workspace id.

    Returns:
        Dict with one reply per request (or error).
    """
    store = _store(ctx)
    workspace = _workspace(spreadsheet_id)
    if not requests:
        return {"error": "requests list cannot be empty"}
    replies: list[dict[str, Any]] = []
    for request in requests:
        if "addSheet" in request:
            title = request["addSheet"].get("properties", {}).get("title", "")
            try:
                created = await store.create_sheet(workspace, title)
                replies.append({"addSheet": {"properties": created}})
            except SheetExistsError as exc:
                replies.append({"error": str(exc)})
        elif "deleteSheet" in request:
            sheet_id = request["deleteSheet"].get("sheetId")
            sheets = await store.list_sheets(workspace)
            match = next((s for s in sheets if s["sheetId"] == sheet_id), None)
            if match is None:
                replies.append({"error": f"sheetId {sheet_id} not found"})
                continue
            await store.delete_sheet(workspace, match["title"])
            replies.append({})
        elif "updateSheetProperties" in request:
            props = request["updateSheetProperties"].get("properties", {})
            sheet_id = props.get("sheetId")
            new_title = props.get("title")
            sheets = await store.list_sheets(workspace)
            match = next((s for s in sheets if s["sheetId"] == sheet_id), None)
            if match is None or not new_title:
                replies.append({"error": f"sheetId {sheet_id} not found"})
                continue
            await store.rename_sheet(workspace, match["title"], new_title)
            replies.append({})
        else:
            replies.append(
                {"error": f"Unsupported request type: {list(request.keys())}"}
            )
    return {"spreadsheetId": workspace, "replies": replies}
