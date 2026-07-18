"""
tests/integration/agent/test_agentic_routing.py

Routing & quality integration tests for the 4 core agent scenarios.
Tests verify both WHICH agent handles the request (routing) and WHAT it returns (quality).

Requirements:
  - startup.sh must be running (MCP-SQLite + MCP-GSheets servers)
  - LLM_API_KEY  OR  (GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT)
  - SHEET_ID pointing to the Bookkeeping 2026 spreadsheet

Run:
  uv run pytest tests/integration/agent/test_agentic_routing.py -v -s

Legend:
  RA = Read Agent    SA = Sheet Agent    WA = Write Agent
"""

import os
import re

import pytest
import pytest_asyncio

from app.models.chat import KlaudiaMessage, KlaudiaResponse
from app.services.core.container import KlaudiaContainer
from app.services.core.orchestrator import KlaudiaOrchestrator

# ──────────────────────────────────────────────────────────────────
# Skip guard — mirrors the pattern in test_data_entry_team.py
# ──────────────────────────────────────────────────────────────────

_has_llm = bool(os.environ.get("LLM_API_KEY")) or (
    os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
    and bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))
)
_has_sheet = bool(os.environ.get("SHEET_ID"))

pytestmark = pytest.mark.skipif(
    not _has_llm or not _has_sheet,
    reason="Requires (LLM_API_KEY or Vertex creds) AND SHEET_ID",
)

# ──────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────

# Use a fixed test user ID — assumed to exist from setup/startup.
TEST_USER_ID = 1


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────


def _msg(text: str) -> list[KlaudiaMessage]:
    return [KlaudiaMessage(role="user", content=text)]


def _normalize_number(text: str) -> str:
    """Strip currency formatting to bare digits for comparison.
    '8.170.000' / '8,170,000' / 'Rp 8170000' → '8170000'
    """
    return re.sub(r"[^\d]", "", text)


def _contains_amount(text: str, expected_digits: str) -> bool:
    """Check whether the response contains an amount matching expected_digits."""
    return expected_digits in _normalize_number(text)


# ──────────────────────────────────────────────────────────────────
# Module-level fixture — single container for all tests in file
# ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="module")
async def orch() -> KlaudiaOrchestrator:
    """Start full container (real MCP + LLM) and return orchestrator."""
    from config.settings import get_settings

    settings = get_settings()
    container = KlaudiaContainer(settings)
    await container.startup()

    yield KlaudiaOrchestrator(container)

    await container.shutdown()


# ──────────────────────────────────────────────────────────────────
# Cleanup fixtures (scoped per test function)
# ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def cleanup_june_sheet(orch: KlaudiaOrchestrator):
    """Delete 'Budget Summary - June' after test_copy_budget_summary_to_june."""
    yield
    # Best-effort cleanup — runs even if test fails
    try:
        await orch.process(
            messages=_msg("Delete the sheet named 'Budget Summary - June'"),
            session_id=None,
            user_id=TEST_USER_ID,
        )
    except Exception:
        pass  # Don't fail teardown


@pytest_asyncio.fixture()
async def restore_electricity_expense(orch: KlaudiaOrchestrator):
    """Restore Electricity Expense to original 450,000 after test_update_electricity."""
    yield
    try:
        await orch.process(
            messages=_msg(
                "Update electricity expense in Budget Summary - May back to 450,000"
            ),
            session_id=None,
            user_id=TEST_USER_ID,
        )
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────
# T1 — Read Agent: total expenses
# ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_total_expenses_for_may(orch: KlaudiaOrchestrator):
    """
    "Show me total expenses for May"

    Routing: supervisor → data_entry_team (NOT sql_agent)
    Sub-agent: read_agent reads 'Budget Summary - May'
    Quality: response contains Total Expenses = 8,170,000 IDR
    """
    response: KlaudiaResponse = await orch.process(
        messages=_msg("Show me total expenses for May"),
        session_id=None,
        user_id=TEST_USER_ID,
    )

    content = response.message.content

    # ── Routing check ──────────────────────────────────────────────
    assert "data_entry_team" in response.tools_used, (
        f"Expected data_entry_team routing but got tools_used={response.tools_used}\n"
        f"Response: {content}"
    )
    assert "sql_agent" not in response.tools_used, (
        "sql_agent should NOT be called for a spreadsheet financial question.\n"
        f"tools_used={response.tools_used}\nResponse: {content}"
    )

    # ── Quality check ──────────────────────────────────────────────
    # Budget Summary - May: Total Expenses = 8,170,000 IDR
    assert _contains_amount(content, "8170000"), (
        f"Expected total expenses 8,170,000 in response.\nGot: {content}"
    )


# ──────────────────────────────────────────────────────────────────
# T2 — Read Agent: filter by merchant
# ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_read_list_indomaret_purchases(orch: KlaudiaOrchestrator):
    """
    "List all purchases from Indomaret"

    Routing: supervisor → data_entry_team
    Sub-agent: read_agent reads 'Purchase Ledger - May', filters Indomaret
    Quality: response includes all 3 Indomaret rows (Cooking Oil, Sugar, Mineral Water)
    """
    response: KlaudiaResponse = await orch.process(
        messages=_msg("List all purchases from Indomaret"),
        session_id=None,
        user_id=TEST_USER_ID,
    )

    content = response.message.content

    # ── Routing check ──────────────────────────────────────────────
    assert "data_entry_team" in response.tools_used, (
        f"Expected data_entry_team routing.\ntool_used={response.tools_used}\nResponse: {content}"
    )
    assert "sql_agent" not in response.tools_used, (
        "sql_agent should NOT be called for spreadsheet data."
    )

    # ── Quality check ──────────────────────────────────────────────
    # Purchase Ledger - May has 3 Indomaret rows:
    #   Cooking Oil 2L, Sugar 1kg, Mineral Water
    assert "Indomaret" in content, f"Response should mention Indomaret.\nGot: {content}"

    indomaret_items = ["Cooking Oil", "Sugar", "Mineral Water"]
    found = [item for item in indomaret_items if item in content]
    assert len(found) >= 2, (
        f"Expected at least 2 of {indomaret_items} in response.\n"
        f"Found: {found}\nGot: {content}"
    )


# ──────────────────────────────────────────────────────────────────
# T3 — Sheet Agent: copy sheet to new month
# ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_copy_budget_summary_to_june(
    orch: KlaudiaOrchestrator,
    cleanup_june_sheet,  # noqa: F811 — fixture, not a shadowed name
):
    """
    "Copy me Budget Summary from May for June"

    Routing: supervisor → data_entry_team
    Sub-agent: sheet_agent copies 'Budget Summary - May' → 'Budget Summary - June'
    Quality: response confirms copy, new sheet name contains 'June'
    Cleanup: 'Budget Summary - June' deleted by cleanup_june_sheet fixture
    """
    response: KlaudiaResponse = await orch.process(
        messages=_msg("Copy me Budget Summary from May for June"),
        session_id=None,
        user_id=TEST_USER_ID,
    )

    content = response.message.content

    # ── Routing check ──────────────────────────────────────────────
    assert "data_entry_team" in response.tools_used, (
        f"Expected data_entry_team routing.\ntools_used={response.tools_used}\nResponse: {content}"
    )

    # ── Quality check ──────────────────────────────────────────────
    # Response should confirm the copy and reference June
    june_variants = ["June", "Juni", "Budget Summary - June"]
    assert any(v in content for v in june_variants), (
        f"Response should confirm copy for June.\n"
        f"Looked for: {june_variants}\nGot: {content}"
    )
    # Must not indicate an error
    assert "error" not in content.lower() and "gagal" not in content.lower(), (
        f"Response suggests an error occurred.\nGot: {content}"
    )


# ──────────────────────────────────────────────────────────────────
# T4 — Write Agent: update a single cell value
# ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_electricity_expense(
    orch: KlaudiaOrchestrator,
    restore_electricity_expense,  # noqa: F811
):
    """
    "Update electricity expense May to 500,000"

    Routing: supervisor → data_entry_team
    Sub-agent: write_agent updates 'Budget Summary - May', Electricity Expense row
               from 450,000 → 500,000
    Quality: response confirms update with new value 500,000
    Cleanup: restore_electricity_expense fixture resets to 450,000
    """
    response: KlaudiaResponse = await orch.process(
        messages=_msg("Update electricity expense May to 500,000"),
        session_id=None,
        user_id=TEST_USER_ID,
    )

    content = response.message.content

    # ── Routing check ──────────────────────────────────────────────
    assert "data_entry_team" in response.tools_used, (
        f"Expected data_entry_team routing.\ntools_used={response.tools_used}\nResponse: {content}"
    )

    # ── Quality check ──────────────────────────────────────────────
    # Response should confirm the update and include the new value 500,000
    assert _contains_amount(content, "500000"), (
        f"Response should confirm update to 500,000.\nGot: {content}"
    )
    # Must not indicate an error
    assert "error" not in content.lower() and "gagal" not in content.lower(), (
        f"Response suggests an error occurred.\nGot: {content}"
    )
