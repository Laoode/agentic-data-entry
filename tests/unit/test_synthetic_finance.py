"""The accountant-workload generators are deterministic and their truth matches.

Hermetic: pure Python, no DB, no LLM. These are the guard on the hard bench's
finance cases - if a generator drifts, the amounts baked into the YAML drift with
it and these tests fail before any live run does.

Each model gets three kinds of check: the truth is recomputed from the grids
independently of the generator, the frozen seed-1013 constants are pinned, and
the values a case asserts are proven not to collide as digit substrings (the
bench's `contains_amount` strips separators, so two asserted amounts that nest
would make a wrong answer look right).
"""

import re
from datetime import date

from tests.e2e.synthetic import (
    BRANCH_SHEET,
    build_branch_ledgers,
    build_bulk_ledger,
)
from tests.e2e.synthetic_finance import (
    AR_AS_OF,
    AR_NOT_DUE,
    AR_OVER_90,
    AR_SHEET,
    CLOSE_APPENDS,
    CLOSE_CORRECTED_AMOUNT,
    CLOSE_CORRECTED_STORE,
    CLOSE_DETAIL_SHEET,
    JOURNAL_SHEET,
    PNL_COGS_SHEET,
    PNL_OPEX_SHEET,
    PNL_REVENUE_SHEET,
    TAX_BASE_ONLY_SHEET,
    TAX_SHEET,
    VAT_RATE_PCT,
    WHT_RATE_PCT,
    build_budget_variance_ledger,
    build_journal_ledger,
    build_month_close_ledger,
    build_profit_loss_ledger,
    build_receivables_ledger,
    build_tax_ledger,
)

SEED = 1013


def _no_digit_collision(values: list[int]) -> bool:
    """True when no asserted amount is a digit substring of another.

    `checks.contains_amount` matches digit-normalized substrings, so if 1500000
    nested inside 21500000 a reply stating only the second would satisfy an
    assertion on the first.
    """
    text = [str(v) for v in values]
    return not any(
        a != b and a in b for i, a in enumerate(text) for j, b in enumerate(text) if i != j
    )


# ── Profit and loss ───────────────────────────────────────────────────────────


def _column_total(grid: list[list], col: int) -> int:
    return sum(int(row[col]) for row in grid[1:])


def test_pnl_is_deterministic():
    assert build_profit_loss_ledger(SEED) == build_profit_loss_ledger(SEED)


def test_pnl_totals_match_the_generated_sheets():
    pnl = build_profit_loss_ledger(SEED)
    assert _column_total(pnl.grids[PNL_REVENUE_SHEET], 2) == pnl.revenue_total
    assert _column_total(pnl.grids[PNL_COGS_SHEET], 2) == pnl.cogs_total
    assert _column_total(pnl.grids[PNL_OPEX_SHEET], 2) == pnl.opex_total


def test_pnl_profit_is_revenue_minus_costs():
    pnl = build_profit_loss_ledger(SEED)
    assert pnl.gross_profit == pnl.revenue_total - pnl.cogs_total
    assert pnl.net_profit == pnl.gross_profit - pnl.opex_total
    # Gross and net must differ, or the case cannot tell the two apart.
    assert pnl.gross_profit != pnl.net_profit


def test_pnl_reads_like_a_real_trading_statement():
    pnl = build_profit_loss_ledger(SEED)
    assert 0 < pnl.net_profit < pnl.gross_profit < pnl.revenue_total
    assert 30 <= pnl.gross_margin_pct <= 60


def test_pnl_golden_seed_1013_is_frozen():
    pnl = build_profit_loss_ledger(SEED)
    assert pnl.revenue_total == 303_000_000
    assert pnl.cogs_total == 177_000_000
    assert pnl.opex_total == 51_000_000
    assert pnl.gross_profit == 126_000_000
    assert pnl.net_profit == 75_000_000
    assert pnl.gross_margin_pct == 41.6
    assert pnl.net_margin_pct == 24.8
    assert _no_digit_collision(
        [
            pnl.revenue_total,
            pnl.cogs_total,
            pnl.opex_total,
            pnl.gross_profit,
            pnl.net_profit,
        ]
    )


# ── Tax: VAT and withholding ──────────────────────────────────────────────────


def test_tax_is_deterministic():
    assert build_tax_ledger(SEED) == build_tax_ledger(SEED)


def test_tax_columns_match_the_stated_rates():
    tax = build_tax_ledger(SEED)
    for row in tax.grids[TAX_SHEET][1:]:
        dpp, vat, wht, payable = (int(row[3]), int(row[4]), int(row[5]), int(row[6]))
        assert vat == dpp * VAT_RATE_PCT // 100
        assert wht == dpp * WHT_RATE_PCT // 100
        assert payable == dpp + vat - wht


def test_tax_totals_match_the_columns():
    tax = build_tax_ledger(SEED)
    grid = tax.grids[TAX_SHEET]
    assert _column_total(grid, 3) == tax.dpp_total
    assert _column_total(grid, 4) == tax.vat_total
    assert _column_total(grid, 5) == tax.wht_total
    assert _column_total(grid, 6) == tax.payable_total


def test_tax_base_only_sheet_carries_no_computed_columns():
    """The August sheet holds DPP alone, so its VAT must be computed, not read."""
    tax = build_tax_ledger(SEED)
    grid = tax.grids[TAX_BASE_ONLY_SHEET]
    assert len(grid[0]) == 4
    assert _column_total(grid, 3) == tax.base_only_dpp_total
    assert tax.base_only_vat == tax.base_only_dpp_total * VAT_RATE_PCT // 100


def test_tax_golden_seed_1013_is_frozen():
    tax = build_tax_ledger(SEED)
    assert tax.dpp_total == 54_000_000
    assert tax.vat_total == 5_940_000
    assert tax.wht_total == 1_080_000
    assert tax.payable_total == 58_860_000
    assert tax.base_only_dpp_total == 54_700_000
    assert tax.base_only_vat == 6_017_000
    assert _no_digit_collision(
        [tax.dpp_total, tax.vat_total, tax.wht_total, tax.payable_total]
    )


# ── Receivables aging ─────────────────────────────────────────────────────────


def test_receivables_is_deterministic():
    assert build_receivables_ledger(SEED) == build_receivables_ledger(SEED)


def test_receivables_every_bucket_has_invoices():
    """A case can only ask about a bucket that actually holds rows."""
    ar = build_receivables_ledger(SEED)
    expected = {AR_NOT_DUE, "1-30", "31-60", "61-90", AR_OVER_90}
    assert set(ar.bucket_total) == expected
    assert all(v > 0 for v in ar.bucket_total.values())


def test_receivables_buckets_match_the_due_dates():
    """Recompute every bucket from the grid's own dates, not from the generator."""
    ar = build_receivables_ledger(SEED)
    recomputed: dict[str, int] = {}
    overdue = 0
    for row in ar.grids[AR_SHEET][1:]:
        due = date.fromisoformat(str(row[2]))
        days = (AR_AS_OF - due).days
        amount = int(row[3])
        if days <= 0:
            label = AR_NOT_DUE
        elif days <= 30:
            label = "1-30"
        elif days <= 60:
            label = "31-60"
        elif days <= 90:
            label = "61-90"
        else:
            label = AR_OVER_90
        if days > 0:
            overdue += amount
        recomputed[label] = recomputed.get(label, 0) + amount
    assert recomputed == ar.bucket_total
    assert overdue == ar.overdue_total


def test_receivables_overdue_excludes_not_yet_due():
    ar = build_receivables_ledger(SEED)
    assert ar.overdue_total + ar.not_due_total == sum(ar.bucket_total.values())
    assert ar.not_due_total == ar.bucket_total[AR_NOT_DUE]


def test_receivables_golden_seed_1013_is_frozen():
    ar = build_receivables_ledger(SEED)
    assert ar.bucket_total == {
        AR_NOT_DUE: 52_500_000,
        "1-30": 50_500_000,
        "31-60": 55_500_000,
        "61-90": 32_500_000,
        AR_OVER_90: 43_000_000,
    }
    assert ar.overdue_total == 181_500_000
    assert ar.top_overdue_customer == "CV Fajar Baru"
    assert ar.top_overdue_customer_total == 59_000_000
    assert _no_digit_collision(
        [*ar.bucket_total.values(), ar.overdue_total, ar.top_overdue_customer_total]
    )


def test_receivables_top_customer_is_the_largest_balance_not_the_largest_invoice():
    """The two readings differ, so the case must ask for the customer balance."""
    ar = build_receivables_ledger(SEED)
    assert ar.top_overdue_customer_total == max(ar.overdue_by_customer.values())
    assert sum(ar.overdue_by_customer.values()) == ar.overdue_total
    biggest_invoice = max(
        int(row[3])
        for row in ar.grids[AR_SHEET][1:]
        if (AR_AS_OF - date.fromisoformat(str(row[2]))).days > 0
    )
    assert biggest_invoice != ar.top_overdue_customer_total


# ── Budget variance ───────────────────────────────────────────────────────────


def test_budget_is_deterministic():
    assert build_budget_variance_ledger(SEED) == build_budget_variance_ledger(SEED)


def test_budget_sheets_disagree_on_row_order():
    """The join must be by department name; positional pairing must be wrong."""
    bud = build_budget_variance_ledger(SEED)
    from tests.e2e.synthetic_finance import ACTUAL_SHEET, BUDGET_SHEET

    budget_order = [row[0] for row in bud.grids[BUDGET_SHEET][1:]]
    actual_order = [row[0] for row in bud.grids[ACTUAL_SHEET][1:]]
    assert sorted(budget_order) == sorted(actual_order)
    assert budget_order != actual_order


def test_budget_variance_matches_the_two_sheets():
    bud = build_budget_variance_ledger(SEED)
    for dept, delta in bud.variance.items():
        assert delta == bud.actual[dept] - bud.budget[dept]
    assert bud.total_variance == sum(bud.variance.values())


def test_budget_has_both_overruns_and_savings():
    """Both directions must appear, or 'which department overspent' is trivial."""
    bud = build_budget_variance_ledger(SEED)
    assert any(v > 0 for v in bud.variance.values())
    assert any(v < 0 for v in bud.variance.values())


def test_budget_worst_overrun_is_the_largest_positive_variance():
    bud = build_budget_variance_ledger(SEED)
    assert bud.worst_overrun_amount == max(bud.variance.values())
    assert bud.variance[bud.worst_overrun_department] == bud.worst_overrun_amount


def test_budget_golden_seed_1013_is_frozen():
    bud = build_budget_variance_ledger(SEED)
    assert bud.total_variance == 27_000_000
    assert bud.overrun_count == 4
    assert bud.worst_overrun_department == "Layanan Pelanggan"
    assert bud.worst_overrun_amount == 22_000_000


# ── Journal balance ───────────────────────────────────────────────────────────


def test_journal_is_deterministic():
    assert build_journal_ledger(SEED) == build_journal_ledger(SEED)


def test_journal_totals_match_the_columns():
    jrn = build_journal_ledger(SEED)
    grid = jrn.grids[JOURNAL_SHEET]
    assert _column_total(grid, 3) == jrn.debit_total
    assert _column_total(grid, 4) == jrn.credit_total
    assert jrn.imbalance == jrn.debit_total - jrn.credit_total


def test_journal_has_exactly_one_unbalanced_entry():
    jrn = build_journal_ledger(SEED)
    per_entry: dict[str, int] = {}
    for row in jrn.grids[JOURNAL_SHEET][1:]:
        per_entry[str(row[0])] = per_entry.get(str(row[0]), 0) + int(row[3]) - int(row[4])
    off = {entry: delta for entry, delta in per_entry.items() if delta != 0}
    assert list(off) == [jrn.unbalanced_entry]
    assert off[jrn.unbalanced_entry] == jrn.imbalance


def test_journal_golden_seed_1013_is_frozen():
    jrn = build_journal_ledger(SEED)
    assert jrn.debit_total == 42_500_000
    assert jrn.credit_total == 41_050_000
    assert jrn.imbalance == 1_450_000
    assert jrn.unbalanced_entry == "JU-008"
    assert _no_digit_collision([jrn.debit_total, jrn.credit_total, jrn.imbalance])


# ── Month close: the ten-step workflow ────────────────────────────────────────


def test_month_close_is_deterministic():
    assert build_month_close_ledger(SEED) == build_month_close_ledger(SEED)


def test_month_close_base_matches_the_detail_sheet():
    close = build_month_close_ledger(SEED)
    assert _column_total(close.grids[CLOSE_DETAIL_SHEET], 3) == close.base_total


def test_month_close_end_state_follows_the_appends_and_the_correction():
    close = build_month_close_ledger(SEED)
    appended = sum(amount for _, _, amount in CLOSE_APPENDS)
    original = next(
        amount for store, _, amount in CLOSE_APPENDS if store == CLOSE_CORRECTED_STORE
    )
    assert close.corrected_total == close.base_total + appended
    assert close.final_total == close.corrected_total - original + CLOSE_CORRECTED_AMOUNT


def test_month_close_summary_disagrees_with_the_detail():
    close = build_month_close_ledger(SEED)
    assert close.stated_total != close.final_total
    assert close.discrepancy == close.final_total - close.stated_total


def test_month_close_skipping_the_correction_lands_on_a_different_total():
    """The pre-correction total is the trap a case asserts must NOT appear."""
    close = build_month_close_ledger(SEED)
    assert close.corrected_total != close.final_total


def test_month_close_golden_seed_1013_is_frozen():
    close = build_month_close_ledger(SEED)
    assert close.base_total == 1_796_000
    assert close.base_category_total["Makan"] == 941_000
    assert close.stated_total == 2_224_000
    assert close.corrected_total == 2_506_000
    assert close.final_total == 2_561_000
    assert close.final_makan_total == 1_191_000
    assert close.discrepancy == 337_000
    assert _no_digit_collision(
        [
            close.base_total,
            close.stated_total,
            close.corrected_total,
            close.final_total,
            close.final_makan_total,
            close.discrepancy,
        ]
    )


# ── Bulk: one enterprise-sized sheet ──────────────────────────────────────────


def test_bulk_has_a_thousand_rows_and_matching_truth():
    bulk = build_bulk_ledger(SEED)
    grid = next(iter(bulk.grids.values()))
    assert len(grid) == 1001  # header + 1000 data rows
    assert _column_total(grid, 3) == bulk.all_sheets_total


def test_bulk_golden_seed_1013_is_frozen():
    bulk = build_bulk_ledger(SEED)
    assert bulk.all_sheets_total == 249_842_000
    assert bulk.per_category_total["Makan"] == 61_417_000
    assert _no_digit_collision(
        [bulk.all_sheets_total, *bulk.per_category_total.values()]
    )


# ── Branches: one tenant, two spreadsheets ────────────────────────────────────


def test_branches_share_a_sheet_name_but_not_a_total():
    """Identical sheet names are the point: only the bound spreadsheet decides."""
    branches = build_branch_ledgers(SEED)
    assert len(branches.per_branch) == 2
    for ledger in branches.per_branch.values():
        assert list(ledger.grids) == [BRANCH_SHEET]
    totals = list(branches.branch_total.values())
    assert totals[0] != totals[1]


def test_branches_combined_total_is_unreachable_from_one_scope():
    branches = build_branch_ledgers(SEED)
    assert branches.combined_total == sum(branches.branch_total.values())
    assert _no_digit_collision([*branches.branch_total.values(), branches.combined_total])


def test_branches_golden_seed_1013_is_frozen():
    branches = build_branch_ledgers(SEED)
    assert branches.branch_total == {
        "Toko Jakarta": 2_252_000,
        "Toko Surabaya": 3_157_000,
    }
    assert branches.combined_total == 5_409_000


def test_every_generated_amount_is_a_whole_rupiah():
    """No fractional cells anywhere: exact-match grading depends on integers."""
    grids = {}
    grids.update(build_profit_loss_ledger(SEED).grids)
    grids.update(build_tax_ledger(SEED).grids)
    grids.update(build_receivables_ledger(SEED).grids)
    grids.update(build_budget_variance_ledger(SEED).grids)
    grids.update(build_journal_ledger(SEED).grids)
    for grid in grids.values():
        for row in grid[1:]:
            for cell in row:
                if isinstance(cell, str) and re.fullmatch(r"-?\d+\.\d+", cell):
                    raise AssertionError(f"fractional cell {cell!r}")
                assert not isinstance(cell, float)
