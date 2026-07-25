"""LedgerSeeder writes grids through the sheets tool surface, hermetically.

Uses an in-memory fake of the MCP sheet tools (no Postgres, no LLM). Also checks
that a spreadsheet_id, when set, is threaded onto every tool call - the tenancy
scoping the ledger backend relies on.
"""

import json

from tests.e2e.ledger_seeder import LedgerSeeder, col_letter, titles


class FakeTool:
    def __init__(self, name, fn):
        self.name = name
        self._fn = fn

    async def ainvoke(self, args):
        return self._fn(args)


class FakeSheets:
    """Minimal stand-in for the sheets MCP tool surface; records every call."""

    def __init__(self, state=None):
        self.state = {k: [list(r) for r in v] for k, v in (state or {}).items()}
        self.calls: list[tuple[str, dict]] = []
        self.tools = [
            FakeTool("tool_list_sheets", self._list),
            FakeTool("tool_clear_range", self._clear),
            FakeTool("tool_update_cells", self._update),
            FakeTool("tool_create_sheet", self._create),
        ]

    def _list(self, args):
        self.calls.append(("tool_list_sheets", args))
        return "\n".join(
            json.dumps({"title": t, "sheetId": i, "index": i})
            for i, t in enumerate(self.state)
        )

    def _clear(self, args):
        self.calls.append(("tool_clear_range", args))
        self.state[args["sheet"]] = []
        return "{}"

    def _update(self, args):
        self.calls.append(("tool_update_cells", args))
        self.state[args["sheet"]] = [list(r) for r in args["data"]]
        return "{}"

    def _create(self, args):
        self.calls.append(("tool_create_sheet", args))
        self.state.setdefault(args["title"], [])
        return "{}"


def test_col_letter():
    assert col_letter(0) == "A"
    assert col_letter(3) == "D"
    assert col_letter(26) == "AA"


def test_titles_parses_concatenated_objects():
    raw = '{"title": "Jun"}\n{"title": "Mei"}'
    assert titles(raw) == ["Jun", "Mei"]


async def test_seed_grids_creates_and_writes_new_tabs():
    sheets = FakeSheets()
    seeder = LedgerSeeder(sheets)

    grids = {"Pengeluaran Juni": [["Tanggal", "Jumlah"], ["2026-06-01", 152000]]}
    await seeder.seed_grids(grids)

    assert sheets.state["Pengeluaran Juni"] == [
        ["Tanggal", "Jumlah"],
        ["2026-06-01", 152000],
    ]
    called = [name for name, _ in sheets.calls]
    assert "tool_create_sheet" in called
    assert "tool_update_cells" in called


async def test_write_grid_clears_then_writes_when_not_creating():
    sheets = FakeSheets({"Jun": [["old"]]})
    seeder = LedgerSeeder(sheets)

    await seeder.write_grid("Jun", [["Tanggal", "Toko"], ["2026-06-01", "X"]], create=False)

    assert sheets.state["Jun"] == [["Tanggal", "Toko"], ["2026-06-01", "X"]]
    called = [name for name, _ in sheets.calls]
    assert "tool_clear_range" in called
    assert "tool_create_sheet" not in called


async def test_update_range_matches_grid_dimensions():
    sheets = FakeSheets()
    seeder = LedgerSeeder(sheets)

    await seeder.write_grid("S", [["a", "b", "c"], ["1", "2", "3"]], create=True)

    update = next(a for n, a in sheets.calls if n == "tool_update_cells")
    assert update["range"] == "A1:C2"


async def test_spreadsheet_id_is_threaded_onto_every_call():
    sheets = FakeSheets()
    seeder = LedgerSeeder(sheets, spreadsheet_id="ws-123")

    await seeder.seed_grids({"S": [["h"], ["v"]]})

    assert sheets.calls, "expected tool calls"
    assert all(args.get("spreadsheet_id") == "ws-123" for _, args in sheets.calls)


async def test_restore_to_baseline_drops_stray_and_repairs():
    baseline = {"Kas Harian": [["Tanggal", "Jumlah"], ["2026-06-01", 100000]]}
    # A mutating case's aftermath: an appended row, plus a stray sheet the agent
    # created, plus the source sheet corrupted.
    sheets = FakeSheets(
        {
            "Kas Harian": [["Tanggal", "Jumlah"], ["2026-06-01", 100000], ["x", 999]],
            "Rekap Baru": [["junk"]],
        }
    )
    sheets.tools.append(FakeTool("tool_delete_sheet", _make_delete(sheets)))
    seeder = LedgerSeeder(sheets)

    await seeder.restore_to_baseline(baseline)

    assert "Rekap Baru" not in sheets.state  # stray tab dropped
    assert sheets.state["Kas Harian"] == baseline["Kas Harian"]  # repaired exactly


def _make_delete(sheets):
    def _delete(args):
        sheets.calls.append(("tool_delete_sheet", args))
        sheets.state.pop(args["sheet"], None)
        return "{}"

    return _delete
