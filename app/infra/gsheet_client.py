"""
Google Sheets API client infrastructure.
Handles authentication and service initialization using service account credentials.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource

from app.utils import logger


# Google Sheets API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


@dataclass
class SheetsContext:
    """
    Context container for Google Sheets service.
    
    Attributes:
        service: Google Sheets API service instance
        default_sheet_id: Optional default spreadsheet ID for operations
    """
    service: Resource
    default_sheet_id: Optional[str] = None


class SheetsClientError(Exception):
    """Custom exception for Sheets client errors."""
    pass


def get_credentials() -> service_account.Credentials:
    """
    Load Google service account credentials.
    
    Returns:
        Authenticated credentials object
        
    Raises:
        SheetsClientError: If credentials cannot be loaded
    """
    service_account_path = os.environ.get("SERVICE_ACCOUNT_PATH", "service_account.json")
    
    if not os.path.exists(service_account_path):
        raise SheetsClientError(
            f"Service account file not found: {service_account_path}. "
            "Please ensure SERVICE_ACCOUNT_PATH is set correctly."
        )
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=SCOPES,
        )
        logger.info(f"Successfully loaded credentials from {service_account_path}")
        return credentials
    except json.JSONDecodeError as e:
        raise SheetsClientError(f"Invalid JSON in service account file: {e}")
    except Exception as e:
        raise SheetsClientError(f"Failed to load credentials: {e}")


def build_sheets_service(credentials: service_account.Credentials) -> Resource:
    """
    Build Google Sheets API service.
    
    Args:
        credentials: Authenticated credentials
        
    Returns:
        Google Sheets API service instance
    """
    service = build("sheets", "v4", credentials=credentials)
    logger.info("Google Sheets service initialized successfully")
    return service


def create_sheets_context() -> SheetsContext:
    """
    Create and initialize the Sheets context with authenticated service.
    
    Returns:
        SheetsContext with initialized service
        
    Raises:
        SheetsClientError: If initialization fails
    """
    credentials = get_credentials()
    service = build_sheets_service(credentials)
    default_sheet_id = os.environ.get("SHEET_ID")
    
    if default_sheet_id:
        logger.info(f"Default spreadsheet ID configured: {default_sheet_id}")
    
    return SheetsContext(
        service=service,
        default_sheet_id=default_sheet_id,
    )


def get_sheet_id_by_name(
    service: Resource,
    spreadsheet_id: str,
    sheet_name: str,
) -> Optional[int]:
    """
    Get the numeric sheet ID from a sheet name.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: The spreadsheet ID
        sheet_name: Name of the sheet tab
        
    Returns:
        Numeric sheet ID or None if not found
    """
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in spreadsheet.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                return sheet["properties"]["sheetId"]
        return None
    except Exception as e:
        logger.error(f"Failed to get sheet ID for '{sheet_name}': {e}")
        return None