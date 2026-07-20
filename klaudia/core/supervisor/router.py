import logging
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END
from langgraph.types import Command
from typing_extensions import TypedDict

from klaudia.core.supervisor._content import (
    coerce_to_text,
    scrub_internal_identifiers,
    strip_internal_markers,
)
from klaudia.core.supervisor.llm import ainvoke_route, with_structured
from klaudia.core.supervisor.prompts import SUPERVISOR_ROUTING_PROMPT
from klaudia.core.supervisor.state import SupervisorState

logger = logging.getLogger(__name__)

MEMBERS = ["sql_agent", "data_entry_team"]
OPTIONS = ["FINISH"] + MEMBERS

# Top-level workers whose reply triggers a deterministic FINISH+summarize.
_WORKER_NAMES = ("data_entry_team", "sql_agent")

# How a worker's reply becomes the user-facing message, split by marker semantics:
#   * [WRITE_DONE]/[READ_DONE]/[SHEET_DONE] — a factual REPORT of completed work.
#     Re-voiced through the full Klaudia persona (streamed), because workers only
#     carry a compact voice card and re-voicing gives the reply her real
#     character. The worker text is immutable ground truth (fidelity clause below)
#     so figures/tables are never dropped or altered.
#   * [CLARIFY] — a QUESTION addressed to the user. Passed through verbatim (NOT
#     re-voiced): an LLM told to "write the reply" tends to ANSWER the question
#     instead of relaying it (e.g. echoing a destructive confirmation phrase the
#     worker asked the user to type). Safety over persona richness here.
_FINAL_REPLY_BASE = (
    "You are Klaudia, speaking DIRECTLY to the user right now. The user will see "
    "ONLY the reply you write in this turn. They have NOT seen any other message, "
    "table, or note, and nothing in this context except the user's own lines was "
    "said BY the user.\n"
    "\n"
    "VOICE: warm and human, a senior finance colleague who addresses the user as "
    "'kak', quietly confident, uses precise accounting terms naturally (ledger, "
    "saldo, rekonsiliasi, audit trail), and formats for instant auditability "
    "(bold key figures, compact markdown tables, short labeled lists). No em "
    "dash. Never mention tools, agents, sheet IDs, or any system/plumbing "
    "detail, and never echo internal tokens like "
    "[WRITE_DONE]/[READ_DONE]/[SHEET_DONE]/[CLARIFY]."
)

# Appended AFTER the folded-in result block. This is what stops the model from
# treating its own internal working output as if the user had already seen it
# ("sudah saya rangkum di atas") and replying with a bare acknowledgment.
_FINAL_REPLY_DELIVER_RULES = (
    "\n\nThe block above is the RESULT you just produced by working on the "
    "user's request. It is your own internal working output. The user has NOT "
    "seen it. Write the reply that DELIVERS this result to the user:\n"
    "- Reproduce EVERY row, figure, amount, date, and name from the result "
    "above, EXACTLY. It is immutable ground truth: never round, drop, invent, or "
    "recompute anything.\n"
    "- Present it FRESH, as your own answer. NEVER say or imply it was 'shown "
    "above', 'sudah saya rangkum di atas', 'as summarized above', or that the "
    "user already has it. Your reply is the ONLY place this result appears, so "
    "the full data (e.g. the entire table) MUST be inside it.\n"
    "- Lead with the direct answer, show the data in a compact table or bolded "
    "list, add one short useful insight if natural, and close warmly. Do NOT "
    "collapse it into a bare acknowledgment like 'sudah beres ya kak'.\n"
    "- Match the user's language."
)

_FINAL_REPLY_NO_RESULT = (
    "\n\nAnswer the user's last message directly in Klaudia's voice: warm, "
    "concrete, and helpful."
)


def _build_final_instruction(source: str) -> str:
    """Compose the final-reply system instruction. When worker output exists it
    is folded in as an explicitly-labeled internal RESULT block (NOT a user
    turn), so the model DELIVERS it instead of acknowledging it as pre-seen."""
    if not source:
        return _FINAL_REPLY_BASE + _FINAL_REPLY_NO_RESULT
    return (
        _FINAL_REPLY_BASE
        + "\n\n=== RESULT YOU JUST PRODUCED (internal; the user has NOT seen it; "
        "it was NOT said by the user) ===\n"
        + source
        + "\n=== END RESULT ==="
        + _FINAL_REPLY_DELIVER_RULES
    )


def _prepare_finish_messages(state_messages: list[Any]) -> list[Any]:
    """Build the final-reply prompt.

    Worker reports are NOT re-added as conversation turns. As HumanMessages they
    read to the model as USER input, so it replies TO them ("sudah saya rangkum
    di atas") instead of presenting them. Instead their text is folded into the
    final system instruction as a labeled internal RESULT block; only the real
    user / history turns remain in the message list.
    """
    convo: list[Any] = []
    reports: list[str] = []
    for msg in state_messages:
        if getattr(msg, "name", None) in _WORKER_NAMES:
            text = scrub_internal_identifiers(
                strip_internal_markers(coerce_to_text(getattr(msg, "content", "")))
            )
            if text:
                reports.append(text)
        else:
            convo.append(msg)
    convo.append(SystemMessage(content=_build_final_instruction("\n\n".join(reports))))
    return convo


class RouterWithResponse(TypedDict):
    """Combined routing + response for initial FINISH decisions.

    When `next` is FINISH and no worker has run yet, `response` contains the
    user-facing reply — skipping the second _emit_final_reply LLM call.
    When routing to a worker, `response` must be "".
    """

    next: Literal["FINISH", "sql_agent", "data_entry_team"]
    response: str


def make_supervisor_node(llm: BaseChatModel):
    """Create a supervisor node that routes between sub-agents."""

    async def _emit_final_reply(state_messages: list[Any]) -> Command:
        final_llm = llm.with_config({"tags": ["final_answer"]})
        reply = await final_llm.ainvoke(_prepare_finish_messages(state_messages))
        return Command(goto=END, update={"messages": [reply], "next": "FINISH"})

    async def supervisor_node(state: SupervisorState) -> Command[...]:
        state_messages = state["messages"]

        # Deterministic FINISH gate — a worker just reported, so skip the routing
        # LLM call.
        if state_messages:
            last = state_messages[-1]
            last_name = getattr(last, "name", None)
            if last_name in _WORKER_NAMES:
                last_text = coerce_to_text(getattr(last, "content", ""))
                # [CLARIFY] is a QUESTION addressed to the user. Pass it through
                # verbatim (marker stripped + scrubbed); do NOT re-voice it. An
                # LLM told to "write the reply" tends to ANSWER the question
                # instead of relaying it — e.g. echoing the very confirmation
                # phrase the worker asked the USER to type ("ya, hapus semua").
                # Safety > persona richness for a clarification.
                if "[CLARIFY]" in last_text:
                    clean = scrub_internal_identifiers(
                        strip_internal_markers(last_text)
                    )
                    if clean:
                        logger.info(
                            f"Supervisor: FINISH (clarify pass-through from {last_name})"
                        )
                        return Command(
                            goto=END,
                            update={
                                "messages": [AIMessage(content=clean)],
                                "next": "FINISH",
                            },
                        )
                # Completed work ([WRITE_DONE]/[READ_DONE]/[SHEET_DONE]) is a
                # factual report → re-voice through the full Klaudia persona.
                logger.info(
                    f"Supervisor: deterministic FINISH (re-voice reply from {last_name})"
                )
                return await _emit_final_reply(state_messages)

        # Combined routing + response call — one LLM hop instead of two for FINISH path
        messages = [
            {"role": "system", "content": SUPERVISOR_ROUTING_PROMPT},
        ] + state_messages

        combined_llm = with_structured(llm, RouterWithResponse).with_config(
            {"tags": ["nostream"]}
        )
        result = await ainvoke_route(combined_llm, messages)
        if result is None:
            # LLM produced no parseable routing object (e.g. malformed DeepSeek
            # tool-call JSON) even after retry. Degrade to a plain user-facing
            # reply instead of crashing the whole request.
            logger.warning("Supervisor: no valid structured route; FINISH fallback")
            return await _emit_final_reply(state_messages)
        goto = result.get("next", "FINISH")
        inline_response = (result.get("response") or "").strip()

        if goto not in MEMBERS:
            if inline_response:
                logger.info(
                    f"Supervisor: FINISH with inline response ({len(inline_response)} chars)"
                )
                return Command(
                    goto=END,
                    update={
                        "messages": [AIMessage(content=inline_response)],
                        "next": "FINISH",
                    },
                )
            logger.info(
                f"Supervisor routing to FINISH (raw: {goto!r}), generating reply"
            )
            return await _emit_final_reply(state_messages)

        logger.info(f"Supervisor routing to: {goto}")
        return Command(goto=goto, update={"next": goto})

    return supervisor_node
