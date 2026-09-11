"""Repeated runs retain every scheduled trial, including incomplete work."""

import asyncio
import json

import pytest

from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.report import Report, TurnRecord
from tests.e2e.schema import Expect


def trial_report():
    """Return a passing single-turn observation without live model calls."""
    view = ResponseView("ok", [], 10)
    return Report(
        [TurnRecord("sum", "shared", "sum", 0, "Read", view, evaluate(Expect(), view))]
    )


async def test_setup_failure_stays_in_planned_denominator(tmp_path):
    """One failed setup does not prevent subsequent scheduled trials."""
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("sum_1000", 2, {})
    seen = []

    async def execute(trial):
        """Fail the first trial and return valid observations for the rest."""
        seen.append(trial["runtime"])
        if len(seen) == 1:
            raise RuntimeError("setup unavailable")
        return trial_report()

    path = tmp_path / "comparison.json"
    await run.execute(execute, path)
    saved = json.loads(path.read_text())
    assert seen == ["legacy", "main", "main", "legacy"]
    assert saved["planned"] == 4
    assert saved["passed"] == 3
    assert saved["trials"][0]["status"] == "error"
    assert saved["complete"]
    assert saved["scheduled_summary"]["legacy"] == {
        "planned": 2,
        "passed": 1,
        "errors": 1,
        "incomplete": 0,
    }


async def test_empty_observation_cannot_pass_and_schedule_precedes_execution(tmp_path):
    """A malformed trial stays failed and the schedule exists before its callback."""
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("sum_1000", 1, {})
    path = tmp_path / "comparison.json"

    async def execute(trial):
        """Check the durable schedule, then return no financial observation."""
        saved = json.loads(path.read_text())
        assert saved["planned"] == 2
        assert any(item["status"] == "running" for item in saved["trials"])
        return Report()

    await run.execute(execute, path)
    assert all(trial["status"] == "error" for trial in run.trials)


async def test_cancellation_persists_interrupted_and_unrun_trials(tmp_path):
    """Cancellation propagates after saving the full original schedule."""
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("append", 2, {})

    async def execute(trial):
        """Cancel before returning an observation."""
        raise asyncio.CancelledError()

    path = tmp_path / "comparison.json"
    with pytest.raises(asyncio.CancelledError):
        await run.execute(execute, path)
    saved = json.loads(path.read_text())
    assert not saved["complete"]
    assert [trial["status"] for trial in saved["trials"]] == [
        "interrupted",
        "not_run",
        "not_run",
        "not_run",
    ]
    assert saved["passed"] == 0


def test_fixture_mismatch_rejects_before_execution():
    """Both runtimes and all repeats must share inputs and expectations."""
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("sum_1000", 1, {})
    run.check_fixture(run.trials[0], "first")
    with pytest.raises(ValueError, match="fixture"):
        run.check_fixture(run.trials[1], "changed")


async def test_cleanup_failure_keeps_observed_recovery_evidence(tmp_path):
    """A callback can retain its observation before a failing fixture teardown."""
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("append", 1, {})

    async def execute(trial):
        """Retain a committed reference before simulating cleanup failure."""
        report = trial_report()
        report.records[0].view.operation_references = ["operation-one"]
        trial["report"] = report.to_json()
        raise RuntimeError("cleanup failed")

    path = tmp_path / "comparison.json"
    await run.execute(execute, path)
    saved = json.loads(path.read_text())
    assert saved["passed"] == 0
    assert saved["trials"][0]["report"]["turns"][0]["operation_references"] == [
        "operation-one"
    ]


async def test_agent_cancellation_retains_operation_references(tmp_path):
    """Cancellation recovery evidence reaches the manifest before propagation."""
    from klaudia.core.agent.agent import AgentRunCancelled, RunOutcome
    from tests.e2e.comparison_run import ComparisonRun

    run = ComparisonRun("append", 1, {})

    async def execute(trial):
        """Cancel after the optional agent has retained a prepared operation."""
        raise AgentRunCancelled(
            RunOutcome(
                "cancelled", "", 2, (), {}, (), operation_references=("operation-one",)
            )
        )

    path = tmp_path / "comparison.json"
    with pytest.raises(AgentRunCancelled):
        await run.execute(execute, path)
    saved = json.loads(path.read_text())
    assert saved["trials"][0]["recovery"]["operation_references"] == ["operation-one"]


@pytest.mark.parametrize("repeats", [0, 11])
def test_repeat_budget_rejects_unbounded_or_empty_runs(repeats):
    """Live comparison costs have an explicit one-to-ten repeat bound."""
    from tests.e2e.comparison_run import ComparisonRun

    with pytest.raises(ValueError):
        ComparisonRun("sum_1000", repeats, {})
