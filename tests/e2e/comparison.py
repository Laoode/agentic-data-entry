"""Shared financial outcomes under a verified single-workbook fixture contract."""

from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
import hashlib
import json
from math import ceil
from statistics import median
from time import perf_counter
from typing import AsyncIterator

import asyncpg

from ledger.store import LedgerStore
from tests.e2e.capability_cases import (
    CapabilityFixture,
    Scenario,
    seeded_capability_case,
)
from tests.e2e.checks import ResponseView
from tests.e2e.report import Report
from tests.e2e.schema import Case
from tests.e2e.sut import SystemUnderTest, TurnRequest


@dataclass(frozen=True)
class ComparisonScope:
    """Fixture identity checked independently of either runtime's own tools."""

    user_id: int
    workbook_id: str


class SingleWorkbookSUT:
    """Adapt only explicit shared cases after verifying the fixture's scope."""

    def __init__(
        self, delegate: SystemUnderTest, pool: asyncpg.Pool, scope: ComparisonScope
    ) -> None:
        """Bind the runtime to one newly seeded owner's workbook.

        Args:
            delegate: Existing legacy or main adapter, without tool changes.
            pool: Sandbox database for independent scope checks.
            scope: Fixture owner and sole workbook.
        """
        self._delegate = delegate
        self._pool = pool
        self._scope = scope
        self.runtime = delegate.runtime

    def unsupported(self, case: Case) -> str | None:
        """Accept only explicit single-turn comparison cases.

        Args:
            case: Shared outcome requirements.

        Returns:
            A reason for unsupported contracts, without rewriting historical cases.
        """
        if case.resource_scope != "single_workbook_fixture":
            return "comparison requires an explicit single_workbook_fixture contract"
        if len(case.turns) != 1 or case.cleanup:
            return "comparison supports one independent turn without cleanup prompts"
        native_scope = (
            "bound_workbook" if self.runtime == "legacy" else "owned_workbooks"
        )
        return self._delegate.unsupported(
            case.model_copy(update={"resource_scope": native_scope})
        )

    async def _check_scope(self) -> None:
        """Require the fixture owner to retain exactly its seeded workbook.

        Raises:
            ValueError: Ownership changed or the fixture includes other workbooks.
        """
        rows = await self._pool.fetch(
            "SELECT spreadsheet_id FROM ledger_spreadsheet WHERE user_id = $1",
            self._scope.user_id,
        )
        if [row["spreadsheet_id"] for row in rows] != [self._scope.workbook_id]:
            raise ValueError("Comparison fixture must own exactly one seeded workbook")

    async def run(self, request: TurnRequest) -> ResponseView:
        """Execute identical requests with verified fixture scope and wall timing.

        Args:
            request: Fresh-session user input bound to this fixture owner/workbook.

        Returns:
            Runtime evidence with measured adapter wall time.

        Raises:
            ValueError: Request identity or fixture scope differs from the contract.
        """
        if (
            request.user_id != self._scope.user_id
            or request.spreadsheet_id != self._scope.workbook_id
            or request.session_id is not None
        ):
            raise ValueError(
                "Comparison request must use its fresh fixture identity and workbook"
            )
        await self._check_scope()
        started = perf_counter()
        try:
            view = await self._delegate.run(request)
        except Exception as exc:
            view = ResponseView(
                "", [], 0, runtime=self.runtime, error=f"{type(exc).__name__}: {exc}"
            )
        view.latency_ms = round((perf_counter() - started) * 1000)
        try:
            await self._check_scope()
        except Exception as exc:
            view.error = f"{view.error}; {exc}" if view.error else str(exc)
        return view


@asynccontextmanager
async def seeded_comparison_case(
    store: LedgerStore, scenario: Scenario, user_id: int
) -> AsyncIterator[CapabilityFixture]:
    """Reuse seeded records with architecture-independent outcome requirements.

    Args:
        store: Connected sandbox ledger.
        scenario: Financial case shared by both runtimes.
        user_id: Fresh isolated owner created for this trial.

    Yields:
        Identical prompts and expected state, without native tool requirements.
    """
    async with seeded_capability_case(store, scenario, user_id=user_id) as fixture:
        case = fixture.case
        case.resource_scope = "single_workbook_fixture"
        case.category = "shared_outcome"
        case.id = f"COMPARE-{scenario}"
        turn = case.turns[0]
        expected = turn.expect
        expected.capabilities_all = []
        expected.committed_operations_min = None
        expected.metric_evidence = []
        expected.content_all = []
        expected.contains_amount = []
        if scenario == "sum_1000":
            total = sum(row[-1] for row in expected.ledger_state["Claims"][1:])
            turn.user += " End with a plain line 'Amount total: <integer>' using no digit separators."
            expected.answer_lines = [f"Amount total: {total}"]
        else:
            turn.user += (
                " If committed, end with the plain line 'Append result: committed'."
            )
            expected.answer_lines = ["Append result: committed"]
        yield fixture


async def fixture_digest(fixture: CapabilityFixture) -> str:
    """Fingerprint shared inputs and expectations while excluding random identities.

    Args:
        fixture: Seeded scenario before runtime execution.

    Returns:
        Digest suitable for comparing runtime/repeat fixture equivalence.
    """
    turn = fixture.case.turns[0]
    payload = {
        "prompt": turn.user,
        "initial_state": await fixture.observe_state(),
        "expected": turn.expect.model_dump(mode="json"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def comparison_summary(reports: list[Report]) -> dict:
    """Summarise each runtime/scenario without excluding failed turns.

    Args:
        reports: One report for each attempted independent trial.

    Returns:
        Pass counts and median/nearest-rank p95 of positive recorded latencies.

    Raises:
        ValueError: A trial report contains other than one turn.
    """
    grouped = defaultdict(lambda: defaultdict(list))
    for report in reports:
        if len(report.records) != 1:
            raise ValueError("Each comparison trial must contain exactly one turn")
        grouped[report.metadata["runtime"]][report.metadata["scenario"]].append(
            report.records[0]
        )
    summary = {}
    for runtime, scenarios in grouped.items():
        summary[runtime] = {}
        for scenario, records in scenarios.items():
            latencies = sorted(
                record.view.latency_ms
                for record in records
                if record.view.latency_ms > 0
            )
            summary[runtime][scenario] = {
                "runs": len(records),
                "passed": sum(record.result.passed for record in records),
                "latency_samples": len(latencies),
                "latency_ms_p50": median(latencies) if latencies else None,
                "latency_ms_p95": latencies[ceil(0.95 * len(latencies)) - 1]
                if latencies
                else None,
            }
    return summary
