"""Checked operations keep workbook selection outside model-controlled input."""

import json

from langchain_core.tools import StructuredTool

from klaudia.core.supervisor.tools.context import (
    reset_active_spreadsheet,
    set_active_spreadsheet,
)
from klaudia.core.supervisor.tools.wrappers import with_tenant_scope


async def test_checked_append_overrides_foreign_workbook():
    """A model cannot change the bound workbook through the new tool shape."""
    calls = []

    async def capture(**kwargs):
        """Record arguments delivered after scope injection."""
        calls.append(kwargs)
        return json.dumps({"status": "committed"})

    tool = StructuredTool.from_function(
        coroutine=capture,
        name="tool_append_rows_checked",
        description="Checked append",
        args_schema={
            "type": "object",
            "properties": {
                "operation": {"type": "object"},
                "spreadsheet_id": {"type": "string"},
            },
            "required": ["operation"],
        },
    )
    scoped = with_tenant_scope(tool)
    assert "spreadsheet_id" not in scoped.args_schema["properties"]
    operation = {
        "sheet_id": 7,
        "expected_revision": 1,
        "idempotency_key": "request",
        "rows": [[10]],
    }
    token = set_active_spreadsheet("authorised-workbook")
    try:
        await scoped.coroutine(operation=operation, spreadsheet_id="foreign-workbook")
    finally:
        reset_active_spreadsheet(token)
    assert calls == [{"operation": operation, "spreadsheet_id": "authorised-workbook"}]
