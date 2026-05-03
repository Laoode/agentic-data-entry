import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from klaudia.interfaces.tool_registry import MCPToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sheets", tags=["sheets"])


def _get_tool(registry: MCPToolRegistry, name: str):
    tool = next((t for t in registry.tools if t.name == name), None)
    if tool is None:
        raise HTTPException(status_code=503, detail=f"MCP tool '{name}' unavailable")
    return tool


async def _invoke(tool, args: dict[str, Any]) -> Any:
    """Call a LangChain StructuredTool and parse its JSON string response."""
    # Strip None values — MCP tools rely on their own defaults for optional params.
    clean_args = {k: v for k, v in args.items() if v is not None}
    raw: str = await tool.ainvoke(clean_args)
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Tool returned a plain string (unlikely for read ops, but be safe).
        return {"raw": raw}


@router.get("/info")
async def get_spreadsheet_info(request: Request) -> JSONResponse:
    """
    Return spreadsheet title and all sheet tab names.
    Uses the server's default SHEET_ID — no params required.
    """
    registry: MCPToolRegistry = request.app.state.container.mcp_gsheets
    tool = _get_tool(registry, "tool_get_spreadsheet_info")
    try:
        data = await _invoke(tool, {})
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"sheets/info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data")
async def get_sheet_data(
    request: Request,
    sheet: str = Query(..., description="Sheet tab name, e.g. 'Sheet1'"),
    range: Optional[str] = Query(None, description="A1 notation range, e.g. 'A1:F50'"),
) -> JSONResponse:
    """
    Return cell values from a sheet tab.
    Uses the server's default SHEET_ID — only sheet name (and optional range) required.
    """
    registry: MCPToolRegistry = request.app.state.container.mcp_gsheets
    tool = _get_tool(registry, "tool_get_sheet_data")
    try:
        data = await _invoke(tool, {"sheet": sheet, "range": range})
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"sheets/data failed (sheet={sheet!r}): {e}")
        raise HTTPException(status_code=500, detail=str(e))