"""Shared outcomes and repeated summaries do not depend on agent architecture."""

from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.schema import Expect
from tests.e2e.schema import Case, Turn


@pytest.mark.parametrize(
    "runtime,native_scope", [("legacy", "bound_workbook"), ("main", "owned_workbooks")]
)
def test_shared_scope_only_adapts_explicit_comparison_cases(runtime, native_scope):
    """Historical scope contracts cannot silently become comparison fixtures."""
    from tests.e2e.comparison import ComparisonScope, SingleWorkbookSUT

    delegate = Mock(runtime=runtime)
    delegate.unsupported.return_value = None
    adapter = SingleWorkbookSUT(delegate, AsyncMock(), ComparisonScope(42, "one"))
    case = Case(id="shared", category="shared", title="Read", turns=[Turn(user="Read")])
    assert adapter.unsupported(case)
    delegate.unsupported.assert_not_called()
    case.resource_scope = "single_workbook_fixture"
    assert adapter.unsupported(case) is None
    assert delegate.unsupported.call_args.args[0].resource_scope == native_scope
    assert case.resource_scope == "single_workbook_fixture"


def test_answer_line_rejects_wrong_label_sign_and_extra_digits():
    """A matching digit substring cannot certify the requested labelled answer."""
    expected = Expect(answer_lines=["Amount total: 20"])
    for content in (
        "Credit total: 20",
        "Amount total: -20",
        "Amount total: 200",
        "Not Amount total: 20",
    ):
        assert not evaluate(expected, ResponseView(content, [], 1)).passed
    assert evaluate(
        expected, ResponseView("The total is below.\nAmount total: 20", [], 1)
    ).passed


def test_approval_count_cannot_override_missing_answer_line():
    """Passing approval evidence must not erase a failed financial answer check."""
    expected = Expect(answer_lines=["Amount total: 20"], pending_approvals_min=0)
    assert not evaluate(expected, ResponseView("Amount total: -20", [], 1)).passed


async def test_scope_observation_failure_preserves_runtime_evidence():
    """A failed post-run database check retains the runtime's recovery evidence."""
    from tests.e2e.comparison import SingleWorkbookSUT, ComparisonScope
    from tests.e2e.sut import TurnRequest
    from app.models.chat import KlaudiaMessage

    delegate = AsyncMock()
    delegate.runtime = "main"
    delegate.run.return_value = ResponseView(
        "Committed", [], 1, operation_references=["operation-one"]
    )
    pool = AsyncMock()
    pool.fetch.side_effect = [
        [{"spreadsheet_id": "one"}],
        RuntimeError("database unavailable"),
    ]
    adapter = SingleWorkbookSUT(delegate, pool, ComparisonScope(42, "one"))
    view = await adapter.run(
        TurnRequest(
            [KlaudiaMessage(role="user", content="Append")], 42, spreadsheet_id="one"
        )
    )
    assert view.operation_references == ["operation-one"]
    assert "database unavailable" in view.error


async def test_shared_adapter_rejects_extra_owned_workbooks():
    """A fixture scope cannot be used without its single-workbook precondition."""
    from tests.e2e.comparison import SingleWorkbookSUT, ComparisonScope
    from tests.e2e.sut import TurnRequest
    from app.models.chat import KlaudiaMessage

    delegate = AsyncMock()
    pool = AsyncMock()
    pool.fetch.return_value = [{"spreadsheet_id": "one"}, {"spreadsheet_id": "two"}]
    adapter = SingleWorkbookSUT(delegate, pool, ComparisonScope(42, "one"))
    with pytest.raises(ValueError, match="exactly one"):
        await adapter.run(
            TurnRequest(
                [KlaudiaMessage(role="user", content="Read")], 42, spreadsheet_id="one"
            )
        )
    delegate.run.assert_not_awaited()


def test_comparison_summary_keeps_failures_and_uses_nearest_rank_p95():
    """Failures stay in the denominator and latency definition remains explicit."""
    from tests.e2e.comparison import comparison_summary
    from tests.e2e.report import Report, TurnRecord

    reports = []
    for index, latency in enumerate((10, 20, 100)):
        view = ResponseView(
            "ok", [], latency, runtime="main", error="failed" if index == 2 else None
        )
        report = Report(
            [
                TurnRecord(
                    "sum", "shared", "Sum", 0, "Read", view, evaluate(Expect(), view)
                )
            ],
            metadata={"runtime": "main", "scenario": "sum", "repeat": index},
        )
        reports.append(report)
    summary = comparison_summary(reports)["main"]["sum"]
    assert summary["runs"] == 3
    assert summary["passed"] == 2
    assert summary["latency_ms_p50"] == 20
    assert summary["latency_ms_p95"] == 100
