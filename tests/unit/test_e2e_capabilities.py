"""Capability checks require observed evidence rather than worker names."""

from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.schema import Expect
import pytest


def test_missing_capability_observation_fails_instead_of_skipping():
    """An unobserved required capability cannot count as a passing check."""
    view = ResponseView(content="Done", tools_used=["data_entry_team"], latency_ms=1)
    assert not evaluate(Expect(capabilities_all=["append_records"]), view).passed


def test_prepare_and_tool_attempt_do_not_prove_a_write():
    """Only committed receipts satisfy an operation evidence requirement."""
    view = ResponseView(
        content="Done",
        tools_used=[],
        latency_ms=1,
        capabilities_attempted=["append_records"],
        operation_receipts=[{"status": "prepared"}],
    )
    assert not evaluate(Expect(committed_operations_min=1), view).passed


def test_metric_evidence_checks_label_sign_and_source():
    """A correct number under another label or table must fail."""
    expect = Expect(
        metric_evidence=[
            {
                "table_id": "claims",
                "column": "Debit",
                "operation": "sum",
                "value": "-20",
            }
        ]
    )
    view = ResponseView(
        content="Debit: -20",
        tools_used=[],
        latency_ms=1,
        calculations=[
            {
                "source": {"table_id": "claims"},
                "groups": [
                    {
                        "key": {},
                        "metrics": [
                            {"column": "Credit", "operation": "sum", "value": "-20"}
                        ],
                    }
                ],
            }
        ],
    )
    assert not evaluate(expect, view).passed
    view.calculations[0]["groups"][0]["metrics"][0]["column"] = "Debit"
    assert evaluate(expect, view).passed
    view.calculations[0]["groups"][0]["metrics"][0]["value"] = "20"
    assert not evaluate(expect, view).passed


def test_state_check_detects_duplicate_or_wrong_destination():
    """Exact fixture state catches writes that a plausible response could hide."""
    expect = Expect(ledger_state={"claims": [["Amount"], [20]], "other": [["Amount"]]})
    view = ResponseView(content="Added 20", tools_used=[], latency_ms=1)
    assert not evaluate(expect, view).passed
    view.ledger_state = {"claims": [["Amount"], [20], [20]], "other": [["Amount"]]}
    assert not evaluate(expect, view).passed
    view.ledger_state = expect.ledger_state
    assert evaluate(expect, view).passed
    view.ledger_state = {**expect.ledger_state, "unexpected": [[20]]}
    assert not evaluate(expect, view).passed


def test_replayed_receipts_count_as_one_operation():
    """Duplicate observation of a receipt cannot satisfy two required commits."""
    receipt = {"operation_id": "op_one", "status": "committed"}
    view = ResponseView(
        content="Done",
        tools_used=[],
        latency_ms=1,
        operation_receipts=[receipt, receipt],
    )
    assert evaluate(Expect(committed_operations_min=1), view).passed
    assert not evaluate(Expect(committed_operations_min=2), view).passed


def test_unsupported_cases_remain_in_report_denominator():
    """Unimplemented contracts appear as unsupported failures, never successful skips."""
    from tests.e2e.report import Report, TurnRecord

    view = ResponseView(
        content="",
        tools_used=[],
        latency_ms=0,
        runtime="main",
        unsupported="bound_workbook",
    )
    record = TurnRecord(
        "scope", "isolation", "Scope", 0, "Read", view, evaluate(Expect(), view)
    )
    report = Report([record])
    assert report.summary()["total_turns"] == 1
    assert report.summary()["unsupported"] == 1
    assert report.summary()["passed"] == 0
    assert report.to_json()["turns"][0]["runtime"] == "main"


@pytest.mark.parametrize(
    "calculation",
    [
        {"source": None, "groups": []},
        {"source": {"table_id": "claims"}, "groups": None},
        {"source": {"table_id": "claims"}, "groups": [{"key": {}, "metrics": [None]}]},
    ],
)
def test_malformed_calculation_evidence_fails_without_aborting(calculation):
    """Malformed observations produce a failed check, retaining the report row."""
    expected = Expect(
        metric_evidence=[
            {
                "table_id": "claims",
                "column": "Amount",
                "operation": "sum",
                "value": "20",
            }
        ]
    )
    view = ResponseView(
        content="Amount: 20", tools_used=[], latency_ms=1, calculations=[calculation]
    )
    assert not evaluate(expected, view).passed


def test_malformed_receipt_identity_cannot_crash_grading():
    """A malformed operation identifier cannot count as a commit or abort grading."""
    view = ResponseView(
        content="Done",
        tools_used=[],
        latency_ms=1,
        operation_receipts=[{"status": "committed", "operation_id": ["op"]}],
    )
    assert not evaluate(Expect(committed_operations_min=1), view).passed


def test_misspelled_expectation_cannot_silently_disable_a_check():
    """Unknown expectation keys fail dataset validation before the run starts."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Expect(capabilites_all=["append_records"])


def test_historical_dataset_retains_bound_workbook_contract():
    """Existing cases still validate and keep their original scope semantics."""
    from tests.e2e.loader import load_cases

    cases = load_cases()
    assert cases
    assert all(case.resource_scope == "bound_workbook" for case in cases)
