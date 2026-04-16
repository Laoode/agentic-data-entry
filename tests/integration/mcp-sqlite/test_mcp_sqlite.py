"""Integration tests for MCP-SQLite server (requires server running on port 8001)."""

import pytest
import httpx


BASE_URL = "http://localhost:8001"


@pytest.fixture
def client():
    return httpx.Client(timeout=10.0)


def test_mcp_sqlite_server_reachable(client):
    """MCP-SQLite server should accept SSE connections."""
    with client.stream("GET", f"{BASE_URL}/sse") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
