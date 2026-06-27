"""Pytest fixtures for the in-process E2E layer.

A single real container (LLM + MCP stdio servers + DB + object store) is built
once per module and shared across all cases. Requires live credentials and
running infra — the suite skips cleanly when they are absent.
"""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv

# Load the main app .env into the environment so the skip guard and the container
# see the same credentials the app uses. SHEET_ID is intentionally NOT required
# here: it lives in mcp-gsheets/.env and is loaded by the MCP server in its own
# cwd, so the parent process never needs it.
load_dotenv()


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "mutating: case mutates the real Google Sheet (deselect with -m 'not mutating')"
    )
    config.addinivalue_line(
        "markers", "e2e: Klaudia whitebox end-to-end case"
    )

# ── Skip guard: the in-process layer needs real LLM credentials ──────────────
# Any one of: Gemini Developer key, Vertex (use_vertexai + project), or DeepSeek.
_has_llm = (
    bool(os.environ.get("LLM_API_KEY"))
    or bool(os.environ.get("DEEPSEEK_API_KEY"))
    or (
        os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        and bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))
    )
)

requires_live = pytest.mark.skipif(
    not _has_llm,
    reason="E2E in-process layer needs LLM credentials (LLM_API_KEY / DEEPSEEK_API_KEY / Vertex)",
)


# loop_scope="module" is REQUIRED: the container's MCP stdio sessions and their
# background tasks are bound to the loop that creates the fixture. The tests must
# run on that SAME loop or every MCP call (e.g. tool_list_sheets in
# get_available_sheets, fired each non-rejected turn) awaits across event loops
# and deadlocks. Tests therefore use @pytest.mark.asyncio(loop_scope="module").
@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def container():
    """Build the real KlaudiaContainer once for the module."""
    from app.services.core.container import KlaudiaContainer
    from config.settings import get_settings

    c = await KlaudiaContainer.create(get_settings())
    yield c
    await c.shutdown()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def orchestrator(container):
    from app.services.core.orchestrator import KlaudiaOrchestrator

    return KlaudiaOrchestrator(container)


@pytest.fixture(scope="module")
def spy(container):
    from tests.e2e.spy import MCPSpy

    return MCPSpy([container.mcp_sqlite, container.mcp_gsheets])
