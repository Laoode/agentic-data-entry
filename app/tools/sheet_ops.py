"""
Google Sheets management operations.
Tools for creating, copying, renaming sheets and performing batch operations.
"""

from typing import Any

from googleapiclient.discovery import Resource

from app.infra import get_sheet_id_by_name
from app.utils import logger


def create_sheet(
    service: Resource,
    spreadsheet_id: str,
    title: str,
) -> dict[str, Any]:
    """
    Create a new sheet tab in an existing spreadsheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        title: Title for the new sheet tab
    
    Returns:
        Information about the newly created sheet
    """
    logger.debug(f"Creating sheet '{title}' in spreadsheet {spreadsheet_id}")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": title,
                        }
                    }
                }
            ]
        },
    ).execute()
    
    new_sheet_props = result["replies"][0]["addSheet"]["properties"]
    
    logger.info(f"Created sheet '{title}' with ID {new_sheet_props['sheetId']}")
    
    return {
        "sheetId": new_sheet_props["sheetId"],
        "title": new_sheet_props["title"],
        "index": new_sheet_props.get("index"),
        "spreadsheetId": spreadsheet_id,
    }


def rename_sheet(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    new_name: str,
) -> dict[str, Any]:
    """
    Rename a sheet in a Google Spreadsheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: Current sheet name
        new_name: New sheet name
    
    Returns:
        Result of the operation
    """
    sheet_id = get_sheet_id_by_name(service, spreadsheet_id, sheet)
    
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}
    
    logger.debug(f"Renaming sheet '{sheet}' to '{new_name}'")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": new_name,
                        },
                        "fields": "title",
                    }
                }
            ]
        },
    ).execute()
    
    logger.info(f"Renamed sheet '{sheet}' to '{new_name}'")
    return result


def copy_sheet(
    service: Resource,
    src_spreadsheet: str,
    src_sheet: str,
    dst_spreadsheet: str,
    dst_sheet: str,
) -> dict[str, Any]:
    """
    Copy a sheet from one spreadsheet to another.
    
    Args:
        service: Google Sheets API service
        src_spreadsheet: Source spreadsheet ID
        src_sheet: Source sheet name
        dst_spreadsheet: Destination spreadsheet ID
        dst_sheet: Name for the copied sheet
    
    Returns:
        Result of the operation
    """
    src_sheet_id = get_sheet_id_by_name(service, src_spreadsheet, src_sheet)
    
    if src_sheet_id is None:
        return {"error": f"Source sheet '{src_sheet}' not found"}
    
    logger.debug(f"Copying sheet '{src_sheet}' to spreadsheet {dst_spreadsheet}")
    
    # Copy the sheet
    copy_result = service.spreadsheets().sheets().copyTo(
        spreadsheetId=src_spreadsheet,
        sheetId=src_sheet_id,
        body={"destinationSpreadsheetId": dst_spreadsheet},
    ).execute()
    
    # Rename if needed
    if copy_result.get("title") != dst_sheet:
        copy_sheet_id = copy_result["sheetId"]
        
        rename_result = service.spreadsheets().batchUpdate(
            spreadsheetId=dst_spreadsheet,
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": copy_sheet_id,
                                "title": dst_sheet,
                            },
                            "fields": "title",
                        }
                    }
                ]
            },
        ).execute()
        
        logger.info(f"Copied and renamed sheet to '{dst_sheet}'")
        return {"copy": copy_result, "rename": rename_result}
    
    logger.info(f"Copied sheet '{src_sheet}' successfully")
    return {"copy": copy_result}


def delete_sheet(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
) -> dict[str, Any]:
    """
    Delete a sheet from a spreadsheet.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: Name of the sheet to delete
    
    Returns:
        Result of the operation
    """
    sheet_id = get_sheet_id_by_name(service, spreadsheet_id, sheet)
    
    if sheet_id is None:
        return {"error": f"Sheet '{sheet}' not found"}
    
    logger.debug(f"Deleting sheet '{sheet}' from spreadsheet {spreadsheet_id}")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "deleteSheet": {
                        "sheetId": sheet_id,
                    }
                }
            ]
        },
    ).execute()
    
    logger.info(f"Deleted sheet '{sheet}'")
    return result


def batch_update(
    service: Resource,
    spreadsheet_id: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute a batch update on a Google Spreadsheet.
    Provides access to all batchUpdate operations.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        requests: List of request objects for batchUpdate operations
                 Common operations include:
                 - addSheet, deleteSheet
                 - updateSheetProperties
                 - insertDimension, deleteDimension
                 - updateCells, updateBorders
                 - addConditionalFormatRule
                 - and more...
    
    Returns:
        Result of the batch update operation
    """
    if not requests:
        return {"error": "requests list cannot be empty"}
    
    if not all(isinstance(req, dict) for req in requests):
        return {"error": "Each request must be a dictionary"}
    
    logger.debug(f"Executing batch update with {len(requests)} requests")
    
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()
    
    logger.info(f"Batch update completed with {len(result.get('replies', []))} replies")
    return result