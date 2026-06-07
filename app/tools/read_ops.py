"""
Google Sheets read operations.
Tools for fetching data, formulas, and metadata from spreadsheets.
"""

from typing import Any, Optional

from googleapiclient.discovery import Resource

from app.utils import logger


def get_sheet_data(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    range_notation: Optional[str] = None,
    include_grid_data: bool = False,
) -> dict[str, Any]:
    """
    Get data from a specific sheet in a Google Spreadsheet.

    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet (found in the URL)
        sheet: The name of the sheet tab
        range_notation: Optional cell range in A1 notation (e.g., 'A1:C10').
                       If not provided, gets all data.
        include_grid_data: If True, includes cell formatting metadata.
                          Warning: Significantly increases response size.

    Returns:
        Dictionary containing spreadsheet data
    """
    full_range = f"{sheet}!{range_notation}" if range_notation else sheet

    logger.debug(f"Fetching data from {spreadsheet_id}, range: {full_range}")

    if include_grid_data:
        result = (
            service.spreadsheets()
            .get(
                spreadsheetId=spreadsheet_id,
                ranges=[full_range],
                includeGridData=True,
            )
            .execute()
        )
    else:
        values_result = (
            service.spreadsheets()
            .values()
            .get(
                spreadsheetId=spreadsheet_id,
                range=full_range,
            )
            .execute()
        )

        result = {
            "spreadsheetId": spreadsheet_id,
            "range": full_range,
            "values": values_result.get("values", []),
        }

    logger.info(f"Successfully fetched data from {full_range}")
    return result


def get_sheet_formulas(
    service: Resource,
    spreadsheet_id: str,
    sheet: str,
    range_notation: Optional[str] = None,
) -> list[list[Any]]:
    """
    Get formulas from a specific sheet in a Google Spreadsheet.

    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet
        sheet: The name of the sheet tab
        range_notation: Optional cell range in A1 notation

    Returns:
        2D array of formulas
    """
    full_range = f"{sheet}!{range_notation}" if range_notation else sheet

    logger.debug(f"Fetching formulas from {spreadsheet_id}, range: {full_range}")

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=full_range,
            valueRenderOption="FORMULA",
        )
        .execute()
    )

    formulas = result.get("values", [])
    logger.info(f"Successfully fetched {len(formulas)} rows of formulas")
    return formulas


def list_sheets(
    service: Resource,
    spreadsheet_id: str,
) -> list[dict[str, Any]]:
    """
    List all sheets in a Google Spreadsheet.

    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet

    Returns:
        List of sheet info dictionaries with title and sheetId
    """
    logger.debug(f"Listing sheets in spreadsheet {spreadsheet_id}")

    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    sheets = [
        {
            "title": sheet["properties"]["title"],
            "sheetId": sheet["properties"]["sheetId"],
            "index": sheet["properties"].get("index", 0),
        }
        for sheet in spreadsheet.get("sheets", [])
    ]

    logger.info(f"Found {len(sheets)} sheets in spreadsheet")
    return sheets


def get_spreadsheet_info(
    service: Resource,
    spreadsheet_id: str,
) -> dict[str, Any]:
    """
    Get basic information about a Google Spreadsheet.

    Args:
        service: Google Sheets API service
        spreadsheet_id: The ID of the spreadsheet

    Returns:
        Dictionary with spreadsheet title and sheet information
    """
    logger.debug(f"Getting info for spreadsheet {spreadsheet_id}")

    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()

    info = {
        "spreadsheetId": spreadsheet_id,
        "title": spreadsheet.get("properties", {}).get("title", "Unknown"),
        "sheets": [
            {
                "title": sheet["properties"]["title"],
                "sheetId": sheet["properties"]["sheetId"],
                "gridProperties": sheet["properties"].get("gridProperties", {}),
            }
            for sheet in spreadsheet.get("sheets", [])
        ],
    }

    logger.info(f"Retrieved info for '{info['title']}'")
    return info


def get_multiple_sheet_data(
    service: Resource,
    queries: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """
    Get data from multiple sheets in one call.

    Args:
        service: Google Sheets API service
        queries: List of dicts.  Required key: 'sheet'.  Optional keys:
                 'spreadsheet_id' (resolved by caller before this function),
                 'range' (A1 notation; omit to fetch the entire sheet).
                 Example (minimal): [{'sheet': 'Sheet1'}]
                 Example (with range): [{'sheet': 'Sheet1', 'range': 'A1:B5'}]

    Returns:
        List of results, each containing query params and 'data' or 'error'
    """
    results = []

    for query in queries:
        spreadsheet_id = query.get("spreadsheet_id")
        sheet = query.get("sheet")
        range_str = query.get("range") or ""  # empty = entire sheet

        if not all([spreadsheet_id, sheet]):
            results.append(
                {
                    **query,
                    "error": "Missing required keys: 'spreadsheet_id' and 'sheet'",
                }
            )
            continue

        try:
            # When no range is given, use just the sheet name (fetches all data)
            full_range = f"{sheet}!{range_str}" if range_str else sheet
            result = (
                service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=spreadsheet_id,
                    range=full_range,
                )
                .execute()
            )

            results.append(
                {
                    **query,
                    "data": result.get("values", []),
                }
            )
            logger.debug(f"Fetched data for query: {full_range}")

        except Exception as e:
            logger.error(f"Error fetching {query}: {e}")
            results.append({**query, "error": str(e)})

    logger.info(
        f"Processed {len(queries)} queries, {len([r for r in results if 'data' in r])} successful"
    )
    return results
