"""Unit tests for the SHEETS_BACKEND registry toggle."""

import pytest

from app.services.core.container import _build_mcp_registries
from config.settings import Settings


def test_default_backend_is_gsheets():
    sqlite_reg, sheets_reg = _build_mcp_registries(Settings())
    assert sqlite_reg._name == "mcp-sqlite"
    assert sheets_reg._name == "mcp-gsheets"


def test_ledger_backend_selected():
    settings = Settings(
        SHEETS_BACKEND="ledger",
        DATABASE_URL="postgresql://x:x@localhost:5432/x",
    )
    _sqlite_reg, sheets_reg = _build_mcp_registries(settings)
    assert sheets_reg._name == "mcp-ledger"


def test_ledger_backend_requires_database_url():
    settings = Settings(SHEETS_BACKEND="ledger", DATABASE_URL="")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        _build_mcp_registries(settings)


def test_ledger_backend_sse_ports():
    settings = Settings(
        SHEETS_BACKEND="ledger",
        DATABASE_URL="postgresql://x:x@localhost:5432/x",
        MCP_TRANSPORT="sse",
    )
    _sqlite_reg, sheets_reg = _build_mcp_registries(settings)
    assert sheets_reg._name == "mcp-ledger"
