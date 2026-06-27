#!/usr/bin/env python3
"""Generate a Postman collection from the E2E dataset.

Mirrors endpoint_test/postman_*.json: one POST /v1/chat request per turn, grouped
into a folder per category. Attachments are inlined as base64 (Postman has no easy
multi-file binding for JSON bodies). Variables: {{base_url}} and {{session_id}}.

Multi-turn cases set {{session_id}} from the first turn's response via a small test
script so the collection runner threads the session like the real client.

Usage:
  python -m tests.e2e.gen_postman
  python -m tests.e2e.gen_postman --out tests/e2e/outputs/klaudia_e2e.postman_collection.json
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from tests.e2e.loader import attachment_bytes, load_cases
from tests.e2e.schema import Case, Turn

_OUT = Path(__file__).resolve().parent / "outputs" / "klaudia_e2e.postman_collection.json"

# Captures session_id from the response into a collection variable so subsequent
# turns of a multi-turn case reuse the same session.
_CAPTURE_SCRIPT = [
    "var ok = pm.response.code === 200;",
    "pm.test('status 200', function () { pm.expect(ok).to.be.true; });",
    "if (ok) {",
    "  var body = pm.response.json();",
    "  if (body.session_id) { pm.collectionVariables.set('session_id', body.session_id); }",
    "  pm.test('routed_to ' + JSON.stringify(body.tools_used || []), function () { pm.expect(true).to.be.true; });",
    "}",
]


def _attachments_json(turn: Turn) -> list[dict] | None:
    atts = []
    for rel in turn.all_attachments():
        name, ct, data = attachment_bytes(rel)
        atts.append(
            {
                "filename": name,
                "content_type": ct,
                "data": base64.b64encode(data).decode("ascii"),
            }
        )
    return atts or None


def _turn_request(case: Case, turn: Turn, idx: int, reset_session: bool) -> dict:
    body = {
        "messages": [
            {
                "role": "user",
                "content": turn.user,
                "attachments": _attachments_json(turn),
            }
        ],
        # First turn of a case starts fresh; later turns reuse the captured id.
        "session_id": None if reset_session else "{{session_id}}",
        "user_id": 1,
        "user_name": "QARunner",
    }
    raw = json.dumps(body, ensure_ascii=False, indent=2)
    # Replace the JSON-quoted placeholder so Postman treats it as a variable/number.
    raw = raw.replace('"{{session_id}}"', "{{session_id}}")

    name = f"{case.id} · turn {idx + 1}"
    if turn.note:
        name += f" — {turn.note[:40]}"

    return {
        "name": name,
        "event": [
            {"listen": "test", "script": {"type": "text/javascript", "exec": _CAPTURE_SCRIPT}}
        ],
        "request": {
            "method": "POST",
            "header": [{"key": "Content-Type", "value": "application/json"}],
            "body": {"mode": "raw", "raw": raw, "options": {"raw": {"language": "json"}}},
            "url": {
                "raw": "{{base_url}}/v1/chat",
                "host": ["{{base_url}}"],
                "path": ["v1", "chat"],
            },
            "description": f"[{case.category}] {case.title}\n\nExpect: {turn.expect.model_dump(exclude_defaults=True)}",
        },
    }


def build_collection(cases: list[Case]) -> dict:
    folders: dict[str, dict] = {}
    for c in cases:
        folder = folders.setdefault(
            c.category, {"name": c.category, "item": []}
        )
        for idx, turn in enumerate(c.turns):
            folder["item"].append(
                _turn_request(c, turn, idx, reset_session=(idx == 0))
            )

    return {
        "info": {
            "name": "Klaudia Whitebox E2E",
            "description": (
                "Auto-generated from tests/e2e/dataset. One POST /v1/chat per turn, "
                "grouped by category. Set {{base_url}} (e.g. http://localhost:8000). "
                "{{session_id}} is captured automatically for multi-turn cases."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000"},
            {"key": "session_id", "value": ""},
        ],
        "item": list(folders.values()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Postman collection from dataset")
    ap.add_argument("--out", default=str(_OUT))
    ap.add_argument(
        "--include-mutating", action="store_true",
        help="include sheet-mutating cases (default: skip for a safe collection)",
    )
    args = ap.parse_args()

    cases = load_cases()
    if not args.include_mutating:
        cases = [c for c in cases if not c.mutating]

    collection = build_collection(cases)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(collection, ensure_ascii=False, indent=2))
    n_req = sum(len(f["item"]) for f in collection["item"])
    print(f"Wrote {out_path} — {len(cases)} cases, {n_req} requests, {len(collection['item'])} folders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
