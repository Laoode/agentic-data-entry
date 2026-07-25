"""Hermetic tests for the bench's amount assertions.

`excludes_amount` is the negative half of `contains_amount`: it grades a figure
the agent had no legitimate way to reach - another workspace's total, or a sum
its request scope cannot see. Because both sides normalize to digits only, the
separator style of the reply must not change the verdict.
"""

from tests.e2e.checks import ResponseView, evaluate
from tests.e2e.schema import Expect


def _view(content: str) -> ResponseView:
    return ResponseView(content=content, tools_used=["data_entry_team"], latency_ms=1)


def test_excludes_amount_passes_when_the_forbidden_figure_is_absent():
    result = evaluate(
        Expect(contains_amount=["2252000"], excludes_amount=["3157000", "5409000"]),
        _view("Total penjualan Juni di Toko Jakarta adalah Rp2.252.000."),
    )
    assert result.passed
    assert result.detail["excludes_amount"] is True


def test_excludes_amount_fails_when_the_other_workspace_leaks():
    result = evaluate(
        Expect(excludes_amount=["3157000"]),
        _view("Jakarta Rp2.252.000 dan Surabaya Rp3.157.000."),
    )
    assert not result.passed
    assert any("excludes_amount" in r for r in result.reasons)


def test_excludes_amount_ignores_separator_style():
    """'5,409,000' and '5.409.000' are the same claim once digits are isolated."""
    for rendered in ("5.409.000", "5,409,000", "Rp 5409000"):
        result = evaluate(
            Expect(excludes_amount=["5409000"]),
            _view(f"Gabungan keduanya {rendered}."),
        )
        assert not result.passed, rendered


def test_excludes_amount_is_skipped_when_unset():
    result = evaluate(Expect(contains_amount=["2252000"]), _view("Rp2.252.000"))
    assert result.passed
    assert "excludes_amount" not in result.detail


def test_contains_and_excludes_compose_on_one_turn():
    """A right number plus a leaked one still fails: the exclusion is a veto."""
    result = evaluate(
        Expect(contains_amount=["2561000"], excludes_amount=["2506000"]),
        _view("Sebelum koreksi Rp2.506.000, setelah koreksi Rp2.561.000."),
    )
    assert not result.passed
    assert result.detail["contains_amount"] is True
    assert result.detail["excludes_amount"] is False
