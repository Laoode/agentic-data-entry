"""Auth + route-protection integration tests.

Runs the real v1 routers against PostgreSQL through an ASGI test
client. No LLM, MCP, Redis, or MinIO required: chat/sheets routes reject
unauthenticated calls before touching the orchestrator.
"""

from types import SimpleNamespace
from typing import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from app.routes import v1_router


@pytest.fixture
async def client(postgres_db) -> AsyncIterator[httpx.AsyncClient]:
    app = FastAPI()
    app.state.container = SimpleNamespace(db_client=postgres_db)
    app.include_router(v1_router)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as http_client:
        yield http_client


async def _register(client: httpx.AsyncClient, name: str) -> dict:
    resp = await client.post(
        "/v1/auth/register",
        json={
            "username": name,
            "email": f"{name}@example.com",
            "password": "hunter2hunter2",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_register_returns_token(client):
    body = await _register(client, "alice")
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["username"] == "alice"


async def test_register_duplicate_username_conflicts(client):
    await _register(client, "alice")
    resp = await client.post(
        "/v1/auth/register",
        json={
            "username": "alice",
            "email": "other@example.com",
            "password": "hunter2hunter2",
        },
    )
    assert resp.status_code == 409


async def test_register_rejects_short_password(client):
    resp = await client.post(
        "/v1/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "short"},
    )
    assert resp.status_code == 422


async def test_login_roundtrip(client):
    await _register(client, "alice")
    resp = await client.post(
        "/v1/auth/login",
        json={"username": "alice", "password": "hunter2hunter2"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_login_wrong_password_rejected(client):
    await _register(client, "alice")
    resp = await client.post(
        "/v1/auth/login",
        json={"username": "alice", "password": "wrong-password"},
    )
    assert resp.status_code == 401


async def test_login_unknown_user_same_error_as_wrong_password(client):
    resp = await client.post(
        "/v1/auth/login",
        json={"username": "ghost", "password": "whatever123"},
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid username or password"


async def test_dev_seed_user_cannot_login(client):
    """The bootstrap row (user_id=1, 'not-a-real-hash') must fail closed."""
    resp = await client.post(
        "/v1/auth/login",
        json={"username": "dev", "password": "not-a-real-hash"},
    )
    assert resp.status_code == 401


async def test_sessions_requires_auth(client):
    assert (await client.get("/v1/sessions")).status_code == 401


async def test_sessions_rejects_garbage_token(client):
    resp = await client.get(
        "/v1/sessions", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert resp.status_code == 401


async def test_chat_requires_auth(client):
    resp = await client.post(
        "/v1/chat", json={"messages": [{"role": "user", "content": "hi"}]}
    )
    assert resp.status_code == 401


async def test_sheets_requires_auth(client):
    assert (await client.get("/v1/sheets/info")).status_code == 401


async def test_session_isolation_between_users(client):
    """User B must not be able to read user A's session (404, not 403,
    so ids are not enumerable)."""
    alice = await _register(client, "alice")
    bob = await _register(client, "bob")

    db = None
    # Create a session for alice directly in the DB (chat route needs the
    # full orchestrator; session creation is not the behavior under test).
    transport_app = client._transport.app  # httpx.ASGITransport
    db = transport_app.state.container.db_client
    session_id = await db.create_session(alice["user_id"], "alice-private")

    ok = await client.get(
        f"/v1/sessions/{session_id}",
        headers={"Authorization": f"Bearer {alice['access_token']}"},
    )
    assert ok.status_code == 200

    stolen = await client.get(
        f"/v1/sessions/{session_id}",
        headers={"Authorization": f"Bearer {bob['access_token']}"},
    )
    assert stolen.status_code == 404

    listed = await client.get(
        "/v1/sessions",
        headers={"Authorization": f"Bearer {bob['access_token']}"},
    )
    assert listed.status_code == 200
    assert listed.json()["sessions"] == []


async def test_chat_rejects_foreign_session_before_orchestrator(client):
    alice = await _register(client, "alice")
    bob = await _register(client, "bob")
    transport_app = client._transport.app  # httpx.ASGITransport
    session_id = await transport_app.state.container.db_client.create_session(
        alice["user_id"], "alice-private"
    )

    class UnexpectedOrchestrator:
        async def process(self, **kwargs):
            raise AssertionError("foreign session reached orchestrator")

    transport_app.state.orchestrator = UnexpectedOrchestrator()
    response = await client.post(
        "/v1/chat",
        headers={"Authorization": f"Bearer {bob['access_token']}"},
        json={
            "session_id": session_id,
            "messages": [{"role": "user", "content": "show history"}],
        },
    )

    assert response.status_code == 404


async def test_chat_stream_hides_internal_errors(client):
    alice = await _register(client, "alice")
    transport_app = client._transport.app  # httpx.ASGITransport

    class BrokenOrchestrator:
        async def stream(self, **kwargs):
            raise RuntimeError("sensitive-internal-detail")
            yield

    transport_app.state.orchestrator = BrokenOrchestrator()
    transport_app.state.container.spreadsheets = None
    response = await client.post(
        "/v1/chat/stream",
        headers={"Authorization": f"Bearer {alice['access_token']}"},
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 200
    assert "sensitive-internal-detail" not in response.text
    assert "Internal server error" in response.text
