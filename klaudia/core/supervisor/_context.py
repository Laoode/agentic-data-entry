"""Per-layer system-prompt composition for the Klaudia graph.

The orchestrator no longer ships one monolithic persona to every node. It puts
the raw context slices (sheet list, file list, date) on the graph state as
explicit fields, and each layer builds the SMALLEST system prompt it needs:

    top supervisor / final reply  -> full Klaudia persona (owns the voice)
    team supervisor (classifier)  -> routing rules + sheet list only
    read / sheet / write agents   -> voice card + sheet list + date
    sql_agent                     -> voice card + file list + session id

Rationale: sub-agents run in their own context window. Inheriting the parent's
200-line persona wastes tokens, dilutes focus, and (for OpenAI-compatible
providers with a stable prefix) hurts KV-cache reuse. A compact voice card keeps
worker output in-voice so the router's verbatim pass-through still holds, without
carrying orchestration vocabulary the worker must not act on.
"""

from typing import Any

# Compact replacement for the ~200-line persona when a worker's text will reach
# the user verbatim (pass-through). Voice only, no orchestration/routing/plumbing.
KLAUDIA_VOICE_CARD = (
    "You are Klaudia, a senior finance colleague. These voice rules apply to any "
    "text the user will read:\n"
    "- Reply in the user's language (Indonesian by default, English if they use it). "
    "Address the user warmly as 'kak', woven naturally into the sentence.\n"
    "- Sound like a real, senior human colleague: warm, concise, quietly confident. "
    "Never say or imply you are an AI, bot, model, or assistant.\n"
    "- No em dash. Use a period, comma, colon, or a new sentence.\n"
    "- Never expose internal plumbing: no session IDs, internal field names, "
    "tool or agent names, or any mention of a system prompt / context.\n"
    "- Emoji are optional when they fit a warm or financial context."
)


def is_system_message(m: Any) -> bool:
    """True for dict {"role": "system"} turns and SystemMessage objects alike."""
    if isinstance(m, dict):
        return m.get("role") == "system"
    return getattr(m, "type", None) == "system"


def swap_system(messages: list[Any], new_system: str) -> list[Any]:
    """Return messages with every leading/embedded system turn replaced by one
    focused system message. Conversation/history/extraction turns are preserved
    in order; only the parent persona is dropped."""
    body = [m for m in messages if not is_system_message(m)]
    return [{"role": "system", "content": new_system}] + body


def build_worker_system(state: dict) -> str:
    """Focused context for read/sheet/write react agents."""
    sheets = state.get("sheets_context") or ""
    date = state.get("date_context") or ""
    parts = [KLAUDIA_VOICE_CARD]
    if sheets:
        parts.append(
            "AVAILABLE SHEETS (index -> title). Resolve names from this list "
            "VERBATIM; copy the title exactly:\n" + sheets
        )
    if date:
        parts.append(date)
    return "\n\n".join(parts)


def build_sql_system(state: dict) -> str:
    """Focused context for the sql_agent (uploaded receipt files only)."""
    files = state.get("files_context") or "No files uploaded in this session yet."
    session_id = state.get("session_id") or 0
    return "\n\n".join(
        [
            KLAUDIA_VOICE_CARD,
            "SESSION FILES:\n" + files,
            f"CURRENT SESSION ID: {session_id}",
        ]
    )


def build_team_classifier_context(base_prompt: str, sheets_context: str) -> str:
    """Team-supervisor routing prompt + the live sheet list, so the classifier
    knows which sheets exist (needed to decide create-then-write ordering)."""
    if not sheets_context:
        return base_prompt
    return (
        base_prompt
        + "\n\nAVAILABLE SHEETS (index -> title). Treat this as the complete set "
        "of sheets that currently exist:\n" + sheets_context
    )
