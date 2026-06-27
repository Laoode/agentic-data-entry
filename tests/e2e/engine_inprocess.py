"""Run a dataset case in-process against the real KlaudiaOrchestrator.

Each turn is one orchestrator.process() call. Turns in a case share a session
(created on the first turn, reused after). The MCP spy captures granular tool
calls per turn so `mcp_tools_*` assertions can be evaluated — something the HTTP
layer cannot see. Cleanup prompts run best-effort in a finally block.
"""

from __future__ import annotations

import asyncio
import logging
import os

from app.models.attachment import FileAttachment
from app.models.chat import KlaudiaMessage
from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.loader import attachment_bytes
from tests.e2e.report import TurnRecord
from tests.e2e.schema import Case, Turn

logger = logging.getLogger(__name__)

TEST_USER_ID = 1
TEST_USER_NAME = "QARunner"

# A turn that exceeds this is recorded as a failure instead of blocking the suite.
# Real agent turns run ~30-55s (cold first call ~55s; heavier multi-tool/KIE turns
# more), so the budget is generous to avoid false timeouts. Override via
# E2E_TURN_TIMEOUT for faster local iteration.
TURN_TIMEOUT_S = float(os.environ.get("E2E_TURN_TIMEOUT", "180"))
CLEANUP_TIMEOUT_S = float(os.environ.get("E2E_CLEANUP_TIMEOUT", "120"))


def _build_message(turn: Turn) -> list[KlaudiaMessage]:
    attachments = None
    paths = turn.all_attachments()
    if paths:
        attachments = []
        for rel in paths:
            name, ct, data = attachment_bytes(rel)
            attachments.append(
                FileAttachment(filename=name, content_type=ct, data=data)
            )
    return [KlaudiaMessage(role="user", content=turn.user, attachments=attachments)]


async def run_case_inprocess(orchestrator, spy, case: Case) -> list[TurnRecord]:
    """Execute every turn of `case`, returning a TurnRecord per turn.

    spy: an MCPSpy whose `.capture()` context records tool calls for the turn.
    Behavioral mismatches do NOT raise — they are recorded in the TurnRecord.
    Only an exception during process() is captured as a transport error.
    """
    records: list[TurnRecord] = []
    session_id: int | None = None

    try:
        for idx, turn in enumerate(case.turns):
            messages = _build_message(turn)
            try:
                with spy.capture() as calls:
                    resp = await asyncio.wait_for(
                        orchestrator.process(
                            messages=messages,
                            session_id=session_id,
                            user_id=TEST_USER_ID,
                            user_name=TEST_USER_NAME,
                        ),
                        timeout=TURN_TIMEOUT_S,
                    )
                session_id = resp.session_id
                view = ResponseView(
                    content=resp.message.content,
                    tools_used=list(resp.tools_used),
                    latency_ms=resp.processing_time_ms,
                    session_id=resp.session_id,
                    mcp_calls=list(calls),
                )
            except asyncio.TimeoutError:
                logger.error(
                    "case %s turn %d timed out after %.0fs", case.id, idx, TURN_TIMEOUT_S
                )
                view = ResponseView(
                    content="", tools_used=[], latency_ms=int(TURN_TIMEOUT_S * 1000),
                    session_id=session_id,
                    error=f"timeout after {TURN_TIMEOUT_S:.0f}s (agent hung or looping)",
                )
            except Exception as exc:  # transport / pipeline failure
                logger.exception("case %s turn %d crashed", case.id, idx)
                view = ResponseView(
                    content="", tools_used=[], latency_ms=0,
                    session_id=session_id, error=f"{type(exc).__name__}: {exc}",
                )

            result = evaluate(turn.expect, view)
            records.append(
                TurnRecord(
                    case_id=case.id,
                    category=case.category,
                    title=case.title,
                    turn_index=idx,
                    user=turn.user,
                    view=view,
                    result=result,
                    layer="in_process",
                )
            )
    finally:
        # Best-effort cleanup in the same session — never fails the case.
        for prompt in case.cleanup:
            try:
                await asyncio.wait_for(
                    orchestrator.process(
                        messages=[KlaudiaMessage(role="user", content=prompt)],
                        session_id=session_id,
                        user_id=TEST_USER_ID,
                        user_name=TEST_USER_NAME,
                    ),
                    timeout=CLEANUP_TIMEOUT_S,
                )
            except Exception:
                logger.warning("cleanup failed/timed out for %s: %r", case.id, prompt)

    return records
