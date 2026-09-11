"""Persist a fixed comparison schedule before invoking any runtime."""

from collections.abc import Awaitable, Callable
import json
from pathlib import Path

from klaudia.core.agent.agent import AgentRunCancelled
from tests.e2e.capability_cases import Scenario
from tests.e2e.comparison import comparison_summary
from tests.e2e.report import Report


class ComparisonRun:
    """Retain failed, interrupted and unrun trials in one report manifest."""

    def __init__(self, scenario: Scenario, repeats: int, metadata: dict) -> None:
        """Create a bounded, alternating runtime schedule.

        Args:
            scenario: Shared financial fixture.
            repeats: Independent attempts per runtime, from one to ten.
            metadata: Model configuration and source revision, excluding secrets.

        Raises:
            ValueError: Scenario or repeat budget is unsupported.
        """
        if scenario not in ("sum_1000", "append") or not 1 <= repeats <= 10:
            raise ValueError(
                "Comparison requires a supported scenario and 1 to 10 repeats"
            )
        self.metadata = metadata
        self.trials = [
            {
                "runtime": runtime,
                "scenario": scenario,
                "repeat": repeat,
                "status": "not_run",
            }
            for repeat in range(1, repeats + 1)
            for runtime in (("legacy", "main") if repeat % 2 else ("main", "legacy"))
        ]
        self._fixture_digest: str | None = None
        self._reports: list[Report] = []

    def check_fixture(self, trial: dict, digest: str) -> None:
        """Reject changed inputs before a runtime receives the request.

        Args:
            trial: Scheduled trial receiving this fixture.
            digest: Fingerprint of initial state, prompt and expectations.

        Raises:
            ValueError: A fixture differs from the first scheduled fixture.
        """
        trial["fixture_digest"] = digest
        if self._fixture_digest is not None and digest != self._fixture_digest:
            raise ValueError("Comparison fixture differs from the initial trial")
        self._fixture_digest = digest

    def to_json(self) -> dict:
        """Return the complete schedule and summaries of observed turns.

        Returns:
            Manifest whose planned denominator includes every trial status.
        """
        return {
            "metadata": self.metadata,
            "planned": len(self.trials),
            "passed": sum(trial["status"] == "passed" for trial in self.trials),
            "complete": all(
                trial["status"] in ("passed", "failed", "error")
                for trial in self.trials
            ),
            "trials": self.trials,
            "scheduled_summary": {
                runtime: {
                    "planned": sum(
                        trial["runtime"] == runtime for trial in self.trials
                    ),
                    "passed": sum(
                        trial["runtime"] == runtime and trial["status"] == "passed"
                        for trial in self.trials
                    ),
                    "errors": sum(
                        trial["runtime"] == runtime and trial["status"] == "error"
                        for trial in self.trials
                    ),
                    "incomplete": sum(
                        trial["runtime"] == runtime
                        and trial["status"] in ("not_run", "running", "interrupted")
                        for trial in self.trials
                    ),
                }
                for runtime in ("legacy", "main")
            },
            "observed_summary": comparison_summary(self._reports),
        }

    def write(self, path: Path) -> None:
        """Replace this run's report atomically, never a historical report.

        Args:
            path: Unique report path allocated for this run.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        pending = path.with_suffix(".pending")
        pending.write_text(json.dumps(self.to_json(), indent=2), encoding="utf-8")
        pending.replace(path)

    async def execute(
        self, execute_trial: Callable[[dict], Awaitable[Report]], path: Path
    ) -> None:
        """Run each trial and persist progress even when execution is cancelled.

        Args:
            execute_trial: Fixture setup, scope checks, runtime and cleanup.
            path: Unique destination for the full schedule and observations.

        Raises:
            BaseException: Cancellation or process interruption, after reporting.
        """
        self.write(path)
        for trial in self.trials:
            trial["status"] = "running"
            self.write(path)
            try:
                report = await execute_trial(trial)
                if len(report.records) != 1:
                    raise ValueError("Comparison trial must return exactly one turn")
                report.metadata.update(
                    {key: trial[key] for key in ("runtime", "scenario", "repeat")}
                )
                self._reports.append(report)
                trial["report"] = report.to_json()
                trial["status"] = (
                    "passed" if report.records[0].result.passed else "failed"
                )
            except Exception as exc:
                trial["status"] = "error"
                trial["error"] = f"{type(exc).__name__}: {exc}"
            except AgentRunCancelled as exc:
                trial["status"] = "interrupted"
                trial["recovery"] = {
                    "operation_references": list(exc.outcome.operation_references),
                    "operation_receipts": list(exc.outcome.operation_receipts),
                }
                raise
            except BaseException:
                trial["status"] = "interrupted"
                raise
            finally:
                self.write(path)
