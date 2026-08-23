"""Unit tests for the SHEETS_BACKEND registry toggle.

Ledger is the backend in use (see .env: SHEETS_BACKEND=ledger). gsheets is the
legacy path, still selectable when explicitly configured. The archive/SQL
registry is mcp-archive under either backend. Every case passes settings
explicitly so the result never depends on the developer's .env.
"""

import pytest

from app.services.core.container import _build_mcp_registries, _legacy_sse_url
from config.settings import Settings

_LEDGER = dict(
    SHEETS_BACKEND="ledger",
    DATABASE_URL="postgresql://x:x@localhost:5432/x",
)


def test_ledger_is_the_default_backend():
    settings = Settings(_env_file=None)
    assert settings.sheets_backend == "ledger"


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
    """Legacy mode derives /sse from the configured remote URL."""
    settings = Settings(**_LEDGER, MCP_TRANSPORT="sse")
    sqlite_reg, sheets_reg = _build_mcp_registries(settings)
    assert sheets_reg._name == "mcp-ledger"
    assert sqlite_reg._url == "http://localhost:8001/sse"
    assert sheets_reg._url == "http://localhost:8003/sse"


def test_http_backend_uses_configured_urls_and_token():
    """Remote MCP settings flow into both active FastMCP clients."""
    settings = Settings(
        **_LEDGER,
        MCP_TRANSPORT="http",
        MCP_ARCHIVE_URL="https://mcp.example/archive/mcp",
        MCP_LEDGER_URL="https://mcp.example/ledger/mcp",
        MCP_AUTH_TOKEN="signed-token",
    )

    archive_reg, ledger_reg = _build_mcp_registries(settings)

    assert archive_reg._url == "https://mcp.example/archive/mcp"
    assert ledger_reg._url == "https://mcp.example/ledger/mcp"
    assert archive_reg._auth_token == "signed-token"
    assert ledger_reg._auth_token == "signed-token"


def test_legacy_sse_url_keeps_explicit_sse_path():
    """An operator-supplied legacy URL is not rewritten twice."""
    assert _legacy_sse_url("https://mcp.example/sse/") == "https://mcp.example/sse"
