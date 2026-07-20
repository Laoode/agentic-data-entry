"""Deterministic gating of irreversible sheet operations.

Sheet deletions and range clears cannot be undone. Asking the model to
confirm first does not work: told to "delete all sheet data", the agent
cleared every sheet on 3 of 3 runs despite the CLARIFY instruction. So the
decision is made in code here, from the actual grid contents, and the
tool physically refuses to execute until the user approves.

Policy: an operation needs approval when it destroys more than
MAX_UNAPPROVED_ROWS rows of data, or any whole column, or a sheet that
still holds data. Everything smaller (a cell fix, a few rows) runs
unattended so ordinary corrections stay one-shot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# More than this many data rows in one destructive call needs approval.
MAX_UNAPPROVED_ROWS = 5

DESTRUCTIVE_TOOLS = ("tool_clear_range", "tool_delete_sheet", "tool_batch_update")

_A1_CELL = re.compile(r"^([A-Z]*)(\d*)$")


@dataclass(frozen=True)
class ImpactAssessment:
    """What a destructive call would actually destroy."""

    rows: int
    full_columns: int
    requires_approval: bool
    summary: str


def _col_index(letters: str) -> int | None:
    if not letters:
        return None
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1


def parse_a1_range(
    notation: str | None,
) -> tuple[int | None, int | None, int | None, int | None]:
    """Parse A1 notation into 0-based (start_row, end_row, start_col, end_col).

    None on any bound means unbounded in that direction: "A:A" is a whole
    column, "2:4" whole rows, None the whole sheet. An unparseable range
    also yields the whole sheet, so malformed input fails toward MORE
    caution rather than less.
    """
    whole = (None, None, None, None)
    if not notation:
        return whole
    text = notation.strip().upper()
    if "!" in text:
        text = text.rsplit("!", 1)[1]
    start_text, _, end_text = text.partition(":")
    start = _A1_CELL.match(start_text)
    if start is None:
        return whole
    end = _A1_CELL.match(end_text) if end_text else start
    if end is None:
        return whole

    start_col = _col_index(start.group(1))
    end_col = _col_index(end.group(1))
    start_row = int(start.group(2)) - 1 if start.group(2) else None
    end_row = int(end.group(2)) - 1 if end.group(2) else None
    if start_col is None or end_col is None:
        start_col = end_col = None
    if start_row is None or end_row is None:
        start_row = end_row = None
    return start_row, end_row, start_col, end_col


def _has_content(cell: Any) -> bool:
    return cell is not None and str(cell).strip() != ""


def _row_indices_with_data(grid: list[list[Any]]) -> set[int]:
    return {i for i, row in enumerate(grid) if any(_has_content(c) for c in row)}


def _assess_range(grid: list[list[Any]], notation: str | None) -> tuple[int, int]:
    """Return (data rows affected, whole columns destroyed) for a range."""
    start_row, end_row, start_col, end_col = parse_a1_range(notation)
    row_lo = 0 if start_row is None else start_row
    row_hi = len(grid) - 1 if end_row is None else end_row
    col_lo = 0 if start_col is None else start_col

    rows = 0
    for index in range(row_lo, min(row_hi, len(grid) - 1) + 1):
        row = grid[index]
        col_hi = len(row) - 1 if end_col is None else end_col
        if any(
            _has_content(row[c]) for c in range(col_lo, min(col_hi, len(row) - 1) + 1)
        ):
            rows += 1

    # A column is "whole" when the range covers every row that holds data
    # in it — clearing A2:A9 of a 9-row sheet destroys that column too.
    data_rows = _row_indices_with_data(grid)
    width = max((len(r) for r in grid), default=0)
    col_hi_all = width - 1 if end_col is None else end_col
    full_columns = 0
    for col in range(col_lo, min(col_hi_all, width - 1) + 1):
        occupied = {
            i for i in data_rows if col < len(grid[i]) and _has_content(grid[i][col])
        }
        if occupied and all(row_lo <= i <= row_hi for i in occupied):
            full_columns += 1
    return rows, full_columns


def _summarize(tool_name: str, args: dict[str, Any], rows: int, columns: int) -> str:
    sheet = args.get("sheet") or args.get("title") or "sheet ini"
    if tool_name == "tool_delete_sheet":
        return f"Hapus permanen sheet '{sheet}' beserta {rows} baris data."
    if tool_name == "tool_batch_update":
        return f"Hapus permanen sheet pada '{sheet}' ({rows} baris data)."
    scope = args.get("range") or "seluruh sheet"
    detail = f"{rows} baris"
    if columns:
        detail += f" dan {columns} kolom penuh"
    return f"Hapus permanen {detail} di sheet '{sheet}' (range {scope})."


def assess_impact(
    tool_name: str, args: dict[str, Any], grid: list[list[Any]]
) -> ImpactAssessment:
    """Assess what a destructive tool call would destroy.

    Args:
        tool_name: Destructive tool being called.
        args: The tool's arguments.
        grid: Current contents of the target sheet.

    Returns:
        ImpactAssessment; requires_approval is True when the call exceeds
        the unattended-destruction policy.
    """
    grid = grid or []
    if tool_name == "tool_delete_sheet":
        rows = len(_row_indices_with_data(grid))
        columns = max((len(r) for r in grid), default=0) if rows else 0
    elif tool_name == "tool_batch_update":
        deletes = [r for r in args.get("requests", []) if "deleteSheet" in r]
        if not deletes:
            return ImpactAssessment(0, 0, False, "")
        # deleteSheet identifies the tab by numeric sheetId, so the target
        # grid cannot be read here. Permanent deletion always asks.
        rows = len(_row_indices_with_data(grid))
        columns = max((len(r) for r in grid), default=0) if rows else 0
        return ImpactAssessment(
            rows, columns, True, _summarize(tool_name, args, rows, columns)
        )
    else:
        rows, columns = _assess_range(grid, args.get("range"))

    requires = rows > MAX_UNAPPROVED_ROWS or columns > 0
    summary = _summarize(tool_name, args, rows, columns) if requires else ""
    return ImpactAssessment(rows, columns, requires, summary)
