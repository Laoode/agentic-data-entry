"""SheetGuard repairs the FULL baseline, not just the guarded tabs.

The bench is the release gate, so fixture corruption silently invalidates
every case after it. A destructive case can empty any tab (H03 asked to
"delete all sheet data" cleared all seven); restoring only Jun and
Rangkuman Total left the rest blank for the remainder of the suite.

Driven by an in-memory fake of the sheets tool surface, so this is
deterministic and needs no Postgres or LLM.
"""

import json

import pytest

from tests.e2e.sheet_guard import SheetGuard

_BASELINE = {
    "Rangkuman Total": [["Bulan", "Total"], ["Juni", "2.164.500"]],
    "Jun": [["Tanggal", "Toko"], ["2026-06-01", "ALFAMIDI"]],
    "Mei": [["Tanggal", "Toko"], ["2026-05-02", "INDOMARET"]],
}


class FakeTool:
    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    async def ainvoke(self, args):
        return self._fn(**args)


class FakeSheets:
    """Minimal in-memory stand-in for the sheets MCP tool surface."""

    def __init__(self, state):
        self.state = {k: [list(r) for r in v] for k, v in state.items()}
        self.tools = [
            FakeTool("tool_list_sheets", self._list),
            FakeTool("tool_get_sheet_data", self._get),
            FakeTool("tool_get_multiple_sheet_data", self._multi),
            FakeTool("tool_clear_range", self._clear),
            FakeTool("tool_update_cells", self._update),
            FakeTool("tool_create_sheet", self._create),
            FakeTool("tool_delete_sheet", self._delete),
        ]

    def _list(self, **_):
        return "\n".join(
            json.dumps({"title": t, "sheetId": i, "index": i})
            for i, t in enumerate(self.state)
        )

    def _get(self, sheet, **_):
        return json.dumps({"values": self.state.get(sheet, [])})

    def _multi(self, queries, **_):
        return "\n".join(
            json.dumps({**q, "data": self.state.get(q["sheet"], [])}) for q in queries
        )

    def _clear(self, sheet, **_):
        self.state[sheet] = []
        return "{}"

    def _update(self, sheet, data, **_):
        self.state[sheet] = [list(r) for r in data]
        return "{}"

    def _create(self, title, **_):
        self.state.setdefault(title, [])
        return "{}"

    def _delete(self, sheet, **_):
        self.state.pop(sheet, None)
        return "{}"


@pytest.fixture
def guard_and_sheets():
    sheets = FakeSheets(_BASELINE)
    guard = SheetGuard(sheets)
    guard._names = list(_BASELINE)
    guard._data = {k: [list(r) for r in v] for k, v in _BASELINE.items()}
    return guard, sheets


async def test_repairs_wiped_non_guarded_sheet(guard_and_sheets):
    guard, sheets = guard_and_sheets
    sheets.state["Mei"] = []  # a destructive case emptied it

    await guard.restore()

    assert sheets.state["Mei"] == _BASELINE["Mei"]


async def test_repairs_every_sheet_after_total_wipe(guard_and_sheets):
    guard, sheets = guard_and_sheets
    for name in list(sheets.state):
        sheets.state[name] = []

    await guard.restore()

    for name, rows in _BASELINE.items():
        assert sheets.state[name] == rows


async def test_recreates_deleted_sheet(guard_and_sheets):
    guard, sheets = guard_and_sheets
    del sheets.state["Mei"]

    await guard.restore()

    assert sheets.state["Mei"] == _BASELINE["Mei"]


async def test_drops_non_baseline_tabs(guard_and_sheets):
    guard, sheets = guard_and_sheets
    sheets.state["QA E2E Copy"] = [["junk"]]

    await guard.restore()

    assert "QA E2E Copy" not in sheets.state


async def test_undrifted_sheets_are_not_rewritten(guard_and_sheets):
    """No drift must not cost a write per tab on every mutating case."""
    guard, sheets = guard_and_sheets
    writes = []
    original = sheets._update

    def counting_update(sheet, data, **kw):
        writes.append(sheet)
        return original(sheet, data, **kw)

    sheets.tools[4] = FakeTool("tool_update_cells", counting_update)

    await guard.restore()

    assert writes == []


async def test_numeric_formatting_is_not_treated_as_drift(guard_and_sheets):
    """2.164.500 written, 2164500 read back is the same value."""
    guard, sheets = guard_and_sheets
    sheets.state["Rangkuman Total"] = [["Bulan", "Total"], ["Juni", 2164500]]
    writes = []
    original = sheets._update

    def counting_update(sheet, data, **kw):
        writes.append(sheet)
        return original(sheet, data, **kw)

    sheets.tools[4] = FakeTool("tool_update_cells", counting_update)

    await guard.restore()

    assert writes == []
