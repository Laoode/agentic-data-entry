"""Materialize named grids into a spreadsheet via the sheets MCP tool surface.

The deterministic write primitive shared by SheetGuard (the docs/TABLE.md
baseline) and the synthetic hard-bench cases. No LLM: it drives
tool_create_sheet / tool_clear_range / tool_update_cells directly. A
spreadsheet_id scopes every call to one tenant's spreadsheet (ledger backend);
None targets the backend's default workspace (gsheets, or ledger before tenancy
resolution).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Bounded wipe range - comfortably larger than any fixture sheet, cheap to clear.
_CLEAR_RANGE = "A1:Z1000"


def tool(registry: Any, name: str):
    """First tool named `name` in a registry, or None."""
    return next((t for t in registry.tools if t.name == name), None)


def col_letter(idx0: int) -> str:
    """0-based column index to a spreadsheet column letter (0 -> A, 26 -> AA)."""
    s, n = "", idx0 + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def iter_json_objects(raw: str):
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


def titles(raw: str) -> list[str]:
    """Sheet titles parsed from a tool_list_sheets result."""
    return [t for o in iter_json_objects(raw) if (t := o.get("title"))]


class LedgerSeeder:
    """Write named grids into a (optionally tenant-scoped) spreadsheet."""

    def __init__(self, registry: Any, spreadsheet_id: str | None = None) -> None:
        self._reg = registry
        self._spreadsheet_id = spreadsheet_id

    def _args(self, **kwargs: Any) -> dict[str, Any]:
        if self._spreadsheet_id is not None:
            kwargs["spreadsheet_id"] = self._spreadsheet_id
        return kwargs

    async def list_titles(self) -> list[str]:
        lister = tool(self._reg, "tool_list_sheets")
        if lister is None:
            return []
        try:
            return titles(await lister.ainvoke(self._args()))
        except Exception as exc:
            logger.warning("LedgerSeeder: list_sheets failed: %s", exc)
            return []

    async def write_grid(
        self, name: str, rows: list[list[Any]], *, create: bool
    ) -> None:
        """Create (or clear) one tab, then write `rows` starting at A1."""
        create_tool = tool(self._reg, "tool_create_sheet")
        clear = tool(self._reg, "tool_clear_range")
        update = tool(self._reg, "tool_update_cells")
        if create_tool is None or clear is None or update is None:
            logger.warning("LedgerSeeder: sheet tools missing; write skipped")
            return
        try:
            if create:
                await create_tool.ainvoke(self._args(title=name))
            else:
                await clear.ainvoke(self._args(sheet=name, range=_CLEAR_RANGE))
            if rows:
                width = max(len(r) for r in rows)
                rng = f"A1:{col_letter(width - 1)}{len(rows)}"
                await update.ainvoke(self._args(sheet=name, range=rng, data=rows))
        except Exception as exc:
            logger.warning("LedgerSeeder: write of %s failed: %s", name, exc)

    async def seed_grids(self, grids: dict[str, list[list[Any]]]) -> None:
        """Materialize every grid, creating tabs that do not exist yet."""
        existing = set(await self.list_titles())
        for name, rows in grids.items():
            await self.write_grid(name, rows, create=name not in existing)

    async def restore_to_baseline(self, grids: dict[str, list[list[Any]]]) -> None:
        """Return the spreadsheet to exactly `grids`: drop stray tabs, reseed.

        The full-template restore used around a mutating case, so a case that
        appended, cleared, or deleted anything cannot leak into the next: any tab
        the baseline does not define is deleted, then every baseline tab is
        rewritten from the frozen grids.
        """
        baseline = set(grids)
        delete = tool(self._reg, "tool_delete_sheet")
        if delete is not None:
            for title in await self.list_titles():
                if title not in baseline:
                    try:
                        await delete.ainvoke(self._args(sheet=title))
                    except Exception as exc:
                        logger.warning(
                            "LedgerSeeder: drop of %r failed: %s", title, exc
                        )
        await self.seed_grids(grids)
