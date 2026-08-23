"""End-to-end MCP server test across both DB backends.

Spawns the real mcp-archive server as a stdio subprocess (exactly how the
app container runs it) and drives document/page/extraction tools through
a FastMCP client. Parametrized over sqlite (temp file) and postgres
(compose instance; skipped when unreachable).
"""

import asyncio
import datetime
import json
import os
import socket
import sys
import tempfile
from pathlib import Path

import jwt
import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.shared.exceptions import MCPError

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SERVER_DIR = _PROJECT_ROOT / "mcp-archive"
_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql://klaudia:klaudia@localhost:5432/klaudia"
)

EXPECTED_TOOL_COUNT = 11
_HTTP_SECRET = "integration-mcp-secret-with-at-least-32-bytes"


async def _pg_available() -> bool:
    import asyncpg

    try:
        conn = await asyncpg.connect(_PG_URL, timeout=3)
        await conn.close()
        return True
    except Exception:
        return False


async def _seed_pg_session() -> int:
    """Create schema prerequisites: wipe public tables, seed user+session."""
    import asyncpg

    conn = await asyncpg.connect(_PG_URL)
    try:
        for table in ("pages", "metadata_file", "conversation", "session"):
            await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        await conn.execute('DROP TABLE IF EXISTS "user" CASCADE')
        # Server recreates schema on connect; pre-create user+session here
        # is impossible before boot, so instead let the server boot first.
    finally:
        await conn.close()
    return 0


def _server_transport(env_overrides: dict[str, str]) -> StdioTransport:
    env = {**os.environ, **env_overrides}
    return StdioTransport(
        command=sys.executable,
        args=["main.py", "--transport", "stdio"],
        cwd=str(_SERVER_DIR),
        env=env,
    )


async def _call(client: Client, tool: str, args: dict) -> dict | list:
    result = await client.call_tool(tool, args, raise_on_error=False)
    text = "".join(c.text for c in result.content if getattr(c, "text", None))
    return json.loads(text)


async def _wait_for_port(process, port: int) -> None:
    """Wait until an HTTP subprocess accepts a local connection.

    Args:
        process: Asyncio subprocess running the MCP server.
        port: Local TCP port selected for the test.

    Raises:
        RuntimeError: If the process exits before opening the port.
        TimeoutError: If the server does not start within five seconds.
    """
    for _ in range(50):
        if process.returncode is not None:
            _stdout, stderr = await process.communicate()
            message = stderr.decode(errors="replace")
            if "operation not permitted" in message.lower():
                pytest.skip("sandbox does not permit binding a local HTTP port")
            raise RuntimeError(f"HTTP MCP server exited early: {message[-1000:]}")
        try:
            _reader, writer = await asyncio.open_connection("127.0.0.1", port)
        except OSError:
            await asyncio.sleep(0.1)
            continue
        writer.close()
        await writer.wait_closed()
        return
    raise TimeoutError("HTTP MCP server did not open its port")


def _http_token() -> str:
    """Create a short-lived bearer token for the HTTP integration test."""
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {
            "sub": "klaudia-integration",
            "iat": now,
            "exp": now + datetime.timedelta(minutes=5),
        },
        _HTTP_SECRET,
        algorithm="HS256",
    )


def _unused_tcp_port() -> int:
    """Reserve and release a local TCP port for an HTTP subprocess.

    Returns:
        An unused local port assigned by the operating system.
    """
    try:
        with socket.socket(type=socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
    except PermissionError:
        pytest.skip("sandbox does not permit binding a local HTTP port")


async def _run_crud_flow(env_overrides: dict[str, str], session_id: int) -> None:
    transport = _server_transport(env_overrides)
    async with Client(transport, mode="auto") as session:
        tools = await session.list_tools()
        assert len(tools) == EXPECTED_TOOL_COUNT

        doc = await _call(
            session,
            "tool_create_document",
            {
                "session_id": session_id,
                "user_id": 1,
                "file_type": "image",
                "file_name": "r.jpg",
                "total_pages": 1,
            },
        )
        doc_id = doc["id"]
        assert doc_id >= 1

        fetched = await _call(session, "tool_get_document", {"document_id": doc_id})
        assert fetched["file_name"] == "r.jpg"
        assert fetched["status"] == "pending"

        page = await _call(
            session,
            "tool_create_page",
            {"metadata_file_id": doc_id, "page_number": 1},
        )
        page_id = page["id"]

        await _call(
            session,
            "tool_save_extraction",
            {
                "page_id": page_id,
                "extraction_json": json.dumps({"info": {"store_name": "TEST STORE"}}),
            },
        )
        extraction = await _call(
            session,
            "tool_get_extraction",
            {"metadata_file_id": doc_id, "page_number": 1},
        )
        assert extraction["info"]["store_name"] == "TEST STORE"

        files = await _call(
            session, "tool_get_session_files", {"session_id": session_id}
        )
        assert len(files) == 1
        assert files[0]["pages"][0]["status"] == "extracted"


async def test_mcp_server_sqlite_backend():
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db.close()
    import aiosqlite

    # Session row must exist before the tool writes to it; boot the schema
    # the same way the server does, then seed.
    env = {"SQLITE_DB": tmp_db.name, "DATABASE_URL": ""}
    transport = _server_transport(env)
    async with Client(transport, mode="auto"):
        pass  # server connect() created the schema
    async with aiosqlite.connect(tmp_db.name) as conn:
        cursor = await conn.execute("INSERT INTO session (user_id) VALUES (1)")
        await conn.commit()
        session_id = cursor.lastrowid

    await _run_crud_flow(env, session_id)
    os.unlink(tmp_db.name)


async def test_mcp_server_postgres_backend():
    if not await _pg_available():
        pytest.skip(f"Postgres not reachable at {_PG_URL}")
    import asyncpg

    await _seed_pg_session()
    # Boot once so the server applies the PG schema, then seed a session.
    env = {"DATABASE_URL": _PG_URL}
    transport = _server_transport(env)
    async with Client(transport, mode="auto"):
        pass

    conn = await asyncpg.connect(_PG_URL)
    try:
        session_id = await conn.fetchval(
            "INSERT INTO session (user_id) VALUES (1) RETURNING session_id"
        )
    finally:
        await conn.close()

    await _run_crud_flow(env, session_id)


async def test_stateless_http_negotiates_modern_protocol_and_requires_auth():
    """HTTP serves the modern protocol and rejects anonymous clients."""
    unused_tcp_port = _unused_tcp_port()
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp_db.close()
    env = {
        **os.environ,
        "DATABASE_URL": "",
        "SQLITE_DB": tmp_db.name,
        "FASTMCP_HOST": "127.0.0.1",
        "FASTMCP_PORT": str(unused_tcp_port),
        "MCP_JWT_SECRET": _HTTP_SECRET,
    }
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "main.py",
        "--transport",
        "http",
        cwd=str(_SERVER_DIR),
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        await _wait_for_port(process, unused_tcp_port)
        url = f"http://127.0.0.1:{unused_tcp_port}/mcp"

        with pytest.raises(MCPError, match="Server returned an error response"):
            async with Client(url, mode="auto"):
                pass

        async with Client(url, auth=_http_token(), mode="auto") as client:
            assert client.protocol_version == "2026-07-28"
            assert len(await client.list_tools()) == EXPECTED_TOOL_COUNT
    finally:
        if process.returncode is None:
            process.terminate()
            await process.wait()
        os.unlink(tmp_db.name)
