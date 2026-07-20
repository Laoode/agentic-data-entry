"""Coordinate annotation for Google Sheets read output.

The MCP read tools (``tool_get_sheet_data`` / ``tool_get_multiple_sheet_data``)
return a bare 2D array with no row/column coordinates. To build a write target
(e.g. ``update_cells('B5', ...)``) the model then has to *count* rows by hand,
which is exactly where it fails: it forgets row 1 is the header and writes to the
row above the one it meant, silently corrupting a neighbouring record.

This module rewrites that output so every row is tagged with its REAL Google
Sheets row number plus a column letter legend. The model reads ``R5: April`` and
the target ``B5`` instead of inferring it arithmetically. Fail-soft: any input
that cannot be parsed is returned unchanged.
"""

import json
import logging
from typing import Any, Iterator

logger = logging.getLogger(__name__)


def col_letter(idx0: int) -> str:
    """0-based column index → A1 column letters (0→A, 25→Z, 26→AA)."""
    s = ""
    n = idx0 + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def _iter_json_objects(raw: str) -> Iterator[dict]:
    """Yield top-level JSON objects from a string holding one object, a JSON
    array, or several objects concatenated with whitespace (the multi-sheet
    case — MCP emits one object per sheet, space/newline separated)."""
    s = raw.strip()
    if not s:
        return
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            for o in parsed:
                if isinstance(o, dict):
                    yield o
            return
        if isinstance(parsed, dict):
            yield parsed
            return
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(s):
        chunk = s[pos:].lstrip()
        if not chunk:
            break
        skipped = len(s[pos:]) - len(chunk)
        try:
            obj, end = decoder.raw_decode(chunk)
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict):
            yield obj
        pos += skipped + end


def _render_sheet(obj: dict[str, Any]) -> str | None:
    """Render one sheet object into a coordinate-annotated text block, or None
    if it carries no tabular rows to annotate.

    Two MCP shapes must both be handled — they use different keys:
      * tool_get_multiple_sheet_data → {"sheet"/query…, "data": [[…]]}
      * tool_get_sheet_data (single) → {"range": "Jun", "values": [[…]]}
    Missing the ``values`` alias silently no-ops annotation on the single-sheet
    read the write agent grounds updates on, so it counts rows by hand and
    writes one row off (corrupting a neighbouring record)."""
    data = obj.get("data")
    if data is None:
        data = obj.get("values")
    if not isinstance(data, list) or not data:
        return None

    sheet = obj.get("sheet") or obj.get("title") or obj.get("range") or "?"
    header = data[0] if isinstance(data[0], list) else [data[0]]
    legend = " | ".join(
        f"{col_letter(c)}={'' if v is None else v}" for c, v in enumerate(header)
    )

    lines = [
        f"[Sheet: {sheet}] Row numbers below are the REAL Google Sheets rows "
        f"(row 1 = header, first data row = row 2). Build A1 cell refs directly "
        f'from them — column B of row 5 is "B5". Never recount rows by hand.',
        f"Columns: {legend}",
    ]
    for r, row in enumerate(data, start=1):
        cells = row if isinstance(row, list) else [row]
        rendered = " | ".join("" if v is None else str(v) for v in cells)
        lines.append(f"R{r}: {rendered}")
    return "\n".join(lines)


def annotate_sheet_output(raw: str) -> str:
    """Transform raw get_sheet_data / get_multiple_sheet_data JSON into a
    row-numbered, column-lettered text block. Fail-soft: returns ``raw``
    unchanged when it cannot be parsed or holds no tabular data."""
    if not isinstance(raw, str) or not raw.strip():
        return raw
    try:
        blocks = [b for o in _iter_json_objects(raw) if (b := _render_sheet(o))]
    except Exception as exc:  # never let annotation break a tool call
        logger.warning("coordinate annotation failed, returning raw: %s", exc)
        return raw
    return "\n\n".join(blocks) if blocks else raw
