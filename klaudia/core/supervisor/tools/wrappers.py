import logging

from langchain_core.tools import BaseTool

from klaudia.core.supervisor.tools.coordinates import annotate_sheet_output
from klaudia.interfaces.tool_registry import MCPToolRegistry

logger = logging.getLogger(__name__)

# Read tools whose tabular output must be coordinate-annotated so the model
# never has to compute write targets (e.g. "B5") by counting rows itself.
_COORD_READ_TOOLS = {"tool_get_sheet_data", "tool_get_multiple_sheet_data"}


def _with_coordinates(tool: BaseTool) -> BaseTool:
    """Return a copy of a read tool whose output is row/column annotated.

    Other tools pass through untouched. Uses model_copy to swap only the
    coroutine, preserving the original name/description/args_schema exactly.
    """
    if tool.name not in _COORD_READ_TOOLS:
        return tool
    if tool.coroutine is None:
        return tool
    src = tool  # original registry tool; its .coroutine may be re-patched later

    async def _call(**kwargs: object) -> str:
        # Resolve src.coroutine at CALL time, not build time, so anything that
        # re-wraps the original tool's coroutine after the graph is built (the
        # E2E MCPSpy, tracing) still observes the invocation. Capturing it in a
        # closure here would make those wrappers invisible.
        return annotate_sheet_output(await src.coroutine(**kwargs))

    return tool.model_copy(update={"coroutine": _call})


def get_sql_tools(registry: MCPToolRegistry) -> list[BaseTool]:
    """Get MCP-SQLite tools filtered for SQL Agent use.

    tool_list_documents is intentionally excluded: the SESSION FILES section
    of the system prompt already contains file IDs for the current session,
    so the agent should call tool_get_extraction directly. For cases where
    the user asks to browse all uploaded files, tool_get_session_files is
    strictly more informative (returns nested page + extraction status).
    """
    allowed = {
        "tool_get_document",
        "tool_get_session_files",  # replaces tool_list_documents; returns pages too
        "tool_list_pages",
        "tool_get_page",
        "tool_get_extraction",
    }
    return [t for t in registry.tools if t.name in allowed]


def get_data_entry_tools(registry: MCPToolRegistry) -> list[BaseTool]:
    """Get all MCP-GSheets tools for Data Entry Team."""
    return registry.tools


def get_read_tools(registry: MCPToolRegistry) -> list[BaseTool]:
    """Get read-only GSheets tools for Read Agent."""
    allowed = {
        "tool_get_sheet_data",
        "tool_get_sheet_formulas",
        "tool_list_sheets",
        "tool_get_spreadsheet_info",
        "tool_get_multiple_sheet_data",
    }
    return [_with_coordinates(t) for t in registry.tools if t.name in allowed]


def get_sheet_tools(registry: MCPToolRegistry) -> list[BaseTool]:
    """Get sheet management tools for Sheet Agent.

    STRUCTURE ONLY — deliberately excludes tool_batch_update. batch_update is a
    low-level spreadsheets.batchUpdate that can also write cell VALUES, and the
    model would use it to populate headers/data (overstepping write_agent's job
    and making the parked write step a redundant no-op). Cell population is
    write_agent's responsibility: sheet_agent only creates/renames/copies/deletes
    the tab, then stops. Structural CRUD is fully covered by the four tools below.
    """
    allowed = {
        "tool_create_sheet",
        "tool_rename_sheet",
        "tool_copy_sheet",
        "tool_delete_sheet",
    }
    return [t for t in registry.tools if t.name in allowed]


def get_write_tools(registry: MCPToolRegistry) -> list[BaseTool]:
    """Get tools for the Write Agent.

    Includes a small set of read tools because compound write flows in the
    WRITE_AGENT_PROMPT (Pattern B dedup, Pattern D add-column, sheet-name
    resolution) explicitly require reading before writing. Without these the
    agent emits [CLARIFY] instead of executing — see incident 2026-04-25
    where the agent asked the user for a column letter it could have read.
    """
    allowed = {
        # Read primitives needed to ground writes in actual sheet state.
        "tool_get_sheet_data",
        "tool_get_multiple_sheet_data",
        "tool_list_sheets",
        # Write primitives.
        "tool_update_cells",
        "tool_batch_update_cells",
        "tool_append_rows",
        "tool_add_rows",
        "tool_add_columns",
        "tool_clear_range",
    }
    return [_with_coordinates(t) for t in registry.tools if t.name in allowed]
