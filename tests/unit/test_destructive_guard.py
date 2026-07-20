"""Deterministic impact assessment for destructive sheet operations.

Irreversible operations (clear range, delete sheet) are gated in CODE, not
by prompting the model to ask first: the model was observed clearing every
sheet 3/3 runs when told to "delete all sheet data". Policy: more than
MAX_UNAPPROVED_ROWS rows of data, or any whole column, requires explicit
user approval before execution.
"""

from klaudia.core.supervisor.tools.destructive import (
    MAX_UNAPPROVED_ROWS,
    assess_impact,
    parse_a1_range,
)

_GRID = [
    ["Tanggal", "Toko", "Total"],
    ["2026-06-01", "ALFAMIDI", 15000],
    ["2026-06-02", "INDOMARET", 23500],
    ["2026-06-03", "PARIS MART", 10000],
]


class TestParseA1Range:
    def test_bounded_range(self):
        assert parse_a1_range("A1:C10") == (0, 9, 0, 2)

    def test_single_cell(self):
        assert parse_a1_range("B5") == (4, 4, 1, 1)

    def test_whole_column(self):
        assert parse_a1_range("A:A") == (None, None, 0, 0)

    def test_column_span(self):
        assert parse_a1_range("A:C") == (None, None, 0, 2)

    def test_row_span(self):
        assert parse_a1_range("2:4") == (1, 3, None, None)

    def test_none_is_whole_sheet(self):
        assert parse_a1_range(None) == (None, None, None, None)

    def test_lowercase_and_whitespace(self):
        assert parse_a1_range(" a1:c10 ") == (0, 9, 0, 2)

    def test_multi_letter_column(self):
        assert parse_a1_range("AA1:AB2") == (0, 1, 26, 27)

    def test_malformed_returns_whole_sheet(self):
        # Fail safe: an unparseable range is treated as maximum impact.
        assert parse_a1_range("not-a-range") == (None, None, None, None)


class TestClearRangeImpact:
    def test_small_clear_is_auto_approved(self):
        impact = assess_impact("tool_clear_range", {"range": "A2:C3"}, _GRID)
        assert impact.rows == 2
        assert impact.full_columns == 0
        assert not impact.requires_approval

    def test_single_cell_is_auto_approved(self):
        impact = assess_impact("tool_clear_range", {"range": "C2"}, _GRID)
        assert impact.rows == 1
        assert not impact.requires_approval

    def test_whole_column_requires_approval(self):
        # One column, only 4 rows — under the row threshold, but a whole
        # column is destructive on its own.
        impact = assess_impact("tool_clear_range", {"range": "C:C"}, _GRID)
        assert impact.full_columns == 1
        assert impact.requires_approval

    def test_more_than_threshold_rows_requires_approval(self):
        grid = [["Total"]] + [[i * 1000] for i in range(1, 9)]  # 8 data rows
        impact = assess_impact("tool_clear_range", {"range": "A2:A9"}, grid)
        assert impact.rows == 8 > MAX_UNAPPROVED_ROWS
        assert impact.requires_approval

    def test_exactly_threshold_rows_is_auto_approved(self):
        grid = [["Total"]] + [[i * 1000] for i in range(1, 6)]  # 5 data rows
        impact = assess_impact("tool_clear_range", {"range": "A2:A6"}, grid)
        assert impact.rows == MAX_UNAPPROVED_ROWS
        assert not impact.requires_approval

    def test_whole_sheet_clear_requires_approval(self):
        impact = assess_impact("tool_clear_range", {"range": "A1:Z1000"}, _GRID)
        assert impact.requires_approval

    def test_empty_rows_in_range_are_not_counted(self):
        grid = [["h"], ["x"], [], [""], ["y"]]
        impact = assess_impact("tool_clear_range", {"range": "A1:A5"}, grid)
        assert impact.rows == 3  # header + x + y

    def test_clearing_empty_region_is_auto_approved(self):
        impact = assess_impact("tool_clear_range", {"range": "A50:C60"}, _GRID)
        assert impact.rows == 0
        assert not impact.requires_approval


class TestDeleteSheetImpact:
    def test_delete_sheet_with_data_requires_approval(self):
        impact = assess_impact("tool_delete_sheet", {"sheet": "Jun"}, _GRID)
        assert impact.requires_approval
        assert impact.rows == 4

    def test_delete_empty_sheet_is_auto_approved(self):
        impact = assess_impact("tool_delete_sheet", {"sheet": "Temp"}, [])
        assert not impact.requires_approval


class TestBatchUpdateImpact:
    def test_delete_sheet_request_requires_approval(self):
        impact = assess_impact(
            "tool_batch_update", {"requests": [{"deleteSheet": {"sheetId": 3}}]}, _GRID
        )
        assert impact.requires_approval

    def test_add_sheet_request_is_auto_approved(self):
        impact = assess_impact(
            "tool_batch_update",
            {"requests": [{"addSheet": {"properties": {"title": "New"}}}]},
            _GRID,
        )
        assert not impact.requires_approval


class TestSummary:
    def test_summary_names_sheet_and_scope(self):
        impact = assess_impact(
            "tool_clear_range", {"sheet": "Jun", "range": "A1:Z1000"}, _GRID
        )
        assert "Jun" in impact.summary
        assert str(impact.rows) in impact.summary

    def test_delete_sheet_summary(self):
        impact = assess_impact("tool_delete_sheet", {"sheet": "Jun"}, _GRID)
        assert "Jun" in impact.summary
