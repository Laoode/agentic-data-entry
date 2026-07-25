"""docs/TABLE.md is a fixture, so its parse is pinned like any other ground truth.

The file is documentation and seed data at once: `sheet_guard.py` parses it and
writes the result into the Tier 1 test user's spreadsheet. That means a prose
edit can silently change what the behavior suite runs against — a heading that
happens to start with `Name:` would invent a tab, and a stray blank line would
truncate one.

These tests are hermetic (no DB, no LLM) and fail on the file, not on a live run.
"""

from tests.e2e.sheet_guard import load_table_md

# The Tier 1 spreadsheet: seven tabs, in this order, with these shapes. Row
# counts include the header row.
EXPECTED_TABS = ["Rangkuman Total", "Jun", "Mei", "Apr", "Mar", "Feb", "Jan"]
EXPECTED_SHAPE = {
    "Rangkuman Total": (7, 2),
    "Jun": (36, 7),
    "Mei": (11, 7),
    "Apr": (11, 7),
    "Mar": (11, 7),
    "Feb": (11, 7),
    "Jan": (11, 7),
}
MONTH_HEADER = [
    "Tanggal",
    "Toko",
    "Item",
    "Jumlah",
    "Metode Pembayaran",
    "Satuan Harga (IDR)",
    "Total (IDR)",
]


def test_tab_names_and_order_are_pinned():
    names, _ = load_table_md()
    assert names == EXPECTED_TABS


def test_every_tab_keeps_its_shape():
    _, data = load_table_md()
    actual = {name: (len(rows), len(rows[0])) for name, rows in data.items()}
    assert actual == EXPECTED_SHAPE


def test_month_tabs_share_one_header():
    """A month tab that drifts from the others breaks the cross-sheet cases."""
    _, data = load_table_md()
    for name in ("Jun", "Mei", "Apr", "Mar", "Feb", "Jan"):
        assert data[name][0] == MONTH_HEADER, name


def test_summary_tab_lists_the_six_months():
    _, data = load_table_md()
    rows = data["Rangkuman Total"]
    assert rows[0] == ["Bulan", "Total Pembelian (Rp)"]
    months = [row[0] for row in rows[1:]]
    assert months == ["Januari", "Februari", "Maret", "April", "Mei", "Juni"]


def test_prose_in_the_file_never_becomes_a_tab():
    """The documentation header must stay invisible to the parser."""
    names, _ = load_table_md()
    assert len(names) == len(set(names)), "a prose line created a duplicate tab"
    for name in names:
        assert name in EXPECTED_TABS, f"prose leaked into the fixture as {name!r}"


def test_no_row_is_ragged():
    """Short rows write misaligned cells and score later cases against garbage."""
    _, data = load_table_md()
    for name, rows in data.items():
        width = len(rows[0])
        ragged = [i for i, row in enumerate(rows) if len(row) != width]
        assert not ragged, f"{name}: rows {ragged} do not match the header width"
