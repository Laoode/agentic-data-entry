import json
import logging
from contextvars import ContextVar, Token
from typing import Any

logger = logging.getLogger(__name__)

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


def build_extraction_context(extraction_data: dict[str, Any] | None) -> str:
    """Format extraction data into a context message."""
    if not extraction_data:
        return ""
    return (
        f"[Extraction Result]\n"
        f"File: {extraction_data.get('file_name', 'unknown')}\n"
        f"Status: {extraction_data.get('status', 'unknown')}\n"
        f"Summary: {extraction_data.get('summary', 'N/A')}\n"
        f"Data:\n{json.dumps(extraction_data.get('pages', []), indent=2, default=str)}"
    )
