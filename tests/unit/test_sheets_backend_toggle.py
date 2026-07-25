"""Unit tests for the SHEETS_BACKEND registry toggle.

Ledger is the backend in use (see .env: SHEETS_BACKEND=ledger). gsheets is the
legacy path, still selectable when explicitly configured. The archive/SQL
registry is mcp-archive under either backend. Every case passes settings
explicitly so the result never depends on the developer's .env.
"""

import pytest

from app.services.core.container import _build_mcp_registries
from config.settings import Settings

_LEDGER = dict(
    SHEETS_BACKEND="ledger",
    DATABASE_URL="postgresql://x:x@localhost:5432/x",
)


def test_archive_registry_is_mcp_archive():
    sqlite_reg, _sheets_reg = _build_mcp_registries(Settings(**_LEDGER))
    assert sqlite_reg._name == "mcp-archive"


def test_ledger_backend_selected():
    _sqlite_reg, sheets_reg = _build_mcp_registries(Settings(**_LEDGER))
    assert sheets_reg._name == "mcp-ledger"


def test_gsheets_backend_is_legacy_opt_in():
    _sqlite_reg, sheets_reg = _build_mcp_registries(Settings(SHEETS_BACKEND="gsheets"))
    assert sheets_reg._name == "mcp-gsheets"


def test_ledger_backend_requires_database_url():
    settings = Settings(SHEETS_BACKEND="ledger", DATABASE_URL="")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        _build_mcp_registries(settings)


def test_ledger_backend_sse_ports():
    settings = Settings(**_LEDGER, MCP_TRANSPORT="sse")
    _sqlite_reg, sheets_reg = _build_mcp_registries(settings)
    assert sheets_reg._name == "mcp-ledger"
