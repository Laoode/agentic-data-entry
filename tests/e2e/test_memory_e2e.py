"""Cross-session memory eval (in-process).

Runs the `12_memory.yaml` cases, which exercise long-term memory across fresh
sessions (and, for isolation, across users). Kept separate from the bench
(test_e2e_dataset.py) because these cases:
  - need long-term memory enabled for the `needs_memory`-tagged ones (embed
    service + MEMORY_MODE); they skip cleanly otherwise, while the deterministic
    continuity / anti-confabulation cases still run,
  - reset the (isolated) memory collection before each case for independence.

Assertions are real (misses fail, not just recorded): each case is a specific
capability or security claim, e.g. MEM04's leak-rate-must-be-0. The harness
flushes background memory writes before each new-session turn so a write in one
session is durable before the next session recalls it.
"""

from __future__ import annotations

import urllib.request

import pytest

from tests.e2e.conftest import requires_live
from tests.e2e.engine_inprocess import run_case_inprocess
from tests.e2e.loader import load_cases

_MEMORY_CASES = [c for c in load_cases() if c.category == "memory"]


def _memory_operational(container) -> bool:
    """True only when memory is enabled AND the embed service is reachable.

    Prevents `needs_memory` cases from failing confusingly when memory is
    switched on but the embedding service is not running: they skip instead.
    """
    if container.memory is None:
        return False
    base = container.settings.memory_embed_base_url.rstrip("/")
    if base.endswith("/v1"):
        base = base[:-3].rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def _params():
    for case in _MEMORY_CASES:
        marks = [pytest.mark.e2e]
        if case.mutating:
            marks.append(pytest.mark.mutating)
        yield pytest.param(case, id=case.id, marks=marks)


@requires_live
@pytest.mark.asyncio(loop_scope="module")
@pytest.mark.parametrize("case", list(_params()))
async def test_memory_case(
    case, orchestrator, spy, extraction_spy, sheet_guard, container
):
    needs_memory = "needs_memory" in (case.tags or [])
    if needs_memory and not _memory_operational(container):
        pytest.skip(
            "case needs long-term memory: set MEMORY_MODE=write and run services/embed"
        )

    # Reset the isolated eval collection so each case starts from a clean slate.
    if container.memory is not None:
        await container.memory.reset()

    records = await run_case_inprocess(
        orchestrator, spy, extraction_spy, case, sheet_guard, container
    )

    crashes = [r for r in records if r.view.error]
    assert not crashes, "\n".join(
        f"{r.case_id} turn {r.turn_index}: {r.view.error}" for r in crashes
    )
    misses = [r for r in records if not r.result.passed]
    assert not misses, "\n".join(
        f"{r.case_id} turn {r.turn_index}: {'; '.join(r.result.reasons)}"
        for r in misses
    )
