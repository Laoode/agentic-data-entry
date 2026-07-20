"""End-to-end MCP server test across both DB backends.

Spawns the real mcp-archive server as a stdio subprocess (exactly how the
app container runs it) and drives document/page/extraction tools through
an MCP ClientSession. Parametrized over sqlite (temp file) and postgres
(compose instance; skipped when unreachable).
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SERVER_DIR = _PROJECT_ROOT / "mcp-archive"
_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql://klaudia:klaudia@localhost:5432/klaudia"
)

EXPECTED_TOOL_COUNT = 11


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


def _server_params(env_overrides: dict[str, str]) -> StdioServerParameters:
    env = {**os.environ, **env_overrides}
    return StdioServerParameters(
        command=sys.executable,
        args=["main.py", "--transport", "stdio"],
        cwd=str(_SERVER_DIR),
        env=env,
    )


async def _call(session: ClientSession, tool: str, args: dict) -> dict | list:
    result = await session.call_tool(tool, args)
    text = "".join(c.text for c in result.content if getattr(c, "text", None))
    return json.loads(text)


async def _run_crud_flow(env_overrides: dict[str, str], session_id: int) -> None:
    params = _server_params(env_overrides)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            assert len(tools.tools) == EXPECTED_TOOL_COUNT

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
                    "extraction_json": json.dumps(
                        {"info": {"store_name": "TEST STORE"}}
                    ),
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
    params = _server_params(env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()  # server connect() created the schema
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
    params = _server_params(env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

    conn = await asyncpg.connect(_PG_URL)
    try:
        session_id = await conn.fetchval(
            "INSERT INTO session (user_id) VALUES (1) RETURNING session_id"
        )
    finally:
        await conn.close()

    await _run_crud_flow(env, session_id)
