# MCP Google Sheets Server

A Model Context Protocol (MCP) server for Google Sheets integration, designed for the **Klaudia** data entry agent system.

## Overview

This server exposes Google Sheets operations as MCP tools, enabling automated data entry for receipt processing and reimbursement workflows.

## Features

### Read Operations
- `tool_get_sheet_data` - Fetch data from specific ranges
- `tool_get_sheet_formulas` - Retrieve formulas from cells
- `tool_list_sheets` - List all sheet tabs in a spreadsheet
- `tool_get_spreadsheet_info` - Get spreadsheet metadata
- `tool_get_multiple_sheet_data` - Batch fetch from multiple ranges

### Write Operations
- `tool_update_cells` - Update specific cell ranges
- `tool_batch_update_cells` - Update multiple ranges efficiently
- `tool_append_rows` - Append new rows (ideal for receipt entries)
- `tool_add_rows` / `tool_add_columns` - Insert empty rows/columns
- `tool_clear_range` - Clear values while keeping formatting

### Sheet Management
- `tool_create_sheet` - Create new sheet tabs
- `tool_rename_sheet` - Rename existing sheets
- `tool_copy_sheet` - Copy sheets between spreadsheets
- `tool_delete_sheet` - Delete sheet tabs
- `tool_batch_update` - Advanced batch operations

## Setup

### 1. Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Cloud project with Sheets API enabled
- Service account with Sheets access

### 2. Installation

```bash
cd mcp-gsheets
uv sync
```

### 3. Configuration

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Configure your environment:

```env
SERVICE_ACCOUNT_PATH=service_account.json
SHEET_ID=your-spreadsheet-id
FASTMCP_PORT=8002
FASTMCP_HOST=0.0.0.0
LOG_LEVEL=INFO
```

### 4. Service Account Setup

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Place it as `service_account.json` in the project root
4. Share your target spreadsheet with the service account email

## Running the Server

### stdio transport (default)
```bash
uv run python main.py
```

### SSE/HTTP transport
```bash
uv run python main.py --transport sse
```

## Project Structure

```
mcp-gsheets/
├── app/
│   ├── __init__.py          # Package entry point
│   ├── server.py            # FastMCP server with tool definitions
│   ├── infra/
│   │   ├── __init__.py
│   │   └── gsheet_client.py # Google Sheets API client
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── read_ops.py      # Read operations
│   │   ├── write_ops.py     # Write operations
│   │   └── sheet_ops.py     # Sheet management
│   └── utils/
│       ├── __init__.py
│       └── logger.py        # Logging configuration
├── main.py                   # Entry point script
├── pyproject.toml
├── .env.template
└── README.md
```

## Usage Example

When used with the Klaudia orchestrator, the agent can:

1. **Extract receipt data** (via mcp-ocr)
2. **Append to spreadsheet** using `tool_append_rows`:

```python
# Example: Adding receipt entry
data = [
    ["2025-01-13", "Starbucks", "Coffee", "45000", "Food & Beverage"]
]
tool_append_rows(
    spreadsheet_id="your-sheet-id",
    sheet="Receipts",
    data=data
)
```

## Integration with Klaudia

This server runs on port **8002** and is designed to work with:
- **mcp-ocr** (port 8001) - Receipt image/PDF processing
- **Klaudia orchestrator** (port 8000) - Main FastAPI backend

## License

Part of the Klaudia AI Data Entry Agent project.