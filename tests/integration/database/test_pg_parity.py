"""PgDBClient parity tests against a real Postgres.

Verifies the Postgres client honors the exact AppDBClient contract the app
relies on: typed domain methods, raw '?'-placeholder SQL from ingest/tasks/
orchestrator (translated internally), lastrowid-style ids from execute(),
and upsert idempotency.

Requires Postgres at PG_TEST_URL (default: docker-compose postgres).
Skipped cleanly when unreachable.
"""

import os
from typing import AsyncIterator

import pytest

from app.services.extraction.infra.db_client_pg import PgDBClient
from config.settings import Settings

_PG_URL = os.environ.get(
    "PG_TEST_URL", "postgresql://klaudia:klaudia@localhost:5432/klaudia"
)

_ALL_TABLES = (
    "metadata_file_blob",
    "blob_extraction",
    "file_blob_page",
    "file_blob",
    "pages",
    "metadata_file",
    "conversation",
    "session",
    '"user"',
)


@pytest.fixture
async def db() -> AsyncIterator[PgDBClient]:
    client = PgDBClient(Settings(DATABASE_URL=_PG_URL))
    try:
        await client.connect()
    except Exception as exc:
        pytest.skip(f"Postgres not reachable at {_PG_URL}: {exc}")
    for table in _ALL_TABLES:
        await client.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")
    # Re-seed the dev bootstrap row that connect() normally provides.
    await client.execute(
        """INSERT INTO "user" (user_id, username, email, password_hash)
           VALUES (1, 'dev', 'dev@local', 'not-a-real-hash')
           ON CONFLICT (user_id) DO NOTHING"""
    )
    await client.reset_user_id_sequence()
    yield client
    await client.close()


async def test_user_roundtrip(db):
    uid = await db.create_user("alice", "alice@example.com", "hash-a")
    assert uid > 1  # seeded dev user holds id 1
    row = await db.get_user_by_username("alice")
    assert row is not None
    assert row["user_id"] == uid
    assert row["email"] == "alice@example.com"
    await db.update_last_login(uid)


async def test_get_unknown_user_returns_none(db):
    assert await db.get_user_by_username("nobody") is None


async def test_session_ownership_and_listing(db):
    uid = await db.create_user("alice", "alice@example.com", "h")
    sid = await db.create_session(uid, "first")
    assert await db.get_session_owner(sid) == uid
    assert await db.get_session_owner(sid + 999) is None
    sessions = await db.get_sessions(uid)
    assert [s["session_id"] for s in sessions] == [sid]


async def test_message_roundtrip_and_ordering(db):
    uid = await db.create_user("alice", "alice@example.com", "h")
    sid = await db.create_session(uid)
    await db.save_message(sid, uid, "user", "first")
    await db.save_message(sid, uid, "assistant", "second")
    msgs = await db.get_session_messages(sid)
    assert [m["message_text"] for m in msgs] == ["first", "second"]
    history = await db.get_conversation_history(sid, limit=1)
    assert history[0]["message_text"] == "second"


async def test_raw_placeholder_sql_from_ingest_path(db):
    """ingest.py/tasks.py issue raw '?' SQL through execute/fetchone;
    the client must translate placeholders and return the inserted id."""
    uid = await db.create_user("alice", "alice@example.com", "h")
    sid = await db.create_session(uid)
    file_id = await db.execute(
        """
        INSERT INTO metadata_file
            (session_id, user_id, type, total_pages, file_name, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (sid, uid, "image", 1, "r.jpg", "pending"),
    )
    assert file_id >= 1
    row = await db.fetchone(
        "SELECT status, file_name FROM metadata_file WHERE id = ?", (file_id,)
    )
    assert row == {"status": "pending", "file_name": "r.jpg"}
    await db.execute(
        "UPDATE metadata_file SET status = ?, status_message = ? WHERE id = ?",
        ("completed", None, file_id),
    )
    files = await db.get_session_files(sid)
    assert files[0]["status"] == "completed"


async def test_blob_registry_roundtrip(db):
    uid = await db.create_user("alice", "alice@example.com", "h")
    blob_id = await db.insert_blob(
        user_id=uid,
        blake3="abc123",
        minio_key="blobs/u/abc123",
        content_type="image/jpeg",
        size_bytes=1234,
        page_count=1,
    )
    assert blob_id >= 1
    found = await db.find_blob(uid, "abc123")
    assert found is not None and found["blob_id"] == blob_id
    assert await db.find_blob(uid + 1, "abc123") is None  # per-user isolation


async def test_upserts_are_idempotent(db):
    uid = await db.create_user("alice", "alice@example.com", "h")
    blob_id = await db.insert_blob(
        user_id=uid,
        blake3="abc",
        minio_key="k",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    for key in ("k1", "k2"):
        await db.upsert_blob_page(
            blob_id=blob_id, page=1, page_blake3="p1", page_minio_key=key
        )
    rows = await db.fetchall(
        "SELECT page_minio_key FROM file_blob_page WHERE blob_id = ?", (blob_id,)
    )
    assert [r["page_minio_key"] for r in rows] == ["k2"]

    for payload in ('{"v": 1}', '{"v": 2}'):
        await db.upsert_extraction(
            user_id=uid,
            page_blake3="p1",
            extraction_json=payload,
            ocr_model="m",
            schema_version="v1",
        )
    cached = await db.get_cached_extraction(uid, "p1")
    assert cached is not None and cached["extraction_json"] == '{"v": 2}'


async def test_link_metadata_file_blob_upsert(db):
    uid = await db.create_user("alice", "alice@example.com", "h")
    sid = await db.create_session(uid)
    file_id = await db.execute(
        """
        INSERT INTO metadata_file
            (session_id, user_id, type, total_pages, file_name, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (sid, uid, "image", 1, "r.jpg", "pending"),
    )
    blob_a = await db.insert_blob(
        user_id=uid,
        blake3="a",
        minio_key="ka",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    blob_b = await db.insert_blob(
        user_id=uid,
        blake3="b",
        minio_key="kb",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    await db.link_metadata_file_blob(file_id, blob_a)
    await db.link_metadata_file_blob(file_id, blob_b)  # relink must update
    row = await db.fetchone(
        "SELECT blob_id FROM metadata_file_blob WHERE metadata_file_id = ?",
        (file_id,),
    )
    assert row == {"blob_id": blob_b}
