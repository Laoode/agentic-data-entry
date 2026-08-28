import json
import logging
from contextvars import ContextVar, Token
from typing import Any, Literal

from toon_format import encode as encode_toon

logger = logging.getLogger(__name__)

ExtractionContextFormat = Literal["toon", "json"]

# Request-scoped tenant boundary: the spreadsheet all sheets tools operate on
# for the current request. Set by the orchestrator before graph invocation
# (child tasks inherit it), read by with_tenant_scope at tool-call time.
# None means unscoped (dev default workspace / gsheets backend).
_ACTIVE_SPREADSHEET: ContextVar[str | None] = ContextVar(
    "active_spreadsheet", default=None
)


def set_active_spreadsheet(spreadsheet_id: str | None) -> Token:
    """Bind the active spreadsheet for the current request context."""
    return _ACTIVE_SPREADSHEET.set(spreadsheet_id)


def reset_active_spreadsheet(token: Token) -> None:
    """Restore the scope captured by the matching set_active_spreadsheet."""
    _ACTIVE_SPREADSHEET.reset(token)


def get_active_spreadsheet() -> str | None:
    """Return the active spreadsheet id, or None when unscoped."""
    return _ACTIVE_SPREADSHEET.get()


# Per-request tool-call trace. The orchestrator starts one before invoking
# the supervisor; with_recording-wrapped tools append (name, args, raw
# output). Child tasks inherit the ContextVar, and appends mutate the same
# list, so the starter sees every call. None = tracing off (no overhead).
_TOOL_TRACE: ContextVar["list[tuple[str, dict, str]] | None"] = ContextVar(
    "tool_trace", default=None
)


def start_tool_trace() -> tuple[list, Token]:
    """Begin recording tool calls for the current request context.

    Returns:
        (trace list to read after the turn, token for reset_tool_trace).
    """
    trace: list[tuple[str, dict, str]] = []
    return trace, _TOOL_TRACE.set(trace)


def reset_tool_trace(token: Token) -> None:
    """Stop recording; the trace list handed out by start remains readable."""
    _TOOL_TRACE.reset(token)


def record_tool_call(name: str, args: dict, output: str) -> None:
    """Append one tool invocation to the active trace, if any."""
    trace = _TOOL_TRACE.get()
    if trace is not None:
        trace.append((name, dict(args), output))


# Approval gate for irreversible operations. The app installs an async
# callable (tool_name, args, impact) -> approval_id that persists a pending
# approval; the guard then refuses to execute. None = no gating (dev,
# unit tests, offline scripts), in which case destructive calls run
# straight through as before.
_APPROVAL_GATE: ContextVar[Any] = ContextVar("approval_gate", default=None)


def set_approval_gate(gate: Any) -> Token:
    """Install the approval gate for the current request context."""
    return _APPROVAL_GATE.set(gate)


def reset_approval_gate(token: Token) -> None:
    """Remove the approval gate installed by set_approval_gate."""
    _APPROVAL_GATE.reset(token)


def get_approval_gate() -> Any:
    """Return the active approval gate, or None when gating is off."""
    return _APPROVAL_GATE.get()


def build_session_context(session_files: list[dict[str, Any]] | None) -> str:
    """Format session files into a context string for the system prompt."""
    if not session_files:
        return "No files in this session."

    lines: list[str] = []
    for i, f in enumerate(session_files, 1):
        pages_info = f.get("pages", [])
        if pages_info:
            extracted = sum(1 for p in pages_info if p.get("status") == "extracted")
            total = len(pages_info)
        else:
            # Page-level details not loaded — infer from file-level status
            total = f.get("total_pages", 0)
            extracted = total if f.get("status") == "completed" else 0
        lines.append(
            f"{i}. {f.get('file_name', 'unknown')}\n"
            f"   - Type: {f.get('type', 'unknown')}\n"
            f"   - Status: {f.get('status', 'unknown')}\n"
            f"   - Pages: {extracted}/{total} extracted\n"
            f"   - File ID: {f.get('id', '?')}"
        )
    return "\n".join(lines)


_PREVIEW_CELLS = 6
_PREVIEW_CHARS = 120


def _preview_row(row: list[Any]) -> str:
    """Compact one-line preview of a grid row: first few cells, char-capped."""
    cells = [str(c) for c in row[:_PREVIEW_CELLS]]
    return " | ".join(cells)[:_PREVIEW_CHARS]


def build_continuity_context(activity: list[dict[str, Any]] | None) -> str:
    """Format recent-sheet activity into a compact cross-session continuity block.

    Deterministic "where you left off" context so a fresh session is not blank.
    Only the most-recent sheet carries a last-row preview to keep the block
    small. Empty activity returns an explicit "no record" line so the model
    states that plainly instead of inventing past work (finance-critical).

    Args:
        activity: Rows from SpreadsheetService.recent_activity, most-recent
            first, or None/empty.

    Returns:
        A prompt-ready block; never an empty string.
    """
    if not activity:
        return "No recent sheet activity on record."
    lines: list[str] = []
    for i, item in enumerate(activity):
        title = item.get("title", "?")
        updated = (item.get("updated_at") or "")[:10]  # date only, no raw time
        count = item.get("rows", 0)
        line = f'- "{title}": last edited {updated}, {count} row(s)'
        if i == 0 and item.get("last_row"):
            preview = _preview_row(item["last_row"])
            if preview:
                line += f". Last entry: {preview}"
        lines.append(line)
    return "MOST RECENT SHEET ACTIVITY (most recent first):\n" + "\n".join(lines)


def build_memory_context(memories: list[str] | None) -> str:
    """Format retrieved long-term memories into a prompt block.

    Empty input returns "" so the orchestrator's slot fallback states plainly
    that nothing is remembered (anti-confabulation), rather than inventing.
    Memories are stored in English; Klaudia still replies in the user's
    language.

    Args:
        memories: Memory texts from MemoryService.recall, most-relevant first.

    Returns:
        A prompt-ready block, or "" when there is nothing to surface.
    """
    facts = [m.strip() for m in (memories or []) if m and m.strip()]
    if not facts:
        return ""
    return "\n".join(f"- {fact}" for fact in facts)


def _encode_compact_json(value: Any) -> str:
    """Encode a value as compact UTF-8 JSON."""
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def _serialize_extraction_pages(
    pages: list[dict[str, Any]], output_format: ExtractionContextFormat
) -> tuple[str, str]:
    """Serialize pages and return the format label with the encoded text."""
    if output_format == "json":
        return "JSON", _encode_compact_json(pages)

    try:
        return "TOON", encode_toon(pages)
    except Exception as exc:
        logger.warning(
            "TOON extraction-context encoding failed; using JSON (%s)",
            type(exc).__name__,
        )
        return "JSON", _encode_compact_json(pages)


def build_extraction_context(
    extraction_data: dict[str, Any] | None,
    output_format: ExtractionContextFormat = "toon",
) -> str:
    """Format extraction data for the supervisor.

    Args:
        extraction_data: File metadata and validated page extractions.
        output_format: Prompt-facing format for the page payload.

    Returns:
        A prompt-ready extraction block, or an empty string without data.
    """
    if not extraction_data:
        return ""
    format_label, serialized_pages = _serialize_extraction_pages(
        extraction_data.get("pages", []), output_format
    )
    return (
        f"[Extraction Result]\n"
        f"File: {extraction_data.get('file_name', 'unknown')}\n"
        f"Status: {extraction_data.get('status', 'unknown')}\n"
        f"Summary: {extraction_data.get('summary', 'N/A')}\n"
        f"Data ({format_label}):\n{serialized_pages}"
    )
