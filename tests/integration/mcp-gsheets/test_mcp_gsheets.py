"""Integration tests for MCP-GSheets server (requires server running on port 8002)."""

import pytest
import httpx


BASE_URL = "http://localhost:8002"


@pytest.fixture
def client():
    return httpx.Client(timeout=10.0)


def test_mcp_gsheets_server_reachable(client):
    """MCP-GSheets server should accept SSE connections."""
    with client.stream("GET", f"{BASE_URL}/sse") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
