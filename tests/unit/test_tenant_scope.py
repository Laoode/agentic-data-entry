"""Tenant-scope injection for sheets tools.

The active spreadsheet is request-scoped (ContextVar) and forced into
every sheets tool call at invocation time, while the spreadsheet-selection
parameters are stripped from the LLM-visible schema. The model can never
name, guess, or be prompt-injected into another tenant's spreadsheet.
"""

from langchain_core.tools import StructuredTool

from klaudia.core.supervisor.tools.context import (
    get_active_spreadsheet,
    reset_active_spreadsheet,
    set_active_spreadsheet,
)
from klaudia.core.supervisor.tools.wrappers import with_tenant_scope

_SHEET_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "sheet": {"type": "string"},
        "spreadsheet_id": {"type": "string"},
        "range": {"type": "string"},
    },
    "required": ["sheet"],
}

_COPY_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "src_sheet": {"type": "string"},
        "dst_sheet": {"type": "string"},
        "src_spreadsheet": {"type": "string"},
        "dst_spreadsheet": {"type": "string"},
    },
    "required": ["src_sheet", "dst_sheet"],
}


def _make_tool(name: str, schema: dict, seen: list[dict]) -> StructuredTool:
    async def _call(**kwargs):
        seen.append(kwargs)
        return "ok"

    return StructuredTool.from_function(
        coroutine=_call, name=name, description=name, args_schema=schema
    )


def test_contextvar_roundtrip():
    assert get_active_spreadsheet() is None
    token = set_active_spreadsheet("ss-abc")
    assert get_active_spreadsheet() == "ss-abc"
    reset_active_spreadsheet(token)
    assert get_active_spreadsheet() is None


def test_schema_strips_spreadsheet_params():
    tool = _make_tool("tool_get_sheet_data", _SHEET_TOOL_SCHEMA, [])
    scoped = with_tenant_scope(tool)

    props = scoped.args_schema["properties"]
    assert "spreadsheet_id" not in props
    assert set(props) == {"sheet", "range"}
    # Original tool schema is untouched (no mutation).
    assert "spreadsheet_id" in tool.args_schema["properties"]


def test_schema_strips_copy_params():
    tool = _make_tool("tool_copy_sheet", _COPY_TOOL_SCHEMA, [])
    scoped = with_tenant_scope(tool)

    props = scoped.args_schema["properties"]
    assert "src_spreadsheet" not in props and "dst_spreadsheet" not in props
    assert set(props) == {"src_sheet", "dst_sheet"}


async def test_injects_active_spreadsheet():
    seen: list[dict] = []
    scoped = with_tenant_scope(
        _make_tool("tool_get_sheet_data", _SHEET_TOOL_SCHEMA, seen)
    )

    token = set_active_spreadsheet("ss-abc")
    try:
        await scoped.coroutine(sheet="Jul")
    finally:
        reset_active_spreadsheet(token)

    assert seen == [{"sheet": "Jul", "spreadsheet_id": "ss-abc"}]


async def test_injection_overrides_model_supplied_value():
    seen: list[dict] = []
    scoped = with_tenant_scope(
        _make_tool("tool_get_sheet_data", _SHEET_TOOL_SCHEMA, seen)
    )

    token = set_active_spreadsheet("ss-abc")
    try:
        # Even if a hostile prompt smuggles a foreign id through, it is replaced.
        await scoped.coroutine(sheet="Jul", spreadsheet_id="ss-other")
    finally:
        reset_active_spreadsheet(token)

    assert seen[0]["spreadsheet_id"] == "ss-abc"


async def test_injects_copy_sheet_src_and_dst():
    seen: list[dict] = []
    scoped = with_tenant_scope(_make_tool("tool_copy_sheet", _COPY_TOOL_SCHEMA, seen))

    token = set_active_spreadsheet("ss-abc")
    try:
        await scoped.coroutine(src_sheet="Jun", dst_sheet="Jun-Backup")
    finally:
        reset_active_spreadsheet(token)

    assert seen[0]["src_spreadsheet"] == "ss-abc"
    assert seen[0]["dst_spreadsheet"] == "ss-abc"


def test_schema_strips_nested_query_params():
    schema = {
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "sheet": {"type": "string"},
                        "spreadsheet_id": {"type": "string"},
                        "range": {"type": "string"},
                    },
                },
            }
        },
        "required": ["queries"],
    }
    scoped = with_tenant_scope(_make_tool("tool_get_multiple_sheet_data", schema, []))

    item_props = scoped.args_schema["properties"]["queries"]["items"]["properties"]
    assert "spreadsheet_id" not in item_props
    assert set(item_props) == {"sheet", "range"}


async def test_rewrites_multi_sheet_queries():
    schema = {
        "type": "object",
        "properties": {"queries": {"type": "array", "items": {"type": "object"}}},
        "required": ["queries"],
    }
    seen: list[dict] = []
    scoped = with_tenant_scope(_make_tool("tool_get_multiple_sheet_data", schema, seen))
    queries = [{"sheet": "A"}, {"sheet": "B", "spreadsheet_id": "ss-other"}]

    token = set_active_spreadsheet("ss-abc")
    try:
        await scoped.coroutine(queries=queries)
    finally:
        reset_active_spreadsheet(token)

    assert all(q["spreadsheet_id"] == "ss-abc" for q in seen[0]["queries"])
    # Caller's list was not mutated in place.
    assert "spreadsheet_id" not in queries[0]
    assert queries[1]["spreadsheet_id"] == "ss-other"


async def test_no_scope_passes_through_unchanged():
    seen: list[dict] = []
    scoped = with_tenant_scope(
        _make_tool("tool_get_sheet_data", _SHEET_TOOL_SCHEMA, seen)
    )

    await scoped.coroutine(sheet="Jul")

    assert seen == [{"sheet": "Jul"}]


async def test_late_binds_source_coroutine():
    """Wrappers applied after scoping (e2e spy, tracing) must stay visible."""
    seen: list[dict] = []
    tool = _make_tool("tool_get_sheet_data", _SHEET_TOOL_SCHEMA, seen)
    scoped = with_tenant_scope(tool)

    patched: list[str] = []
    original = tool.coroutine

    async def spy(**kwargs):
        patched.append("spy")
        return await original(**kwargs)

    tool.coroutine = spy
    await scoped.coroutine(sheet="Jul")

    assert patched == ["spy"]
