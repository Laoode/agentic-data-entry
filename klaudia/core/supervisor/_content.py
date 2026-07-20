"""Content coercion helper shared across supervisor + worker nodes.

Lives in its own module to avoid circular imports between ``agent.py``
(top-level supervisor) and ``agents/*`` (workers). Both depend on it.
"""

import re
from typing import Any


def coerce_to_text(content: Any) -> str:
    """Coerce a LangChain message content payload into a plain string.

    Gemini (and other multimodal LLMs) can return ``content`` as either a
    ``str`` or a list of part-dicts like
    ``[{"type": "text", "text": "...", "extras": {"signature": "..."}}]``.
    Naively ``str()``-ing the list yields a Python ``repr`` (single quotes,
    nested ``extras`` blob) which leaks to users when re-wrapped as a
    ``HumanMessage(content=...)`` for the supervisor.

    Rules:
    - ``str`` → returned trimmed.
    - ``list`` → concatenate ``item["text"]`` for each part dict; raw string
      parts pass through. Anything without a ``text`` key is dropped.
    - ``None`` → empty string.
    - Other types → ``str()`` then trimmed (last-resort).
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                txt = item.get("text") if "text" in item else ""
                if isinstance(txt, str):
                    parts.append(txt)
        return "".join(parts).strip()
    return str(content).strip()


# Strip only the bracketed marker token; preserve any inline summary that the
# worker wrote alongside the marker. Stripping the whole line would drop the
# user-facing summary and break the named-worker fallback in
# `_resolve_final_content` whenever the worker's reply was just one line.
_INTERNAL_MARKER_TOKEN_RE = re.compile(
    r"\[(?:WRITE_DONE|READ_DONE|SHEET_DONE|CLARIFY)\]\s*"
)


def strip_internal_markers(text: str) -> str:
    """Remove [WRITE_DONE]/[READ_DONE]/[SHEET_DONE]/[CLARIFY] tokens while
    keeping ALL of the human-readable text the worker emitted around them.

    Workers emit these markers so the team supervisor's deterministic
    completion gate can fire without an LLM call. This helper only neutralises
    the bracket tokens; it keeps every surrounding line, because the worker text
    is used as GROUND TRUTH for the final re-voicing pass (router.py's
    _emit_final_reply). Dropping any of it would strip figures/tables the
    persona reply must preserve. Leaked worker scratchpad never reaches the user
    verbatim anymore: the top supervisor always re-voices worker output through
    the full Klaudia persona, which rewrites it into a clean user-facing reply.
    """
    if not text:
        return ""
    cleaned = _INTERNAL_MARKER_TOKEN_RE.sub("", text)
    return "\n".join(
        line.rstrip() for line in cleaned.splitlines() if line.strip()
    ).strip()


# Internal plumbing identifiers that must never surface in user-facing text.
# A worker occasionally echoes one of these straight from its own system prompt
# (e.g. sql_agent saying "SESSION FILES masih kosong"). That is a leak on its
# own, AND when the final-reply LLM (which carries the anti-leak persona) sees
# the phrase it misreads it as a prompt-extraction attempt and refuses outright.
# Scrubbing the worker text before it reaches the user or the final LLM closes
# both failure modes. Applied only to worker output, so legitimate financial
# content is never touched.
_INTERNAL_PHRASE_SUBS = (
    (re.compile(r"\bSESSION FILES\b", re.IGNORECASE), "file yang diupload"),
    (re.compile(r"\bAVAILABLE GOOGLE SHEETS\b", re.IGNORECASE), "daftar sheet"),
    (re.compile(r"\bCURRENT SESSION ID\b", re.IGNORECASE), "sesi ini"),
)
_INTERNAL_TOKEN_RE = re.compile(
    r"\b(?:data_entry_team|sql_agent|read_agent|write_agent|sheet_agent"
    r"|session_files|available_sheets|tool_[a-z_]+)\b",
    re.IGNORECASE,
)
_MULTISPACE_RE = re.compile(r"[ \t]{2,}")


def scrub_internal_identifiers(text: str) -> str:
    """Neutralize internal field names, agent names, and tool names so they
    never reach the user or the final-reply LLM. Conservative: only known
    plumbing tokens are touched; everything else passes through verbatim."""
    if not text:
        return ""
    out = text
    for pattern, replacement in _INTERNAL_PHRASE_SUBS:
        out = pattern.sub(replacement, out)
    out = _INTERNAL_TOKEN_RE.sub("sistem", out)
    return _MULTISPACE_RE.sub(" ", out)
