#!/usr/bin/env python3
"""Black-box HTTP runner for the Klaudia whitebox E2E dataset.

Drives the SAME dataset as the pytest layer, but over real HTTP against a running
server (POST /v1/chat) — the closest thing to what QA / production will hit. The
HTTP response only exposes sub-agent names, so granular `mcp_tools_*` assertions
are skipped here (the in-process layer covers those); routing, content and true
end-to-end latency are all scored.

Prereqs: ./startup.sh running (FastAPI on :8000 + MCP servers).

Usage:
  python -m tests.e2e.runner_http
  python -m tests.e2e.runner_http --base-url http://localhost:8000 --filter guardrails
  python -m tests.e2e.runner_http --include-mutating
  python -m tests.e2e.runner_http --id DR01-monthly-total
"""

from __future__ import annotations

import argparse
import base64
import time
from pathlib import Path

import httpx

from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.loader import attachment_bytes, load_cases
from tests.e2e.report import Report, TurnRecord
from tests.e2e.schema import Case, Turn

DEFAULT_BASE_URL = "http://localhost:8000"
CHAT_PATH = "/v1/chat"
TEST_USER_ID = 1
TEST_USER_NAME = "QARunner"
_OUT = Path(__file__).resolve().parent / "outputs" / "results_http.json"


def _encode_attachments(turn: Turn) -> list[dict]:
    out: list[dict] = []
    for rel in turn.all_attachments():
        name, ct, data = attachment_bytes(rel)
        out.append(
            {
                "filename": name,
                "content_type": ct,
                "data": base64.b64encode(data).decode("ascii"),
            }
        )
    return out


def _post_turn(
    client: httpx.Client, base_url: str, turn: Turn, session_id: int | None
) -> ResponseView:
    payload = {
        "messages": [
            {
                "role": "user",
                "content": turn.user,
                "attachments": _encode_attachments(turn) or None,
            }
        ],
        "session_id": session_id,
        "user_id": TEST_USER_ID,
        "user_name": TEST_USER_NAME,
    }
    start = time.time()
    try:
        resp = client.post(f"{base_url}{CHAT_PATH}", json=payload, timeout=120.0)
        wall_ms = int((time.time() - start) * 1000)
        resp.raise_for_status()
        data = resp.json()
        return ResponseView(
            content=data.get("message", {}).get("content", ""),
            tools_used=list(data.get("tools_used", [])),
            latency_ms=wall_ms,
            session_id=data.get("session_id"),
            cache_observable=False,  # HTTP cannot see KIE cache hits/misses
        )
    except Exception as exc:
        wall_ms = int((time.time() - start) * 1000)
        return ResponseView(
            content="", tools_used=[], latency_ms=wall_ms,
            session_id=session_id, cache_observable=False,
            error=f"{type(exc).__name__}: {exc}",
        )


def run_case_http(client: httpx.Client, base_url: str, case: Case) -> list[TurnRecord]:
    records: list[TurnRecord] = []
    session_id: int | None = None
    try:
        for idx, turn in enumerate(case.turns):
            view = _post_turn(client, base_url, turn, session_id)
            if view.session_id is not None:
                session_id = view.session_id
            records.append(
                TurnRecord(
                    case_id=case.id, category=case.category, title=case.title,
                    turn_index=idx, user=turn.user, view=view,
                    result=evaluate(turn.expect, view), layer="http",
                )
            )
    finally:
        for prompt in case.cleanup:
            cleanup_turn = Turn(user=prompt)
            _post_turn(client, base_url, cleanup_turn, session_id)
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description="Klaudia E2E HTTP runner")
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--filter", help="only run cases in this category")
    ap.add_argument("--id", help="only run the case with this exact id")
    ap.add_argument(
        "--include-mutating", action="store_true",
        help="include cases that write to the real sheet (default: skip)",
    )
    ap.add_argument("--out", default=str(_OUT))
    args = ap.parse_args()

    cases = load_cases()
    if args.filter:
        cases = [c for c in cases if c.category == args.filter]
    if args.id:
        cases = [c for c in cases if c.id == args.id]
    if not args.include_mutating and not args.id:
        cases = [c for c in cases if not c.mutating]

    if not cases:
        print("No cases selected.")
        return 1

    print(f"Running {len(cases)} cases against {args.base_url}{CHAT_PATH}")
    report = Report()
    with httpx.Client() as client:
        for c in cases:
            print(f"  → {c.id} ({c.category})")
            for rec in run_case_http(client, args.base_url, c):
                report.add(rec)

    print(report.render_table())
    out_path = Path(args.out)
    report.write_json(out_path)
    print(f"JSON written to {out_path}")

    s = report.summary()
    return 0 if s["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
