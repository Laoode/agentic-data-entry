"""Shared reporting for both the pytest and HTTP layers.

Produces a category summary table (pass rate + latency) plus a per-turn
breakdown, and a machine-readable JSON dump for the next phase (deciding whether
to fix the dataset or the code). The result itself is not asserted to be 100% —
the goal is a faithful measurement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, median

from tests.e2e.checks import CheckResult, ResponseView


@dataclass
class TurnRecord:
    case_id: str
    category: str
    title: str
    turn_index: int
    user: str
    view: ResponseView
    result: CheckResult
    layer: str = "in_process"  # or "http"

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "title": self.title,
            "turn": self.turn_index,
            "layer": self.layer,
            "user": self.user,
            "passed": self.result.passed,
            "reasons": self.result.reasons,
            "detail": self.result.detail,
            "latency_ms": self.view.latency_ms,
            "latency_warn": self.result.latency_warn,
            "routed_to": sorted(set(self.view.tools_used)),
            "mcp_tools": self.view.mcp_tool_names,
            "session_id": self.view.session_id,
            "error": self.view.error,
            "response_snippet": (self.view.content or "")[:240],
        }


@dataclass
class Report:
    records: list[TurnRecord] = field(default_factory=list)

    def add(self, rec: TurnRecord) -> None:
        self.records.append(rec)

    # ── Aggregation ──────────────────────────────────────────────────────────

    def _by_category(self) -> dict[str, list[TurnRecord]]:
        cats: dict[str, list[TurnRecord]] = {}
        for r in self.records:
            cats.setdefault(r.category, []).append(r)
        return cats

    def summary(self) -> dict:
        total = len(self.records)
        passed = sum(1 for r in self.records if r.result.passed)
        lat = [r.view.latency_ms for r in self.records if r.view.latency_ms]
        return {
            "total_turns": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "latency_ms_mean": round(mean(lat)) if lat else 0,
            "latency_ms_median": round(median(lat)) if lat else 0,
            "latency_ms_max": max(lat) if lat else 0,
        }

    # ── Rendering ────────────────────────────────────────────────────────────

    def render_table(self) -> str:
        cats = self._by_category()
        line = "─" * 86
        out: list[str] = [
            "",
            "KLAUDIA WHITEBOX E2E — RESULTS",
            line,
            f"{'Category':<26}{'Turns':>6}{'Pass':>6}{'Rate':>7}"
            f"{'p50 ms':>9}{'max ms':>9}",
            line,
        ]
        for cat in sorted(cats):
            rows = cats[cat]
            n = len(rows)
            p = sum(1 for r in rows if r.result.passed)
            lat = [r.view.latency_ms for r in rows if r.view.latency_ms]
            p50 = round(median(lat)) if lat else 0
            mx = max(lat) if lat else 0
            rate = f"{(p / n * 100):.0f}%" if n else "-"
            out.append(f"{cat:<26}{n:>6}{p:>6}{rate:>7}{p50:>9}{mx:>9}")
        out.append(line)

        s = self.summary()
        rate = f"{s['pass_rate'] * 100:.0f}%"
        out.append(
            f"{'OVERALL':<26}{s['total_turns']:>6}{s['passed']:>6}{rate:>7}"
            f"{s['latency_ms_median']:>9}{s['latency_ms_max']:>9}"
        )
        out.append(line)
        out.append("")
        out.append("Per-turn breakdown:")
        out.append(f"  {'ID':<14}{'T':>2}  {'P':<2}{'routed_to':<22}{'ms':>7}  detail")
        out.append("  " + "─" * 84)
        for r in self.records:
            mark = "✓" if r.result.passed else "✗"
            routed = ",".join(sorted(set(r.view.tools_used))) or "FINISH"
            note = "" if r.result.passed else (" | " + "; ".join(r.result.reasons))[:120]
            warn = " ⚠lat" if r.result.latency_warn else ""
            out.append(
                f"  {r.case_id:<14}{r.turn_index:>2}  {mark:<2}{routed:<22}"
                f"{r.view.latency_ms:>7}{warn}{note}"
            )
        out.append("")
        return "\n".join(out)

    def to_json(self) -> dict:
        return {
            "summary": self.summary(),
            "by_category": {
                cat: {
                    "turns": len(rows),
                    "passed": sum(1 for r in rows if r.result.passed),
                }
                for cat, rows in self._by_category().items()
            },
            "turns": [r.to_dict() for r in self.records],
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json(), indent=2, ensure_ascii=False))
