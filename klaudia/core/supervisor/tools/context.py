import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


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
