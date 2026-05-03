"""Unit tests for supervisor reply resolution + FINISH-branch message prep.

Regression coverage for the multi-turn bug where a follow-up turn (e.g. user
asks to delete a row after a recap) returned the previous turn's recap text
verbatim. Two cooperating bugs caused that:

1. `_resolve_final_content` walked back across turns when the current
   AIMessage was empty, ending up at a previous-turn AIMessage from history.
2. The supervisor's FINISH branch fed `[WRITE_DONE]`-tagged worker messages
   straight to the final-reply LLM with no instruction, which is what made
   Gemini emit empty content in the first place.

These tests are hermetic — no LLM, no MCP.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from klaudia.core.supervisor._content import strip_internal_markers
from klaudia.core.supervisor.agent import _resolve_final_content
from klaudia.core.supervisor.router import _prepare_finish_messages


@pytest.mark.unit
def test_resolve_falls_back_to_worker_not_previous_turn_ai():
    """Empty trailing AIMessage must NOT promote a previous-turn AIMessage."""
    messages = [
        SystemMessage(content="You are Klaudia."),
        HumanMessage(content="recapkan sheet sari laut"),
        AIMessage(content="Halo! Ini dia rekap isi sari laut: ..."),  # turn-1
        HumanMessage(content="hapus baris nasi padang"),
        HumanMessage(
            content="[WRITE_DONE] Saya sudah hapus baris nasi padang.",
            name="data_entry_team",
        ),
        AIMessage(content=""),  # supervisor produced an empty reply
    ]

    out = _resolve_final_content(messages)

    assert "hapus" in out.lower()
    assert "rekap" not in out.lower(), (
        "Regression: resolved content leaked the previous turn's AIMessage"
    )


@pytest.mark.unit
def test_resolve_returns_last_ai_when_non_empty():
    messages = [
        HumanMessage(content="hi"),
        HumanMessage(content="[WRITE_DONE] done", name="data_entry_team"),
        AIMessage(content="Selesai!"),
    ]
    assert _resolve_final_content(messages) == "Selesai!"


@pytest.mark.unit
def test_resolve_returns_empty_when_no_ai_no_worker():
    messages = [HumanMessage(content="hi")]
    assert _resolve_final_content(messages) == ""


@pytest.mark.unit
def test_strip_internal_markers_keeps_summary():
    """Stripping must preserve the inline summary text next to the marker."""
    assert strip_internal_markers("[WRITE_DONE] Saya hapus.") == "Saya hapus."
    assert strip_internal_markers("Detail.\n[WRITE_DONE] Done") == "Detail.\nDone"
    assert strip_internal_markers("[CLARIFY] Sheet 'X' tidak ada.") == "Sheet 'X' tidak ada."
    assert strip_internal_markers("plain text") == "plain text"
    assert strip_internal_markers("") == ""


@pytest.mark.unit
def test_prepare_finish_strips_markers_and_appends_instruction():
    messages = [
        SystemMessage(content="persona"),
        HumanMessage(content="hapus"),
        HumanMessage(
            content="[WRITE_DONE] Baris terhapus.", name="data_entry_team"
        ),
    ]
    prepped = _prepare_finish_messages(messages)

    # Last message is always the summarization instruction
    assert isinstance(prepped[-1], SystemMessage)
    assert "user-facing reply" in prepped[-1].content.lower()

    # Worker message preserved but marker token stripped
    worker = next(m for m in prepped if getattr(m, "name", None) == "data_entry_team")
    assert "[WRITE_DONE]" not in worker.content
    assert "terhapus" in worker.content


@pytest.mark.unit
def test_prepare_finish_drops_worker_msg_that_is_only_marker():
    messages = [
        HumanMessage(content="hapus"),
        HumanMessage(content="[WRITE_DONE]", name="data_entry_team"),
    ]
    prepped = _prepare_finish_messages(messages)

    workers = [m for m in prepped if getattr(m, "name", None) == "data_entry_team"]
    assert workers == [], (
        "An empty-after-strip worker turn must be dropped, not forwarded as a "
        "blank user turn (which Gemini would treat as silence)."
    )
    assert isinstance(prepped[-1], SystemMessage)
