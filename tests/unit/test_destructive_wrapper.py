"""The destructive guard refuses and parks; it never half-executes.

Model-independent: the guard is what makes "no silent destruction" a
guarantee rather than a prompt the model may ignore.
"""

import json

import pytest
from langchain_core.tools import StructuredTool

from klaudia.core.supervisor.tools.context import (
    reset_approval_gate,
    set_approval_gate,
)
from klaudia.core.supervisor.tools.wrappers import with_destructive_guard

_BIG_GRID = [["Tanggal", "Toko", "Total"]] + [
    [f"2026-06-{i:02d}", "TOKO", 1000 * i] for i in range(1, 9)
]

_SCHEMA = {
    "type": "object",
    "properties": {"sheet": {"type": "string"}, "range": {"type": "string"}},
    "required": ["sheet"],
}


def _tool(name: str, executed: list) -> StructuredTool:
    async def _call(**kwargs):
        executed.append(kwargs)
        return '{"cleared": true}'

    return StructuredTool.from_function(
        coroutine=_call, name=name, description=name, args_schema=_SCHEMA
    )


def _reader(grid):
    async def _read(sheet: str):
        return grid

    return _read


class _Gate:
    def __init__(self) -> None:
        self.parked: list[tuple] = []

    async def __call__(self, tool_name, args, impact):
        self.parked.append((tool_name, args, impact))
        return f"appr-{len(self.parked)}"


@pytest.fixture
def gate():
    g = _Gate()
    token = set_approval_gate(g)
    yield g
    reset_approval_gate(token)


async def test_large_clear_is_refused_and_parked(gate):
    executed: list = []
    guarded = with_destructive_guard(
        _tool("tool_clear_range", executed), _reader(_BIG_GRID)
    )

    raw = await guarded.coroutine(sheet="Jun", range="A1:Z1000")

    assert executed == []  # nothing destroyed
    assert len(gate.parked) == 1
    payload = json.loads(raw)
    assert payload["status"] == "approval_required"
    assert payload["approval_id"] == "appr-1"
    assert payload["rows_affected"] == 9


async def test_small_clear_executes_unattended(gate):
    executed: list = []
    guarded = with_destructive_guard(
        _tool("tool_clear_range", executed), _reader(_BIG_GRID)
    )

    await guarded.coroutine(sheet="Jun", range="C2")

    assert executed == [{"sheet": "Jun", "range": "C2"}]
    assert gate.parked == []


async def test_delete_sheet_with_data_is_parked(gate):
    executed: list = []
    guarded = with_destructive_guard(
        _tool("tool_delete_sheet", executed), _reader(_BIG_GRID)
    )

    await guarded.coroutine(sheet="Jun")

    assert executed == []
    assert gate.parked[0][0] == "tool_delete_sheet"


async def test_delete_empty_sheet_executes(gate):
    executed: list = []
    guarded = with_destructive_guard(_tool("tool_delete_sheet", executed), _reader([]))

    await guarded.coroutine(sheet="Kosong")

    assert executed == [{"sheet": "Kosong"}]


async def test_non_destructive_tool_is_untouched(gate):
    executed: list = []
    guarded = with_destructive_guard(
        _tool("tool_append_rows", executed), _reader(_BIG_GRID)
    )

    await guarded.coroutine(sheet="Jun", range="A1")

    assert executed and gate.parked == []


async def test_without_gate_behavior_is_unchanged():
    """No gate installed (dev/tests/scripts) => passthrough."""
    executed: list = []
    guarded = with_destructive_guard(
        _tool("tool_clear_range", executed), _reader(_BIG_GRID)
    )

    await guarded.coroutine(sheet="Jun", range="A1:Z1000")

    assert executed == [{"sheet": "Jun", "range": "A1:Z1000"}]


async def test_unreadable_grid_still_parks_whole_sheet_delete(gate):
    """A failed grid read must not downgrade a delete to auto-approved."""
    executed: list = []
    guarded = with_destructive_guard(_tool("tool_batch_update", executed), _reader([]))

    await guarded.coroutine(sheet="Jun", requests=[{"deleteSheet": {"sheetId": 3}}])

    assert executed == []
    assert len(gate.parked) == 1
