"""Deterministic accountant-workload ledgers for the hard E2E bench.

Same generate-then-freeze discipline as `synthetic.py`: a fixed seed yields the
same grids and the same code-computed truth on every run, so a case bakes exact
amounts into YAML while the generator reproduces the data the seeder writes.

Where `synthetic.py` models a personal expense book, this module models what an
enterprise accountant actually does: read a profit and loss statement, settle
VAT and withholding tax, age receivables, explain budget variance, and prove a
journal balances. Every case here has a closed-form answer, so the numeric
verifier and `contains_amount` grade it exactly and no judge is involved.

Amounts are chosen so derived figures stay whole rupiah: tax bases are multiples
of 100_000, which makes 11% VAT and 2% withholding exact integers.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

# Every generated sheet writes plain integer amounts. Messy number formats are
# already covered by `synthetic.py`'s dirty ledger; holding format constant here
# keeps a failure attributable to the finance reasoning, not to parsing.

VAT_RATE_PCT = 11  # PPN, Indonesian value-added tax
WHT_RATE_PCT = 2  # PPh 23, withholding on services
_TAX_UNIT = 100_000  # tax bases are multiples of this, so both rates stay whole


def _pct(part: int, whole: int) -> float:
    """Percentage of `part` in `whole`, one decimal, 0.0 when `whole` is 0."""
    return round(part / whole * 100, 1) if whole else 0.0


# ── Profit and loss: revenue, cost of goods sold, operating expense ───────────

PNL_HEADER: list[str] = ["Tanggal", "Keterangan", "Nominal"]
PNL_REVENUE_SHEET = "Pendapatan"
PNL_COGS_SHEET = "HPP"
PNL_OPEX_SHEET = "Beban Operasional"

_REVENUE_ITEMS = (
    "Penjualan retail",
    "Penjualan grosir",
    "Jasa instalasi",
    "Kontrak maintenance",
    "Penjualan online",
)
_COGS_ITEMS = (
    "Pembelian barang dagang",
    "Ongkos kirim masuk",
    "Bahan baku",
    "Upah produksi",
)
_OPEX_ITEMS = (
    "Gaji karyawan",
    "Sewa kantor",
    "Listrik dan air",
    "Internet",
    "Perlengkapan kantor",
    "Biaya pemasaran",
)


@dataclass(frozen=True)
class ProfitLossLedger:
    """Three statement sheets and the profit figures derived from them.

    `gross_profit` needs one cross-sheet subtraction; `net_profit` needs two, and
    is the figure an agent most often conflates with gross profit.
    """

    grids: dict[str, list[list[str | int]]]
    revenue_total: int
    cogs_total: int
    opex_total: int
    gross_profit: int
    net_profit: int
    gross_margin_pct: float
    net_margin_pct: float


def _statement_rows(
    rng: random.Random,
    items: tuple[str, ...],
    count: int,
    low_juta: int,
    high_juta: int,
) -> tuple[list[list[str | int]], int]:
    """Dated line items in whole millions of rupiah, plus their total."""
    rows: list[list[str | int]] = [list(PNL_HEADER)]
    total = 0
    for _ in range(count):
        day = rng.randint(1, 28)
        amount = rng.randint(low_juta, high_juta) * 1_000_000
        rows.append([f"2026-06-{day:02d}", rng.choice(items), amount])
        total += amount
    return rows, total


def build_profit_loss_ledger(seed: int) -> ProfitLossLedger:
    """Revenue, COGS and opex sheets whose profit figures are code-computed."""
    rng = random.Random(seed)
    # Ranges are sized so the statement reads like a real trading company:
    # COGS lands near 60% of revenue and net margin in the low teens.
    revenue_rows, revenue_total = _statement_rows(rng, _REVENUE_ITEMS, 10, 12, 40)
    cogs_rows, cogs_total = _statement_rows(rng, _COGS_ITEMS, 8, 14, 28)
    opex_rows, opex_total = _statement_rows(rng, _OPEX_ITEMS, 9, 3, 9)

    gross_profit = revenue_total - cogs_total
    net_profit = gross_profit - opex_total
    return ProfitLossLedger(
        grids={
            PNL_REVENUE_SHEET: revenue_rows,
            PNL_COGS_SHEET: cogs_rows,
            PNL_OPEX_SHEET: opex_rows,
        },
        revenue_total=revenue_total,
        cogs_total=cogs_total,
        opex_total=opex_total,
        gross_profit=gross_profit,
        net_profit=net_profit,
        gross_margin_pct=_pct(gross_profit, revenue_total),
        net_margin_pct=_pct(net_profit, revenue_total),
    )


# ── Tax: PPN 11% output tax and PPh 23 withholding on vendor invoices ─────────

TAX_HEADER: list[str] = [
    "No Faktur",
    "Tanggal",
    "Vendor",
    "DPP",
    "PPN 11%",
    "PPh 23",
    "Total Bayar",
]
TAX_SHEET = "Faktur Juli"
# Same vendors, no tax columns: the agent must compute the rates, not read them.
TAX_BASE_ONLY_HEADER: list[str] = ["No Faktur", "Tanggal", "Vendor", "DPP"]
TAX_BASE_ONLY_SHEET = "Faktur Agustus"

_VENDORS = (
    "CV Mitra Sejahtera",
    "PT Sinar Abadi",
    "UD Karya Mandiri",
    "PT Logistik Nusantara",
    "CV Sumber Rejeki",
)


@dataclass(frozen=True)
class TaxLedger:
    """Vendor invoices with VAT and withholding, plus a base-only sheet.

    `payable_total` is DPP + PPN - PPh: the amount actually transferred. Summing
    the DPP column, or the PPN column, or ignoring the withholding, each lands on
    a different number, so the traps are distinguishable.
    """

    grids: dict[str, list[list[str | int]]]
    dpp_total: int
    vat_total: int
    wht_total: int
    payable_total: int
    base_only_dpp_total: int
    base_only_vat: int
    base_only_wht: int


def build_tax_ledger(seed: int, rows: int = 12, base_only_rows: int = 9) -> TaxLedger:
    """Invoice lines whose VAT, withholding and net payable are exact integers."""
    rng = random.Random(seed)
    grid: list[list[str | int]] = [list(TAX_HEADER)]
    dpp_total = vat_total = wht_total = payable_total = 0
    for i in range(rows):
        dpp = rng.randint(15, 90) * _TAX_UNIT
        vat = dpp * VAT_RATE_PCT // 100
        wht = dpp * WHT_RATE_PCT // 100
        payable = dpp + vat - wht
        grid.append(
            [
                f"FK-2607-{i + 1:03d}",
                f"2026-07-{rng.randint(1, 28):02d}",
                rng.choice(_VENDORS),
                dpp,
                vat,
                wht,
                payable,
            ]
        )
        dpp_total += dpp
        vat_total += vat
        wht_total += wht
        payable_total += payable

    base_grid: list[list[str | int]] = [list(TAX_BASE_ONLY_HEADER)]
    base_dpp_total = 0
    for i in range(base_only_rows):
        dpp = rng.randint(15, 90) * _TAX_UNIT
        base_grid.append(
            [
                f"FK-2608-{i + 1:03d}",
                f"2026-08-{rng.randint(1, 28):02d}",
                rng.choice(_VENDORS),
                dpp,
            ]
        )
        base_dpp_total += dpp

    return TaxLedger(
        grids={TAX_SHEET: grid, TAX_BASE_ONLY_SHEET: base_grid},
        dpp_total=dpp_total,
        vat_total=vat_total,
        wht_total=wht_total,
        payable_total=payable_total,
        base_only_dpp_total=base_dpp_total,
        base_only_vat=base_dpp_total * VAT_RATE_PCT // 100,
        base_only_wht=base_dpp_total * WHT_RATE_PCT // 100,
    )


# ── Receivables aging: bucket open invoices by how long they are overdue ──────

AR_HEADER: list[str] = ["No Invoice", "Pelanggan", "Jatuh Tempo", "Nominal"]
AR_SHEET = "Piutang Usaha"
# Fixed reference date, aligned with the suite's frozen "now" (E2E_FREEZE_NOW),
# so bucket membership never depends on when the bench runs.
AR_AS_OF = date(2026, 6, 30)
# Upper day bound of each aging bucket, in the order accountants report them.
AR_BUCKETS: tuple[tuple[str, int], ...] = (
    ("1-30", 30),
    ("31-60", 60),
    ("61-90", 90),
)
AR_OVER_90 = ">90"
AR_NOT_DUE = "belum jatuh tempo"

_CUSTOMERS = (
    "PT Andalan Jaya",
    "CV Bintang Terang",
    "PT Cahaya Mandiri",
    "UD Damai Sentosa",
    "PT Eka Prima",
    "CV Fajar Baru",
)


@dataclass(frozen=True)
class ReceivablesLedger:
    """Open invoices with a due date, bucketed by days past `AR_AS_OF`.

    Bucketing needs date arithmetic per row before any summing, which is why this
    separates an agent that computes from one that pattern-matches amounts.
    """

    grids: dict[str, list[list[str | int]]]
    bucket_total: dict[str, int]
    overdue_total: int
    not_due_total: int
    # Overdue balance per customer, and the customer owing the most. A case must
    # ask for the customer balance, not "the largest overdue", because the
    # biggest single invoice and the biggest customer balance are different
    # numbers and an ambiguous question cannot be graded exactly.
    overdue_by_customer: dict[str, int]
    top_overdue_customer: str
    top_overdue_customer_total: int


def _bucket(days_overdue: int) -> str:
    """Aging bucket label for a row that is `days_overdue` days past due."""
    if days_overdue <= 0:
        return AR_NOT_DUE
    for label, upper in AR_BUCKETS:
        if days_overdue <= upper:
            return label
    return AR_OVER_90


# Day-offset band per bucket, cycled across rows so no bucket comes out empty.
# Negative days mean the invoice is not due yet.
_AR_BANDS: tuple[tuple[int, int], ...] = (
    (-45, -1),
    (1, 30),
    (31, 60),
    (61, 90),
    (91, 140),
)


def build_receivables_ledger(seed: int, rows: int = 16) -> ReceivablesLedger:
    """Invoices spread across every aging bucket, with per-bucket totals."""
    rng = random.Random(seed)
    grid: list[list[str | int]] = [list(AR_HEADER)]
    bucket_total: dict[str, int] = {}
    overdue_by_customer: dict[str, int] = {}
    overdue_total = 0
    not_due_total = 0

    for i in range(rows):
        # Cycling the bands guarantees every bucket has invoices, so a case can
        # ask about any one of them and still have a non-trivial answer.
        low, high = _AR_BANDS[i % len(_AR_BANDS)]
        days_overdue = rng.randint(low, high)
        due = AR_AS_OF - timedelta(days=days_overdue)
        customer = rng.choice(_CUSTOMERS)
        amount = rng.randint(3, 60) * 500_000
        grid.append([f"INV-26-{i + 1:03d}", customer, due.isoformat(), amount])

        label = _bucket(days_overdue)
        bucket_total[label] = bucket_total.get(label, 0) + amount
        if days_overdue > 0:
            overdue_total += amount
            overdue_by_customer[customer] = (
                overdue_by_customer.get(customer, 0) + amount
            )
        else:
            not_due_total += amount

    top_customer = max(overdue_by_customer, key=lambda c: overdue_by_customer[c])
    return ReceivablesLedger(
        grids={AR_SHEET: grid},
        bucket_total=bucket_total,
        overdue_total=overdue_total,
        not_due_total=not_due_total,
        overdue_by_customer=overdue_by_customer,
        top_overdue_customer=top_customer,
        top_overdue_customer_total=overdue_by_customer[top_customer],
    )


# ── Budget variance: two sheets joined by department name, not row order ──────

BUDGET_HEADER: list[str] = ["Departemen", "Anggaran"]
ACTUAL_HEADER: list[str] = ["Departemen", "Realisasi"]
BUDGET_SHEET = "Anggaran 2026"
ACTUAL_SHEET = "Realisasi 2026"

_DEPARTMENTS = (
    "Produksi",
    "Pemasaran",
    "Keuangan",
    "SDM",
    "Logistik",
    "Teknologi",
    "Layanan Pelanggan",
    "Umum",
)


@dataclass(frozen=True)
class BudgetVarianceLedger:
    """Budget and actual per department, with the actual sheet reordered.

    The row order differs between the two sheets, so an agent that pairs rows by
    position instead of by department name computes the wrong variance for
    everyone. `overrun_count` and `worst_overrun_*` give a ranking answer that a
    positional pairing cannot reach by luck.
    """

    grids: dict[str, list[list[str | int]]]
    budget: dict[str, int]
    actual: dict[str, int]
    variance: dict[str, int]
    total_variance: int
    overrun_count: int
    worst_overrun_department: str
    worst_overrun_amount: int


def build_budget_variance_ledger(seed: int) -> BudgetVarianceLedger:
    """Per-department budget vs actual whose sheets disagree on row order."""
    rng = random.Random(seed)
    budget: dict[str, int] = {}
    actual: dict[str, int] = {}
    for dept in _DEPARTMENTS:
        planned = rng.randint(20, 120) * 1_000_000
        # Swing both ways so the answer is not "every department overspent".
        spent = planned + rng.randint(-18, 24) * 1_000_000
        budget[dept] = planned
        actual[dept] = spent

    budget_rows: list[list[str | int]] = [list(BUDGET_HEADER)]
    budget_rows.extend([dept, budget[dept]] for dept in _DEPARTMENTS)

    shuffled = list(_DEPARTMENTS)
    rng.shuffle(shuffled)
    actual_rows: list[list[str | int]] = [list(ACTUAL_HEADER)]
    actual_rows.extend([dept, actual[dept]] for dept in shuffled)

    variance = {dept: actual[dept] - budget[dept] for dept in _DEPARTMENTS}
    overruns = {d: v for d, v in variance.items() if v > 0}
    worst = max(overruns, key=lambda d: overruns[d])

    return BudgetVarianceLedger(
        grids={BUDGET_SHEET: budget_rows, ACTUAL_SHEET: actual_rows},
        budget=budget,
        actual=actual,
        variance=variance,
        total_variance=sum(variance.values()),
        overrun_count=len(overruns),
        worst_overrun_department=worst,
        worst_overrun_amount=overruns[worst],
    )


# ── Journal: double-entry lines where exactly one entry does not balance ──────

JOURNAL_HEADER: list[str] = ["No Jurnal", "Tanggal", "Akun", "Debit", "Kredit"]
JOURNAL_SHEET = "Jurnal Umum"
# The credit shortfall planted in one entry. Distinct from any single amount, so
# naming the difference is only possible by actually comparing the two columns.
_JOURNAL_ERROR = 1_450_000

_DEBIT_ACCOUNTS = ("Kas", "Piutang Usaha", "Persediaan", "Beban Sewa", "Peralatan")
_CREDIT_ACCOUNTS = ("Pendapatan", "Utang Usaha", "Modal", "Utang Bank")


@dataclass(frozen=True)
class JournalLedger:
    """Double-entry journal lines with one deliberately unbalanced entry.

    A correct answer names `unbalanced_entry` and states `imbalance` exactly;
    stating only "it does not balance" is not enough to pass.
    """

    grids: dict[str, list[list[str | int]]]
    debit_total: int
    credit_total: int
    imbalance: int
    unbalanced_entry: str


def build_journal_ledger(seed: int, entries: int = 10) -> JournalLedger:
    """Balanced debit/credit pairs, except one entry short on the credit side."""
    rng = random.Random(seed)
    grid: list[list[str | int]] = [list(JOURNAL_HEADER)]
    debit_total = credit_total = 0
    bad_index = rng.randrange(entries)
    unbalanced_entry = ""

    for i in range(entries):
        entry_id = f"JU-{i + 1:03d}"
        when = f"2026-06-{rng.randint(1, 28):02d}"
        amount = rng.randint(4, 45) * 250_000
        credit = amount - _JOURNAL_ERROR if i == bad_index else amount
        if i == bad_index:
            unbalanced_entry = entry_id
        grid.append([entry_id, when, rng.choice(_DEBIT_ACCOUNTS), amount, 0])
        grid.append([entry_id, when, rng.choice(_CREDIT_ACCOUNTS), 0, credit])
        debit_total += amount
        credit_total += credit

    return JournalLedger(
        grids={JOURNAL_SHEET: grid},
        debit_total=debit_total,
        credit_total=credit_total,
        imbalance=debit_total - credit_total,
        unbalanced_entry=unbalanced_entry,
    )


# ── Month close: the ten-step workflow an accountant runs at period end ───────

CLOSE_HEADER: list[str] = ["Tanggal", "Toko", "Kategori", "Jumlah"]
CLOSE_DETAIL_SHEET = "Kas Juli"
CLOSE_SUMMARY_SHEET = "Rangkuman Juli"
CLOSE_STORES = ("Indomaret", "Alfamart", "GoFood", "Warung Padang", "Shopee", "Grab")
CLOSE_CATEGORIES = ("Belanja", "Makan", "Transport")

# The three entries the case appends, in order, and the correction applied to the
# second one. Holding them here (not only in the YAML prose) means the end-state
# truth is code-computed from the same constants the case asks for.
CLOSE_APPENDS: tuple[tuple[str, str, int], ...] = (
    ("GoFood", "Makan", 250_000),
    ("Grab", "Transport", 120_000),
    ("Shopee", "Belanja", 340_000),
)
CLOSE_CORRECTED_STORE = "Grab"
CLOSE_CORRECTED_AMOUNT = 175_000
# How far the stale summary sheet overstates the detail before it is repaired.
_CLOSE_SUMMARY_ERROR = 428_000


@dataclass(frozen=True)
class MonthCloseLedger:
    """A detail sheet, a stale summary, and the end state after a full close.

    The case appends three entries, corrects one, re-aggregates, reconciles
    against the summary and repairs it. Every intermediate figure is exposed so a
    ten-turn case can grade each step on its own and localize where it broke,
    rather than only scoring the final number.
    """

    grids: dict[str, list[list[str | int]]]
    base_total: int
    base_category_total: dict[str, int]
    stated_total: int
    corrected_total: int
    final_total: int
    final_makan_total: int
    discrepancy: int


def build_month_close_ledger(seed: int, rows: int = 10) -> MonthCloseLedger:
    """Detail rows plus a summary that disagrees, and the post-close truth."""
    rng = random.Random(seed)
    grid: list[list[str | int]] = [list(CLOSE_HEADER)]
    base_total = 0
    base_category_total: dict[str, int] = {}
    for _ in range(rows):
        day = rng.randint(1, 28)
        category = rng.choice(CLOSE_CATEGORIES)
        amount = rng.randint(20, 400) * 1_000
        grid.append([f"2026-07-{day:02d}", rng.choice(CLOSE_STORES), category, amount])
        base_total += amount
        base_category_total[category] = base_category_total.get(category, 0) + amount

    appended = sum(amount for _, _, amount in CLOSE_APPENDS)
    corrected_delta = CLOSE_CORRECTED_AMOUNT - next(
        amount for store, _, amount in CLOSE_APPENDS if store == CLOSE_CORRECTED_STORE
    )
    corrected_total = base_total + appended
    final_total = corrected_total + corrected_delta
    final_makan = base_category_total.get("Makan", 0) + sum(
        amount for _, category, amount in CLOSE_APPENDS if category == "Makan"
    )

    stated_total = base_total + _CLOSE_SUMMARY_ERROR
    summary: list[list[str | int]] = [["Bulan", "Total"], ["Juli", stated_total]]

    return MonthCloseLedger(
        grids={CLOSE_DETAIL_SHEET: grid, CLOSE_SUMMARY_SHEET: summary},
        base_total=base_total,
        base_category_total=base_category_total,
        stated_total=stated_total,
        corrected_total=corrected_total,
        final_total=final_total,
        final_makan_total=final_makan,
        discrepancy=final_total - stated_total,
    )
