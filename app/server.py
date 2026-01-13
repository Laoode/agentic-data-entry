"""
Google Sheets MCP Server Application.
FastMCP server exposing Google Sheets operations as MCP tools.
"""

import os
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
        "Use for receipt data entry, automated data input, and spreadsheet management."
    ),
    lifespan=sheets_lifespan,
    host=HOST,
    port=PORT,
)


# ============================================================================
# READ OPERATIONS
# ============================================================================


@mcp.tool()
def tool_get_sheet_data(
    spreadsheet_id: str,
    sheet: str,
    range: Optional[str] = None,
    include_grid_data: bool = False,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get data from a specific sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet (found in URL after /d/)
        sheet: The name of the sheet tab
        range: Optional cell range in A1 notation (e.g., 'A1:C10'). Gets all data if not provided.
        include_grid_data: If True, includes cell formatting metadata. Default False for efficiency.
    
    Returns:
        Dictionary containing spreadsheet data with 'values' key
    """
    service = ctx.request_context.lifespan_context.service
    return get_sheet_data(service, spreadsheet_id, sheet, range, include_grid_data)


@mcp.tool()
def tool_get_sheet_formulas(
    spreadsheet_id: str,
    sheet: str,
    range: Optional[str] = None,
    ctx: Context = None,
) -> list[list[Any]]:
    """
    Get formulas from a specific sheet in a Google Spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range: Optional cell range in A1 notation
    
    Returns:
        2D array of formulas
    """
    service = ctx.request_context.lifespan_context.service
    return get_sheet_formulas(service, spreadsheet_id, sheet, range)


@mcp.tool()
def tool_list_sheets(
    spreadsheet_id: str,
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    List all sheet tabs in a Google Spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
    
    Returns:
        List of sheet info with title, sheetId, and index
    """
    service = ctx.request_context.lifespan_context.service
    return list_sheets(service, spreadsheet_id)


@mcp.tool()
def tool_get_spreadsheet_info(
    spreadsheet_id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Get basic information about a Google Spreadsheet including title and all sheets.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
    
    Returns:
        Dictionary with spreadsheet title and sheet information
    """
    service = ctx.request_context.lifespan_context.service
    return get_spreadsheet_info(service, spreadsheet_id)


@mcp.tool()
def tool_get_multiple_sheet_data(
    queries: list[dict[str, str]],
    ctx: Context = None,
) -> list[dict[str, Any]]:
    """
    Get data from multiple ranges across spreadsheets in one call.
    
    Args:
        queries: List of dicts with 'spreadsheet_id', 'sheet', and 'range' keys
                Example: [{'spreadsheet_id': 'abc123', 'sheet': 'Sheet1', 'range': 'A1:B5'}]
    
    Returns:
        List of results with original query params and 'data' or 'error'
    """
    service = ctx.request_context.lifespan_context.service
    return get_multiple_sheet_data(service, queries)


# ============================================================================
# WRITE OPERATIONS
# ============================================================================


@mcp.tool()
def tool_update_cells(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    data: list[list[Any]],
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Update cells in a Google Spreadsheet with new values.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range: Cell range in A1 notation (e.g., 'A1:C10')
        data: 2D array of values to write
    
    Returns:
        Result with updatedCells, updatedRows, updatedColumns info
    """
    service = ctx.request_context.lifespan_context.service
    return update_cells(service, spreadsheet_id, sheet, range, data)


@mcp.tool()
def tool_batch_update_cells(
    spreadsheet_id: str,
    sheet: str,
    ranges: dict[str, list[list[Any]]],
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Update multiple ranges in a single API call for efficiency.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        ranges: Dict mapping range strings to 2D value arrays
               e.g., {'A1:B2': [[1, 2], [3, 4]], 'D1:E2': [['a', 'b'], ['c', 'd']]}
    
    Returns:
        Result with totalUpdatedCells info
    """
    service = ctx.request_context.lifespan_context.service
    return batch_update_cells(service, spreadsheet_id, sheet, ranges)


@mcp.tool()
def tool_append_rows(
    spreadsheet_id: str,
    sheet: str,
    data: list[list[Any]],
    range: str = "A:Z",
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Append rows to the end of existing data in a sheet.
    Ideal for adding new receipt entries without specifying exact row numbers.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        data: 2D array of values to append (each inner list is a row)
        range: Range to search for existing table (default: all columns)
    
    Returns:
        Result with updates info including updatedRows
    """
    service = ctx.request_context.lifespan_context.service
    return append_rows(service, spreadsheet_id, sheet, data, range)


@mcp.tool()
def tool_add_rows(
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_row: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Add empty rows to a sheet at a specific position.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        count: Number of rows to add
        start_row: 0-based row index to insert at. If None, adds at beginning.
    
    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    return add_rows(service, spreadsheet_id, sheet, count, start_row)


@mcp.tool()
def tool_add_columns(
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_column: Optional[int] = None,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Add empty columns to a sheet at a specific position.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        count: Number of columns to add
        start_column: 0-based column index to insert at. If None, adds at beginning.
    
    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    return add_columns(service, spreadsheet_id, sheet, count, start_column)


@mcp.tool()
def tool_clear_range(
    spreadsheet_id: str,
    sheet: str,
    range: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Clear values from a range while keeping formatting intact.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range: Cell range in A1 notation to clear
    
    Returns:
        Result of the clear operation
    """
    service = ctx.request_context.lifespan_context.service
    return clear_range(service, spreadsheet_id, sheet, range)


# ============================================================================
# SHEET MANAGEMENT OPERATIONS
# ============================================================================


@mcp.tool()
def tool_create_sheet(
    spreadsheet_id: str,
    title: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Create a new sheet tab in an existing spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        title: Title for the new sheet tab
    
    Returns:
        Information about the new sheet including sheetId and title
    """
    service = ctx.request_context.lifespan_context.service
    return create_sheet(service, spreadsheet_id, title)


@mcp.tool()
def tool_rename_sheet(
    spreadsheet_id: str,
    sheet: str,
    new_name: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Rename a sheet tab in a spreadsheet.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: Current sheet name
        new_name: New name for the sheet
    
    Returns:
        Result of the operation
    """
    service = ctx.request_context.lifespan_context.service
    return rename_sheet(service, spreadsheet_id, sheet, new_name)


@mcp.tool()
def tool_copy_sheet(
    src_spreadsheet: str,
    src_sheet: str,
    dst_spreadsheet: str,
    dst_sheet: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Copy a sheet from one spreadsheet to another.
    
    Args:
        src_spreadsheet: Source spreadsheet ID
        src_sheet: Source sheet name
        dst_spreadsheet: Destination spreadsheet ID
        dst_sheet: Name for the copied sheet in destination
    
    Returns:
        Result of the copy operation
    """
    service = ctx.request_context.lifespan_context.service
    return copy_sheet(service, src_spreadsheet, src_sheet, dst_spreadsheet, dst_sheet)


@mcp.tool()
def tool_delete_sheet(
    spreadsheet_id: str,
    sheet: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Delete a sheet tab from a spreadsheet.
    WARNING: This operation is destructive and cannot be undone.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        sheet: Name of the sheet to delete
    
    Returns:
        Result of the delete operation
    """
    service = ctx.request_context.lifespan_context.service
    return delete_sheet(service, spreadsheet_id, sheet)


@mcp.tool()
def tool_batch_update(
    spreadsheet_id: str,
    requests: list[dict[str, Any]],
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Execute advanced batch operations on a spreadsheet.
    For complex operations like formatting, conditional rules, or multiple structural changes.
    
    Args:
        spreadsheet_id: The ID of the spreadsheet
        requests: List of batchUpdate request objects
                 See Google Sheets API docs for available request types
    
    Returns:
        Result with replies for each request
    """
    service = ctx.request_context.lifespan_context.service
    return batch_update(service, spreadsheet_id, requests)


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