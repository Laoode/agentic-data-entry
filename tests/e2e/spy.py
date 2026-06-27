"""In-process MCP tool-call spy.

The public HTTP response only reports sub-agent names. To assert the *granular*
MCP tool calls (e.g. `tool_append_rows`) and their parameters, we wrap every tool
in the SQLite + GSheets registries and record each invocation.

Each registry tool is a `StructuredTool.from_function(coroutine=_call, ...)`
(see klaudia/interfaces/tool_registry.py). `coroutine` is a real pydantic field,
so it can be reassigned — unlike the `ainvoke` method — and `_call(**kwargs)`
receives the exact tool arguments. We wrap `coroutine` to record (name, kwargs)
then delegate, leaving behavior unchanged. Registries are restored on exit.

Usage:

    spy = MCPSpy([container.mcp_sqlite, container.mcp_gsheets])
    with spy.capture() as calls:
        await orchestrator.process(...)
    # calls == [("tool_append_rows", {"sheet": "Jun", ...}), ...]
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class MCPSpy:
    """Patches `coroutine` on every tool of the given registries to record calls."""

    def __init__(self, registries: list[Any]) -> None:
        self._registries = [r for r in registries if r is not None]
        self._calls: list[tuple[str, dict]] = []

    @property
    def calls(self) -> list[tuple[str, dict]]:
        return self._calls

    @contextmanager
    def capture(self) -> Iterator[list[tuple[str, dict]]]:
        """Record all tool invocations made within the block.

        Resets the call log on entry so each turn captures only its own calls.
        Tools whose `coroutine` cannot be wrapped are skipped (the granular
        checks degrade to "skipped" rather than crashing the run).
        """
        self._calls = []
        originals: list[tuple[Any, Any]] = []

        for reg in self._registries:
            for tool in getattr(reg, "tools", []) or []:
                original = getattr(tool, "coroutine", None)
                if original is None:
                    continue

                def make_wrapper(name: str, original):
                    async def wrapper(**kwargs: Any):
                        self._calls.append((name, dict(kwargs)))
                        return await original(**kwargs)

                    return wrapper

                try:
                    tool.coroutine = make_wrapper(tool.name, original)
                    originals.append((tool, original))
                except Exception:
                    # Pydantic blocked the assignment — skip this tool.
                    continue

        try:
            yield self._calls
        finally:
            for tool, original in originals:
                try:
                    tool.coroutine = original
                except Exception:
                    pass
