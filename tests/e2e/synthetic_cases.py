"""Registry mapping each synthetic hard-bench category to its data and tenant.

One place decides which categories the synthetic runner seeds and, by the same
token, which ones the main bench must skip. Both runners import from here, so
adding a category cannot leave the main bench trying to run it against a
spreadsheet nobody seeded.

Every category owns a scratch user id, so its ledger never collides with another
category's or with the docs/TABLE.md baseline on the main test user.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

from tests.e2e.synthetic import (
    build_aggregation_ledger,
    build_branch_ledgers,
    build_bulk_ledger,
    build_compound_ledger,
    build_dirty_ledger,
    build_distractor_ledger,
    build_hostile_schema_ledger,
    build_injection_ledger,
    build_missing_value_ledger,
    build_reconciliation_ledger,
    build_scale_ledger,
)
from tests.e2e.synthetic_finance import (
    build_budget_variance_ledger,
    build_journal_ledger,
    build_month_close_ledger,
    build_profit_loss_ledger,
    build_receivables_ledger,
    build_tax_ledger,
)

SEED = 1013


class GridLedger(Protocol):
    """What the seeder needs from any generated ledger."""

    grids: dict[str, list[list[Any]]]


# category -> (scratch user id, builder). The builder takes the seed and returns
# an object exposing `.grids`; the runner materializes those grids into that
# user's default spreadsheet.
SYNTHETIC_SEEDS: dict[str, tuple[int, Callable[..., GridLedger]]] = {
    "aggregation": (90100, build_aggregation_ledger),
    "dirty_data": (90101, build_dirty_ledger),
    "distractor_column": (90102, build_distractor_ledger),
    "find_missing": (90103, build_missing_value_ledger),
    "scale": (90104, build_scale_ledger),
    "reconciliation": (90105, build_reconciliation_ledger),
    "injection_in_data": (90106, build_injection_ledger),
    "compound": (90107, build_compound_ledger),
    "hostile_schema": (90108, build_hostile_schema_ledger),
    "profit_loss": (90109, build_profit_loss_ledger),
    "tax": (90110, build_tax_ledger),
    "receivables": (90111, build_receivables_ledger),
    "budget_variance": (90112, build_budget_variance_ledger),
    "journal_balance": (90113, build_journal_ledger),
    "bulk_scale": (90114, build_bulk_ledger),
    "month_close": (90116, build_month_close_ledger),
}

# Multi-spreadsheet is seeded differently: one user owning several spreadsheets,
# each holding an identically named sheet, so it gets its own path in the runner.
BRANCH_CATEGORY = "multi_spreadsheet"
BRANCH_USER = 90115
BRANCH_BUILDER = build_branch_ledgers

# Every category the synthetic runner owns. The main bench (test_e2e_dataset.py)
# skips exactly this set.
SYNTHETIC_CATEGORIES: frozenset[str] = frozenset(SYNTHETIC_SEEDS) | {BRANCH_CATEGORY}
