"""Unit tests for the deterministic cross-session continuity block.

Pure formatting, no DB: given recent-activity rows, produce the compact
"where you left off" prompt slice. The anti-confabulation behavior (explicit
"no record" when empty) is the finance-critical property here.
"""

from klaudia.core.supervisor.tools.context import build_continuity_context

_TWO_SHEETS = [
    {
        "title": "Jun",
        "updated_at": "2026-07-20T10:00:00+00:00",
        "rows": 42,
        "last_row": ["2026-07-20", "Indomaret", "152000"],
    },
    {
        "title": "Mei",
        "updated_at": "2026-07-18T09:00:00+00:00",
        "rows": 30,
        "last_row": ["2026-07-18", "Alfamart", "50000"],
    },
]


def test_empty_activity_states_no_record_explicitly():
    # Anti-confabulation: the model must be told there is nothing, not left blank.
    assert "no recent" in build_continuity_context([]).lower()


def test_none_activity_states_no_record():
    assert "no recent" in build_continuity_context(None).lower()


def test_lists_sheets_most_recent_first_with_dates():
    out = build_continuity_context(_TWO_SHEETS)
    assert "Jun" in out and "Mei" in out
    assert "2026-07-20" in out
    assert out.index("Jun") < out.index("Mei")


def test_only_most_recent_sheet_gets_last_row_preview():
    out = build_continuity_context(_TWO_SHEETS)
    assert "Indomaret" in out  # top sheet preview present
    assert "Alfamart" not in out  # second sheet: no preview, keeps the block small


def test_row_preview_is_truncated_to_a_few_cells():
    long_row = [f"cell{i}" for i in range(20)]
    activity = [
        {
            "title": "Big",
            "updated_at": "2026-07-20T10:00:00+00:00",
            "rows": 1,
            "last_row": long_row,
        }
    ]
    out = build_continuity_context(activity)
    assert "cell0" in out
    assert "cell19" not in out


def test_date_only_no_raw_timestamp_leak():
    out = build_continuity_context(_TWO_SHEETS)
    # Only the date is shown, not the internal ISO time component.
    assert "T10:00:00" not in out
