"""
Google Sheets MCP Server Application.
FastMCP server exposing Google Sheets operations as MCP tools.
"""

import os
import re
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from app.infra import SheetsContext, create_sheets_context
from app.tools import (
    add_columns,
    add_rows,
    append_rows,
    batch_update,
    batch_update_cells,
    clear_range,
    copy_sheet,
    create_sheet,
    delete_sheet,
    get_multiple_sheet_data,
    get_sheet_data,
    get_sheet_formulas,
    get_spreadsheet_info,
    list_sheets,
    rename_sheet,
    update_cells,
)
from app.utils import logger

# Load environment variables
load_dotenv()


@asynccontextmanager
async def sheets_lifespan(server: FastMCP) -> AsyncIterator[SheetsContext]:
    """
    Manage Google Sheets API connection lifecycle.

    Yields:
        SheetsContext with authenticated service
    """
    logger.info("Initializing Google Sheets MCP server...")

    try:
        context = create_sheets_context()
        logger.info("Google Sheets service ready")
        yield context
    finally:
        logger.info("Google Sheets MCP server shutting down")


# Server configuration
HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("FASTMCP_PORT", "8002"))

# Initialize FastMCP server
mcp = FastMCP(
    name="mcp-gsheets",
    instructions=(
        "Google Sheets MCP Server for data entry operations. "
        "Provides tools for reading, writing, and managing Google Spreadsheets. "
        "Use for receipt data entry, automated data input, and spreadsheet management. "
        "A default spreadsheet is configured via the SHEET_ID environment variable; "
        "tools will use it automatically when spreadsheet_id is omitted."
    ),
    lifespan=sheets_lifespan,
    host=HOST,
    port=PORT,
)


def _resolve_sheet_id(ctx: Context, spreadsheet_id: Optional[str]) -> str:
    """Return the provided spreadsheet_id, or fall back to SHEET_ID env default."""
    if spreadsheet_id:
        return spreadsheet_id
    default = ctx.request_context.lifespan_context.default_sheet_id
    if not default:
        raise ValueError(
            "spreadsheet_id not provided and no SHEET_ID default is configured on the MCP server."
        )
    return default


def _fuzzy_resolve_sheet_name(
    service: Any,
    spreadsheet_id: str,
    name: str,
) -> Optional[str]:
    """Find the actual tab name that best matches *name*.

    Handles two common LLM normalization errors:
    1. Case differences ("sheet1" vs "Sheet1")
    2. Spacing around dashes ("Foo - Bar" vs "Foo- Bar" vs "Foo-Bar")

    Returns the exact tab title from the spreadsheet, or None if no match.
    """
    try:
        sheets = list_sheets(service, spreadsheet_id)
    except Exception:
        return None

    def _norm(s: str) -> str:
        # Collapse all whitespace around hyphens and lowercase
        return re.sub(r"\s*-\s*", "-", s.strip().lower())

    name_norm = _norm(name)
    for sheet in sheets:
        title = sheet["title"]
        if title.strip().lower() == name.strip().lower():
            return title  # exact case-insensitive
        if _norm(title) == name_norm:
            return title  # dash-spacing normalised
    return None


# ============================================================================
# READ OPERATIONS
# ============================================================================


@mcp.tool()
def tool_get_sheet_data(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    range: Optional[str] = None,
    include_grid_data: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get data from a specific sheet in a Google Spreadsheet.

    Args:
        sheet: The name of the sheet tab (MUST match the tab name exactly;
               minor spacing differences around dashes are auto-corrected).
        spreadsheet_id: Optional spreadsheet ID (found in URL after /d/).
                        If omitted, uses the server's default SHEET_ID.
        range: Optional cell range in A1 notation (e.g., 'A1:C10'). Gets all data if not provided.
        include_grid_data: If True, includes cell formatting metadata. Default False for efficiency.

    Returns:
        Dictionary containing spreadsheet data with 'values' key
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    try:
        return get_sheet_data(service, sid, sheet, range, include_grid_data)
    except Exception as exc:
        if "Unable to parse range" in str(exc):
            # LLM may have normalised the sheet name (e.g. added a space before a
            # dash). Try a fuzzy match against the actual tab list and retry once.
            resolved = _fuzzy_resolve_sheet_name(service, sid, sheet)
            if resolved and resolved != sheet:
                logger.warning(
                    "Sheet name %r auto-corrected to %r via fuzzy match", sheet, resolved
                )
                return get_sheet_data(service, sid, resolved, range, include_grid_data)
        raise


@mcp.tool()
def tool_get_sheet_formulas(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    range: Optional[str] = None,
    ctx: Context = None,
) -> list[list[Any]]:
    """
    Get formulas from a specific sheet in a Google Spreadsheet.

    Args:
        sheet: The name of the sheet tab
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.
        range: Optional cell range in A1 notation

    Returns:
        2D array of formulas
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return get_sheet_formulas(service, sid, sheet, range)


@mcp.tool()
def tool_list_sheets(
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    List all sheet tabs in a Google Spreadsheet.

    Args:
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        List of sheet info with title, sheetId, and index
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return list_sheets(service, sid)


@mcp.tool()
def tool_get_spreadsheet_info(
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get basic information about a Google Spreadsheet including title and all sheets.

    Args:
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Dictionary with spreadsheet title and sheet information
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return get_spreadsheet_info(service, sid)


@mcp.tool()
def tool_get_multiple_sheet_data(
    queries: list[dict[str, str]],
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    Get data from multiple sheets in a single API round-trip.

    Args:
        queries: List of dicts. Required key per item: 'sheet'.
                 Optional keys: 'range' (A1 notation; omit to fetch the entire sheet),
                 'spreadsheet_id' (falls back to the server's default SHEET_ID).
                 Minimal example: [{'sheet': 'Sheet1'}, {'sheet': 'Sheet2'}]
                 With range:      [{'sheet': 'Sheet1', 'range': 'A1:B10'}]

    Returns:
        List of results with original query params plus 'data' (2-D array) or 'error'
    """
    service = ctx.request_context.lifespan_context.service
    default_sid = ctx.request_context.lifespan_context.default_sheet_id
    resolved = [{**q, "spreadsheet_id": q.get("spreadsheet_id") or default_sid} for q in queries]
    return get_multiple_sheet_data(service, resolved)


# ============================================================================
# WRITE OPERATIONS
# ============================================================================


@mcp.tool()
def tool_update_cells(
    sheet: str,
    range: str,
    data: list[list[Any]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Update cells in a Google Spreadsheet with new values.

    Args:
        sheet: The name of the sheet tab
        range: Cell range in A1 notation (e.g., 'A1:C10')
        data: 2D array of values to write
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result with updatedCells, updatedRows, updatedColumns info
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return update_cells(service, sid, sheet, range, data)


@mcp.tool()
def tool_batch_update_cells(
    sheet: str,
    ranges: dict[str, list[list[Any]]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Update multiple ranges in a single API call for efficiency.

    Args:
        sheet: The name of the sheet tab
        ranges: Dict mapping range strings to 2D value arrays
               e.g., {'A1:B2': [[1, 2], [3, 4]], 'D1:E2': [['a', 'b'], ['c', 'd']]}
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result with totalUpdatedCells info
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return batch_update_cells(service, sid, sheet, ranges)


@mcp.tool()
def tool_append_rows(
    sheet: str,
    data: list[list[Any]],
    spreadsheet_id: Optional[str] = None,
    range: str = "A:Z",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Append rows to the end of existing data in a sheet.
    Ideal for adding new receipt entries without specifying exact row numbers.

    Args:
        sheet: The name of the sheet tab
        data: 2D array of values to append (each inner list is a row)
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.
        range: Range to search for existing table (default: all columns)

    Returns:
        Result with updates info including updatedRows
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return append_rows(service, sid, sheet, data, range)


@mcp.tool()
def tool_add_rows(
    sheet: str,
    count: int,
    spreadsheet_id: Optional[str] = None,
    start_row: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Add empty rows to a sheet at a specific position.

    Args:
        sheet: The name of the sheet tab
        count: Number of rows to add
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.
        start_row: 0-based row index to insert at. If None, adds at beginning.

    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return add_rows(service, sid, sheet, count, start_row)


@mcp.tool()
def tool_add_columns(
    sheet: str,
    count: int,
    spreadsheet_id: Optional[str] = None,
    start_column: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Add empty columns to a sheet at a specific position.

    Args:
        sheet: The name of the sheet tab
        count: Number of columns to add
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.
        start_column: 0-based column index to insert at. If None, adds at beginning.

    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return add_columns(service, sid, sheet, count, start_column)


@mcp.tool()
def tool_clear_range(
    sheet: str,
    range: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Clear values from a range while keeping formatting intact.

    Args:
        sheet: The name of the sheet tab
        range: Cell range in A1 notation to clear
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result of the clear operation
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return clear_range(service, sid, sheet, range)


# ============================================================================
# SHEET MANAGEMENT OPERATIONS
# ============================================================================


@mcp.tool()
def tool_create_sheet(
    title: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Create a new sheet tab in an existing spreadsheet.

    Args:
        title: Title for the new sheet tab
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Information about the new sheet including sheetId and title
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return create_sheet(service, sid, title)


@mcp.tool()
def tool_rename_sheet(
    sheet: str,
    new_name: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Rename a sheet tab in a spreadsheet.

    Args:
        sheet: Current sheet name
        new_name: New name for the sheet
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return rename_sheet(service, sid, sheet, new_name)


@mcp.tool()
def tool_copy_sheet(
    src_sheet: str,
    dst_sheet: str,
    src_spreadsheet: Optional[str] = None,
    dst_spreadsheet: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Copy a sheet from one spreadsheet to another.

    Args:
        src_sheet: Source sheet name
        dst_sheet: Name for the copied sheet in destination
        src_spreadsheet: Optional source spreadsheet ID. If omitted, uses the server's default SHEET_ID.
        dst_spreadsheet: Optional destination spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result of the copy operation
    """
    service = ctx.request_context.lifespan_context.service
    src_sid = _resolve_sheet_id(ctx, src_spreadsheet)
    dst_sid = _resolve_sheet_id(ctx, dst_spreadsheet)
    return copy_sheet(service, src_sid, src_sheet, dst_sid, dst_sheet)


@mcp.tool()
def tool_delete_sheet(
    sheet: str,
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Delete a sheet tab from a spreadsheet.
    WARNING: This operation is destructive and cannot be undone.

    Args:
        sheet: Name of the sheet to delete
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result of the delete operation
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return delete_sheet(service, sid, sheet)


@mcp.tool()
def tool_batch_update(
    requests: list[dict[str, Any]],
    spreadsheet_id: Optional[str] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Execute advanced batch operations on a spreadsheet.
    For complex operations like formatting, conditional rules, or multiple structural changes.

    Args:
        requests: List of batchUpdate request objects
                 See Google Sheets API docs for available request types
        spreadsheet_id: Optional spreadsheet ID. If omitted, uses the server's default SHEET_ID.

    Returns:
        Result with replies for each request
    """
    service = ctx.request_context.lifespan_context.service
    sid = _resolve_sheet_id(ctx, spreadsheet_id)
    return batch_update(service, sid, requests)


def main() -> None:
    """Main entry point for MCP server."""
    transport = "stdio"

    # Parse command line args for transport mode
    for i, arg in enumerate(sys.argv):
        if arg == "--transport" and i + 1 < len(sys.argv):
            transport = sys.argv[i + 1]
            break

    logger.info(f"Starting MCP Google Sheets server on {HOST}:{PORT} with {transport} transport")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
