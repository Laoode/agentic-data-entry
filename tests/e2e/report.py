"""Shared reporting for both the pytest and HTTP layers.

Produces a category summary table (pass rate + latency) plus a per-turn
breakdown, and a machine-readable JSON dump for the next phase (deciding whether
to fix the dataset or the code). The result itself is not asserted to be 100% —
the goal is a faithful measurement.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
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
            "runtime": self.view.runtime,
            "unsupported": self.view.unsupported,
            "capabilities_attempted": self.view.capabilities_attempted,
            "calculations": self.view.calculations,
            "append_attempts": self.view.append_attempts,
            "append_attempts_omitted": self.view.append_attempts_omitted,
            "append_attempts_observable": self.view.append_attempts_observable,
            "operation_receipts": self.view.operation_receipts,
            "operation_references": self.view.operation_references,
            "model_steps": self.view.model_steps,
            "loaded_skills": self.view.loaded_skills,
            "ledger_state": self.view.ledger_state,
            "response_snippet": (self.view.content or "")[:240],
        }


@dataclass
class Report:
    records: list[TurnRecord] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

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
            "unsupported": sum(bool(r.view.unsupported) for r in self.records),
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
            note = (
                "" if r.result.passed else (" | " + "; ".join(r.result.reasons))[:120]
            )
            warn = " ⚠lat" if r.result.latency_warn else ""
            out.append(
                f"  {r.case_id:<14}{r.turn_index:>2}  {mark:<2}{routed:<22}"
                f"{r.view.latency_ms:>7}{warn}{note}"
            )
        out.append("")
        return "\n".join(out)

    def to_json(self) -> dict:
        return {
            "metadata": self.metadata,
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

    # ── Per-model markdown summary ───────────────────────────────────────────

    def render_markdown(self, model: str, provider: str = "") -> str:
        """Render a markdown report (category summary + per-turn breakdown).

        Mirrors the hand-curated table-<model>.md format so model runs can be
        compared side by side over time.
        """
        s = self.summary()
        cats = self._by_category()
        prov = f" (provider `{provider}`)" if provider else ""
        lines: list[str] = [
            "# KLAUDIA WHITEBOX E2E — RESULTS",
            "",
            f"**Model:** `{model}`{prov}  ",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
            f"**Overall:** {s['passed']}/{s['total_turns']} "
            f"({s['pass_rate'] * 100:.0f}%) · p50 {s['latency_ms_median']}ms · "
            f"max {s['latency_ms_max']}ms",
            "",
            "## Summary by Category",
            "",
            "| Category | Turns | Pass | Rate | p50 (ms) | max (ms) |",
            "|---|---|---|---|---|---|",
        ]
        for cat in sorted(cats):
            rows = cats[cat]
            n = len(rows)
            p = sum(1 for r in rows if r.result.passed)
            lat = [r.view.latency_ms for r in rows if r.view.latency_ms]
            p50 = round(median(lat)) if lat else 0
            mx = max(lat) if lat else 0
            rate = f"{(p / n * 100):.0f}%" if n else "-"
            lines.append(f"| {cat} | {n} | {p} | {rate} | {p50} | {mx} |")
        lines.append(
            f"| **OVERALL** | **{s['total_turns']}** | **{s['passed']}** | "
            f"**{s['pass_rate'] * 100:.0f}%** | **{s['latency_ms_median']}** | "
            f"**{s['latency_ms_max']}** |"
        )

        lines += [
            "",
            "## Per-Turn Breakdown",
            "",
            "| ID | T | P | Routed To | ms | Detail |",
            "|---|---|---|---|---|---|",
        ]
        for r in self.records:
            mark = "✓" if r.result.passed else "✗"
            routed = ", ".join(sorted(set(r.view.tools_used))) or "FINISH"
            detail = (
                "; ".join(r.result.reasons).replace("|", "\\|")
                if r.result.reasons
                else ""
            )
            lines.append(
                f"| {r.case_id} | {r.turn_index} | {mark} | {routed} | "
                f"{r.view.latency_ms} | {detail} |"
            )
        lines.append("")
        return "\n".join(lines)

    def write_markdown(
        self,
        out_dir: Path,
        model: str,
        provider: str = "",
        filename: str | None = None,
    ) -> Path:
        """Write the markdown report and return its path.

        Defaults to out_dir/table-<model-slug>.md. `filename` overrides that so a
        second bench over the same model (the synthetic hard bench) writes its own
        table instead of overwriting the main one.
        """
        slug = re.sub(r"[^a-z0-9.]+", "-", model.lower()).strip("-") or "model"
        path = out_dir / (filename or f"table-{slug}.md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_markdown(model, provider))
        return path
