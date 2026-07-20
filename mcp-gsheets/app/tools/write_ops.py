"""
Google Sheets write operations.
Tools for updating cells, adding rows/columns, and modifying spreadsheet data.
"""

from typing import Any, Optional

from googleapiclient.discovery import Resource

from app.infra import get_sheet_id_by_name
from app.utils import logger


def update_cells(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    range_notation: str,
    data: list[list[Any]],
) -> dict[str, Any]:
    """
    Update cells in a Google Spreadsheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range_notation: Cell range in A1 notation (e.g., 'A1:C10')
        data: 2D array of values to write
    
    Returns:
        Result of the update operation
    """
    full_range = f"{sheet}!{range_notation}"
    
    logger.debug(f"Updating cells at {full_range} with {len(data)} rows")
    
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueInputOption="USER_ENTERED",
        body={"values": data},
    ).execute()
    
    logger.info(f"Updated {result.get('updatedCells', 0)} cells in {full_range}")
    return result


def batch_update_cells(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    ranges: dict[str, list[list[Any]]],
) -> dict[str, Any]:
    """
    Batch update multiple ranges in a Google Spreadsheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        ranges: Dictionary mapping range strings to 2D arrays
               e.g., {'A1:B2': [[1, 2], [3, 4]], 'D1:E2': [['a', 'b'], ['c', 'd']]}
    
    Returns:
        Result of the batch update operation
    """
    data = [
        {
            "range": f"{sheet}!{range_str}",
            "values": values,
        }
        for range_str, values in ranges.items()
    ]
    
    logger.debug(f"Batch updating {len(data)} ranges in {sheet}")
    
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": data,
        },
    ).execute()
    
    logger.info(f"Batch updated {result.get('totalUpdatedCells', 0)} cells")
    return result


def append_rows(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    data: list[list[Any]],
    range_notation: str = "A:Z",
) -> dict[str, Any]:
    """
    Append rows to the end of a sheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        data: 2D array of values to append
        range_notation: Range to search for table (default searches all columns)
    
    Returns:
        Result of the append operation
    """
    full_range = f"{sheet}!{range_notation}"
    
    logger.debug(f"Appending {len(data)} rows to {sheet}")
    
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=full_range,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": data},
    ).execute()
    
    updates = result.get("updates", {})
    logger.info(f"Appended {updates.get('updatedRows', 0)} rows to {sheet}")
    return result


def add_rows(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_row: Optional[int] = None,
) -> dict[str, Any]:
    """
    Add empty rows to a sheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        count: Number of rows to add
        start_row: 0-based row index to insert at. If None, adds at beginning.
    
    Returns:
        Result of the operation
    """
    sheet_id = get_sheet_id_by_name(service, spreadsheet_id, sheet)
    
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}
    
    start_index = start_row if start_row is not None else 0
    
    logger.debug(f"Adding {count} rows at index {start_index} in {sheet}")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "ROWS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        },
                        "inheritFromBefore": start_index > 0,
                    }
                }
            ]
        },
    ).execute()
    
    logger.info(f"Added {count} rows at index {start_index}")
    return result


def add_columns(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    count: int,
    start_column: Optional[int] = None,
) -> dict[str, Any]:
    """
    Add empty columns to a sheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        count: Number of columns to add
        start_column: 0-based column index to insert at. If None, adds at beginning.
    
    Returns:
        Result of the operation
    """
    sheet_id = get_sheet_id_by_name(service, spreadsheet_id, sheet)
    
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}
    
    start_index = start_column if start_column is not None else 0
    
    logger.debug(f"Adding {count} columns at index {start_index} in {sheet}")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "insertDimension": {
                        "range": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": start_index,
                            "endIndex": start_index + count,
                        },
                        "inheritFromBefore": start_index > 0,
                    }
                }
            ]
        },
    ).execute()
    
    logger.info(f"Added {count} columns at index {start_index}")
    return result


def clear_range(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    range_notation: str,
) -> dict[str, Any]:
    """
    Clear values from a range (keeps formatting).
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range_notation: Cell range in A1 notation to clear
    
    Returns:
        Result of the clear operation
    """
    full_range = f"{sheet}!{range_notation}"
    
    logger.debug(f"Clearing range {full_range}")
    
    result = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=full_range,
    ).execute()
    
    logger.info(f"Cleared range {full_range}")
    return result