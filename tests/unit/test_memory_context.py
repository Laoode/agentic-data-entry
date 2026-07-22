"""Unit tests for the long-term-memory prompt block builder."""

from klaudia.core.supervisor.tools.context import build_memory_context


def test_empty_or_none_returns_blank():
    assert build_memory_context([]) == ""
    assert build_memory_context(None) == ""


def test_blank_facts_are_filtered_out():
    assert build_memory_context(["   ", ""]) == ""


def test_formats_facts_as_bullets_in_order():
    out = build_memory_context(["Fact A", "Fact B"])
    assert out == "- Fact A\n- Fact B"
