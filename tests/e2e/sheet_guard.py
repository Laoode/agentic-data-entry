"""Deterministic Google Sheet reset for the in-process E2E suite.

Mutating cases append rows to "Jun" and rewrite the "Juni" total in "Rangkuman
Total" (double-entry: a Jun write is always paired with a Rangkuman Total
update). The dataset's LLM `cleanup` prompts are best-effort and drift, so later
read/routing cases (e.g. R01, which asserts the canonical Juni total) see a
corrupted sheet.

This guard restores the guarded sheets to the EXACT contents of docs/TABLE.md —
the single source of truth for the fixture scheme — via direct MCP tool calls
(no agent, no LLM), after every mutating case and at suite end. Because the
source is TABLE.md (not a runtime snapshot), a dirty start state cannot poison
the baseline: the sheet is always rewritten to the template. It also deletes any
tab that TABLE.md does not define, cleaning up create/copy/rename leftovers.

Values are written with USER_ENTERED (the MCP default); the spreadsheet locale
is Indonesian, so the dotted strings from TABLE.md ("2.164.500", "12.000")
parse back to the same numbers the sheet already stores.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Sheets that mutating cases write to and that later cases assert amounts on.
GUARDED_SHEETS = ("Jun", "Rangkuman Total")

_TABLE_MD = Path(__file__).resolve().parents[2] / "docs" / "TABLE.md"
# Bounded wipe range — comfortably larger than any fixture sheet, cheap to clear.
_CLEAR_RANGE = "A1:Z1000"


def _tool(registry: Any, name: str):
    return next((t for t in registry.tools if t.name == name), None)


def _col_letter(idx0: int) -> str:
    s, n = "", idx0 + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def load_table_md(
    path: Path = _TABLE_MD,
) -> tuple[list[str], dict[str, list[list[str]]]]:
    """Parse docs/TABLE.md into (ordered sheet names, {name: rows}).

    Format per block: 'Index: N,' / 'Name: <name>,' / 'Table:' then tab-
    separated rows until a blank line. Name may be quoted and/or comma-suffixed.
    """
    names: list[str] = []
    data: dict[str, list[list[str]]] = {}
    current: str | None = None
    in_table = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("Index:"):
            current, in_table = None, False
            continue
        if line.startswith("Name:"):
            name = line[len("Name:") :].strip().strip(",").strip().strip('"').strip()
            current, in_table = name, False
            names.append(name)
            data[name] = []
            continue
        if line.strip() == "Table:":
            in_table = True
            continue
        if not line.strip():
            in_table = False
            continue
        if in_table and current is not None:
            data[current].append(line.split("\t"))

    return names, data


def _iter_json_objects(raw: str):
    """Yield JSON objects from one object, an array, or whitespace-concatenated
    objects (tool_list_sheets uses the last form)."""
    s = (raw or "").strip()
    if not s:
        return
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            yield from (o for o in parsed if isinstance(o, dict))
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


def _titles(raw: str) -> list[str]:
    return [t for o in _iter_json_objects(raw) if (t := o.get("title"))]


class SheetGuard:
    """Restore guarded sheets + drop stray tabs, from the TABLE.md template.

    spreadsheet_id scopes every tool call to the test user's spreadsheet
    (ledger backend, per-user tenancy). None = the backend's default
    workspace (gsheets, or ledger before tenancy resolution).
    """

    def __init__(
        self, gsheets_registry: Any, spreadsheet_id: str | None = None
    ) -> None:
        self._reg = gsheets_registry
        self._spreadsheet_id = spreadsheet_id
        self._names: list[str] = []
        self._data: dict[str, list[list[str]]] = {}

    def _args(self, **kwargs: Any) -> dict[str, Any]:
        if self._spreadsheet_id is not None:
            kwargs["spreadsheet_id"] = self._spreadsheet_id
        return kwargs

    @property
    def _baseline_titles(self) -> set[str]:
        return set(self._names)

    async def snapshot(self) -> None:
        """Load the TABLE.md baseline. Named snapshot() for fixture symmetry;
        the baseline is the file, not the live sheet, so there is nothing to
        read from Sheets here."""
        try:
            self._names, self._data = load_table_md()
            logger.info("SheetGuard: loaded TABLE.md baseline tabs=%s", self._names)
        except Exception as exc:
            logger.warning("SheetGuard: failed to load TABLE.md: %s", exc)

    async def _list_titles(self) -> list[str]:
        lister = _tool(self._reg, "tool_list_sheets")
        if lister is None:
            return []
        try:
            return _titles(await lister.ainvoke(self._args()))
        except Exception as exc:
            logger.warning("SheetGuard: list_sheets failed: %s", exc)
            return []

    async def seed(self) -> None:
        """Materialize the FULL TABLE.md baseline (all tabs, exact contents).

        Only used for spreadsheet-scoped runs (ledger tenancy): the test
        user's spreadsheet is provisioned empty, unlike the gsheets fixture
        sheet which is assumed to match TABLE.md already.
        """
        if not self._names:
            logger.warning("SheetGuard: no baseline loaded; seed skipped")
            return
        existing = set(await self._list_titles())
        for name in self._names:
            await self._write_sheet(name, create=name not in existing)
        await self._drop_extra_sheets()

    async def restore(self) -> None:
        # 1. Drop any tab TABLE.md does not define (copy/new/rename leftovers).
        await self._drop_extra_sheets()

        # 2. Rewrite guarded sheets to the template contents (recreating any
        # that a mutating case deleted).
        existing = set(await self._list_titles())
        for sheet in GUARDED_SHEETS:
            await self._write_sheet(sheet, create=sheet not in existing)

    async def _write_sheet(self, name: str, create: bool) -> None:
        """Create (or clear) one tab, then write its TABLE.md rows."""
        create_tool = _tool(self._reg, "tool_create_sheet")
        clear = _tool(self._reg, "tool_clear_range")
        update = _tool(self._reg, "tool_update_cells")
        if create_tool is None or clear is None or update is None:
            logger.warning("SheetGuard: sheet tools missing; write skipped")
            return
        rows = self._data.get(name)
        try:
            if create:
                await create_tool.ainvoke(self._args(title=name))
            else:
                await clear.ainvoke(self._args(sheet=name, range=_CLEAR_RANGE))
            if rows:
                width = max(len(r) for r in rows)
                rng = f"A1:{_col_letter(width - 1)}{len(rows)}"
                await update.ainvoke(self._args(sheet=name, range=rng, data=rows))
        except Exception as exc:
            logger.warning("SheetGuard: write of %s failed: %s", name, exc)

    async def _drop_extra_sheets(self) -> None:
        baseline = self._baseline_titles
        if not baseline:
            return  # never parsed a baseline — refuse to delete blindly
        delete = _tool(self._reg, "tool_delete_sheet")
        if delete is None:
            return
        for title in await self._list_titles():
            if title in baseline:
                continue
            try:
                await delete.ainvoke(self._args(sheet=title))
                logger.info("SheetGuard: deleted non-baseline sheet %r", title)
            except Exception as exc:
                logger.warning("SheetGuard: delete of %r failed: %s", title, exc)
