"""Application database tests against PostgreSQL.

Verifies the typed domain methods, native SQL calls, affected-row counts,
generated IDs, and idempotent upserts used by the application.

Requires PostgreSQL at PG_TEST_URL (default: the Compose sandbox).
Skipped cleanly when unreachable.
"""


async def test_user_roundtrip(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "hash-a")
    assert uid > 1  # seeded dev user holds id 1
    row = await postgres_db.get_user_by_username("alice")
    assert row is not None
    assert row["user_id"] == uid
    assert row["email"] == "alice@example.com"
    await postgres_db.update_last_login(uid)


async def test_get_unknown_user_returns_none(postgres_db):
    assert await postgres_db.get_user_by_username("nobody") is None


async def test_execute_returns_affected_row_count(postgres_db):
    user_id = await postgres_db.create_user("alice", "alice@example.com", "hash-a")

    changed = await postgres_db.execute(
        'UPDATE "user" SET email = $1 WHERE user_id = $2',
        ("new-alice@example.com", user_id),
    )
    missing = await postgres_db.execute(
        'UPDATE "user" SET email = $1 WHERE user_id = $2',
        ("missing@example.com", user_id + 999),
    )

    assert changed == 1
    assert missing == 0


async def test_session_ownership_and_listing(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    sid = await postgres_db.create_session(uid, "first")
    assert await postgres_db.get_session_owner(sid) == uid
    assert await postgres_db.get_session_owner(sid + 999) is None
    sessions = await postgres_db.get_sessions(uid)
    assert [s["session_id"] for s in sessions] == [sid]


async def test_message_roundtrip_and_ordering(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    sid = await postgres_db.create_session(uid)
    await postgres_db.save_message(sid, uid, "user", "first")
    await postgres_db.save_message(sid, uid, "assistant", "second")
    msgs = await postgres_db.get_session_messages(sid)
    assert [m["message_text"] for m in msgs] == ["first", "second"]
    history = await postgres_db.get_conversation_history(sid, limit=1)
    assert history[0]["message_text"] == "second"


async def test_native_sql_from_ingest_path(postgres_db):
    """Native SQL returns generated IDs and typed rows."""
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    sid = await postgres_db.create_session(uid)
    file_id = await postgres_db.fetchval(
        """
        INSERT INTO metadata_file
            (session_id, user_id, type, total_pages, file_name, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        (sid, uid, "image", 1, "r.jpg", "pending"),
    )
    assert file_id >= 1
    row = await postgres_db.fetchone(
        "SELECT status, file_name FROM metadata_file WHERE id = $1", (file_id,)
    )
    assert row == {"status": "pending", "file_name": "r.jpg"}
    await postgres_db.execute(
        "UPDATE metadata_file SET status = $1, status_message = $2 WHERE id = $3",
        ("completed", None, file_id),
    )
    files = await postgres_db.get_session_files(sid)
    assert files[0]["status"] == "completed"


async def test_blob_registry_roundtrip(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    blob_id = await postgres_db.insert_blob(
        user_id=uid,
        blake3="abc123",
        minio_key="blobs/u/abc123",
        content_type="image/jpeg",
        size_bytes=1234,
        page_count=1,
    )
    assert blob_id >= 1
    found = await postgres_db.find_blob(uid, "abc123")
    assert found is not None and found["blob_id"] == blob_id
    assert await postgres_db.find_blob(uid + 1, "abc123") is None


async def test_upserts_are_idempotent(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    blob_id = await postgres_db.insert_blob(
        user_id=uid,
        blake3="abc",
        minio_key="k",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    for key in ("k1", "k2"):
        await postgres_db.upsert_blob_page(
            blob_id=blob_id, page=1, page_blake3="p1", page_minio_key=key
        )
    rows = await postgres_db.fetchall(
        "SELECT page_minio_key FROM file_blob_page WHERE blob_id = $1", (blob_id,)
    )
    assert [r["page_minio_key"] for r in rows] == ["k2"]

    for payload in ('{"v": 1}', '{"v": 2}'):
        await postgres_db.upsert_extraction(
            user_id=uid,
            page_blake3="p1",
            extraction_json=payload,
            ocr_model="m",
            schema_version="v1",
        )
    cached = await postgres_db.get_cached_extraction(uid, "p1")
    assert cached is not None and cached["extraction_json"] == '{"v": 2}'


async def test_link_metadata_file_blob_upsert(postgres_db):
    uid = await postgres_db.create_user("alice", "alice@example.com", "h")
    sid = await postgres_db.create_session(uid)
    file_id = await postgres_db.fetchval(
        """
        INSERT INTO metadata_file
            (session_id, user_id, type, total_pages, file_name, status)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id
        """,
        (sid, uid, "image", 1, "r.jpg", "pending"),
    )
    blob_a = await postgres_db.insert_blob(
        user_id=uid,
        blake3="a",
        minio_key="ka",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    blob_b = await postgres_db.insert_blob(
        user_id=uid,
        blake3="b",
        minio_key="kb",
        content_type="image/jpeg",
        size_bytes=1,
        page_count=1,
    )
    await postgres_db.link_metadata_file_blob(file_id, blob_a)
    await postgres_db.link_metadata_file_blob(file_id, blob_b)
    row = await postgres_db.fetchone(
        "SELECT blob_id FROM metadata_file_blob WHERE metadata_file_id = $1",
        (file_id,),
    )
    assert row == {"blob_id": blob_b}


async def test_schema_drops_duplicate_blob_hash_index(postgres_db):
    index_name = await postgres_db.fetchval(
        "SELECT to_regclass('public.idx_file_blob_user_hash')"
    )

    assert index_name is None
