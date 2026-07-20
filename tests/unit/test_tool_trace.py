"""Per-request tool-call trace: production's equivalent of the e2e spy.

The orchestrator starts a trace before invoking the supervisor; every
worker tool call records (name, args, raw output) into it. The numeric
verifier grounds reply claims in these outputs. No trace started = no
recording (zero overhead outside chat turns).
"""

from langchain_core.tools import StructuredTool

from klaudia.core.supervisor.tools.context import (
    record_tool_call,
    reset_tool_trace,
    start_tool_trace,
)
from klaudia.core.supervisor.tools.wrappers import with_recording

_SCHEMA = {
    "type": "object",
    "properties": {"sheet": {"type": "string"}},
    "required": ["sheet"],
}


def _make_tool(name: str, output: str) -> StructuredTool:
    async def _call(**kwargs):
        return output

    return StructuredTool.from_function(
        coroutine=_call, name=name, description=name, args_schema=_SCHEMA
    )


async def test_records_calls_into_active_trace():
    tool = with_recording(_make_tool("tool_get_sheet_data", '{"values": [[1]]}'))

    trace, token = start_tool_trace()
    try:
        await tool.coroutine(sheet="Jun")
    finally:
        reset_tool_trace(token)

    assert trace == [("tool_get_sheet_data", {"sheet": "Jun"}, '{"values": [[1]]}')]


async def test_no_trace_means_no_recording_and_passthrough():
    tool = with_recording(_make_tool("tool_get_sheet_data", "ok"))
    assert await tool.coroutine(sheet="Jun") == "ok"


async def test_trace_is_isolated_after_reset():
    tool = with_recording(_make_tool("tool_get_sheet_data", "ok"))
    trace, token = start_tool_trace()
    reset_tool_trace(token)

    await tool.coroutine(sheet="Jun")

    assert trace == []


def test_record_tool_call_without_trace_is_noop():
    record_tool_call("tool_x", {}, "out")  # must not raise


async def test_late_binds_source_coroutine():
    """Spy/tracing re-wraps applied after composition must stay visible."""
    tool = _make_tool("tool_get_sheet_data", "raw")
    recorded = with_recording(tool)

    calls: list[str] = []
    original = tool.coroutine

    async def spy(**kwargs):
        calls.append("spy")
        return await original(**kwargs)

    tool.coroutine = spy
    trace, token = start_tool_trace()
    try:
        await recorded.coroutine(sheet="Jun")
    finally:
        reset_tool_trace(token)

    assert calls == ["spy"]
    assert trace[0][2] == "raw"
