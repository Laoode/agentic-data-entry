"""Coordinate-annotation unit tests.

Regression guard for the write-corruption bug: the single-sheet
tool_get_sheet_data output uses the "values" key (not "data"), so the helper
must annotate BOTH shapes. When it silently no-ops on the single-sheet shape,
the write agent counts rows by hand and writes one row off — corrupting a
neighbouring record. These tests pin the real Google Sheets row numbers.
"""

import json

from klaudia.core.supervisor.tools.coordinates import (
    annotate_sheet_output,
    col_letter,
)

HEADER = [
    "Tanggal",
    "Toko",
    "Item",
    "Jumlah",
    "Metode Pembayaran",
    "Satuan Harga (IDR)",
    "Total (IDR)",
]


def _rows_with_tail(tail_labels):
    """Header + 31 filler rows + tail rows → tail starts at sheet row 33."""
    rows = [HEADER]
    for i in range(31):
        rows.append(
            ["2026-06-19", "PARIS MART", f"ITEM{i}", "1", "Kartu Debit", "1000", "1000"]
        )
    for name in tail_labels:
        rows.append(["2026-06-27", "sy_beautyskin", name, "1", "", "150000", "150000"])
    return rows


def test_col_letter():
    assert col_letter(0) == "A"
    assert col_letter(4) == "E"
    assert col_letter(25) == "Z"
    assert col_letter(26) == "AA"


def test_single_sheet_values_shape_is_annotated():
    """tool_get_sheet_data uses {'range', 'values'} — must NOT fall through raw."""
    payload = json.dumps(
        {"spreadsheetId": "x", "range": "Jun", "values": [HEADER, HEADER]}
    )
    out = annotate_sheet_output(payload)
    assert out.startswith("[Sheet: Jun]")
    assert "R1:" in out


def test_multi_sheet_data_shape_still_annotated():
    """tool_get_multiple_sheet_data uses the 'data' key — unchanged behavior."""
    payload = json.dumps({"sheet": "Mei", "data": [HEADER, HEADER]})
    out = annotate_sheet_output(payload)
    assert out.startswith("[Sheet: Mei]")


def test_header_is_row_1_first_data_row_is_row_2():
    payload = json.dumps(
        {"range": "Jun", "values": [HEADER, ["2026-06-19", "PARIS MART"]]}
    )
    lines = annotate_sheet_output(payload).splitlines()
    assert any(ln.startswith("R1: Tanggal") for ln in lines)
    assert any(ln.startswith("R2: 2026-06-19") for ln in lines)


def test_off_by_one_regression_sy_beautyskin_is_rows_33_to_36():
    """The exact case that corrupted the sheet: the four sy_beautyskin rows must
    annotate as R33-R36 (the write agent had used 34-37)."""
    rows = _rows_with_tail(
        ["Ms Glow acne", "serum lifting ms glow", "eye treatment serum", "waiteu"]
    )
    payload = json.dumps({"range": "Jun", "values": rows})
    out = annotate_sheet_output(payload)
    assert "R33: 2026-06-27 | sy_beautyskin | Ms Glow acne" in out
    assert "R36: 2026-06-27 | sy_beautyskin | waiteu" in out
    assert "R37:" not in out  # no phantom trailing row


def test_fail_soft_on_unparseable_input():
    assert annotate_sheet_output("not json") == "not json"
    assert annotate_sheet_output("") == ""


def test_no_data_returns_raw():
    """Object with neither 'data' nor 'values' is returned unchanged."""
    payload = json.dumps({"range": "Jun", "spreadsheetId": "x"})
    assert annotate_sheet_output(payload) == payload
