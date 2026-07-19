import logging
from typing import Any
from uuid import uuid4

import aiosqlite

from config.settings import Settings

logger = logging.getLogger(__name__)


# Public schema mirrors mcp-sqlite/app/infra/db_client.py. Both processes
# create the same tables idempotently (`CREATE TABLE IF NOT EXISTS`); whichever
# connects first wins. We duplicate the DDL here so:
#   - Tests with a fresh temp DB don't need an MCP server running.
#   - The app boots even if mcp-sqlite hasn't started yet (race-free startup).
_PUBLIC_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS session (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS conversation (
    message_id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sender TEXT NOT NULL,
    message_text TEXT NOT NULL,
    file_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(session_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id),
    FOREIGN KEY (file_id) REFERENCES metadata_file(id)
);

CREATE TABLE IF NOT EXISTS metadata_file (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    total_pages INTEGER NOT NULL DEFAULT 0,
    file_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    status_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES session(session_id),
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metadata_file_id INTEGER NOT NULL,
    page INTEGER NOT NULL,
    agent_extracted TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    status_message TEXT,
    FOREIGN KEY (metadata_file_id) REFERENCES metadata_file(id)
);

INSERT OR IGNORE INTO user (user_id, username, email, password_hash)
VALUES (1, 'dev', 'dev@local', 'not-a-real-hash');
"""


# Private app-side tables for blob storage + dedup. NOT exposed via MCP-SQLite
# tools — the LLM only sees metadata_file/pages. Hash + minio_key never reach
# the agent context.
_PRIVATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS file_blob (
    blob_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    blake3 TEXT NOT NULL,
    minio_key TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, blake3)
);

CREATE INDEX IF NOT EXISTS idx_file_blob_user_hash
    ON file_blob(user_id, blake3);

CREATE TABLE IF NOT EXISTS file_blob_page (
    blob_id INTEGER NOT NULL,
    page INTEGER NOT NULL,
    page_blake3 TEXT NOT NULL,
    page_minio_key TEXT NOT NULL,
    PRIMARY KEY (blob_id, page),
    FOREIGN KEY (blob_id) REFERENCES file_blob(blob_id)
);

CREATE INDEX IF NOT EXISTS idx_file_blob_page_hash
    ON file_blob_page(page_blake3);

CREATE TABLE IF NOT EXISTS blob_extraction (
    user_id INTEGER NOT NULL,
    page_blake3 TEXT NOT NULL,
    extraction_json TEXT NOT NULL,
    ocr_model TEXT,
    schema_version TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, page_blake3)
);

CREATE TABLE IF NOT EXISTS metadata_file_blob (
    metadata_file_id INTEGER PRIMARY KEY,
    blob_id INTEGER NOT NULL,
    FOREIGN KEY (blob_id) REFERENCES file_blob(blob_id)
);
"""


class AppDBClient:
    """Thin async SQLite client for app-side queries (conversation history, session management)."""

    def __init__(self, settings: Settings) -> None:
        self._db_path = settings.sqlite_db
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        # WAL improves concurrent read while mcp-sqlite subprocess writes.
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.executescript(_PUBLIC_SCHEMA_SQL)
        await self._conn.executescript(_PRIVATE_SCHEMA_SQL)
        await self._conn.commit()
        logger.info(f"App DB connected: {self._db_path} (schema applied)")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected")
        return self._conn

    async def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        cursor = await self.conn.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def execute(self, sql: str, params: tuple = ()) -> int:
        cursor = await self.conn.execute(sql, params)
        await self.conn.commit()
        return cursor.lastrowid or 0

    async def get_user_by_username(self, username: str) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT user_id, username, email, password_hash FROM user "
            "WHERE username = ?",
            (username,),
        )

    async def create_user(self, username: str, email: str, password_hash: str) -> int:
        return await self.execute(
            "INSERT INTO user (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )

    async def update_last_login(self, user_id: int) -> None:
        await self.execute(
            "UPDATE user SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
            (user_id,),
        )

    async def get_session_owner(self, session_id: int) -> int | None:
        row = await self.fetchone(
            "SELECT user_id FROM session WHERE session_id = ?",
            (session_id,),
        )
        return row["user_id"] if row else None

    async def create_session(
        self, user_id: int, session_name: str | None = None
    ) -> int:
        return await self.execute(
            "INSERT INTO session (user_id, session_name) VALUES (?, ?)",
            (user_id, session_name),
        )

    async def get_conversation_history(
        self, session_id: int, limit: int = 10
    ) -> list[dict[str, Any]]:
        return await self.fetchall(
            """
            SELECT sender, message_text, file_id, timestamp
            FROM conversation
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (session_id, limit),
        )

    async def save_message(
        self,
        session_id: int,
        user_id: int,
        sender: str,
        message_text: str,
        file_id: int | None = None,
    ) -> str:
        message_id = uuid4().hex
        await self.execute(
            """
            INSERT INTO conversation (message_id, session_id, user_id, sender, message_text, file_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message_id, session_id, user_id, sender, message_text, file_id),
        )
        return message_id

    async def update_session_timestamp(self, session_id: int) -> None:
        await self.execute(
            "UPDATE session SET updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (session_id,),
        )

    async def get_session_files(self, session_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            "SELECT * FROM metadata_file WHERE session_id = ? ORDER BY created_at",
            (session_id,),
        )

    async def get_sessions(self, user_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            """
            SELECT session_id, session_name, created_at, updated_at
            FROM session
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        )

    async def get_session_messages(self, session_id: int) -> list[dict[str, Any]]:
        return await self.fetchall(
            """
            SELECT sender, message_text, file_id, timestamp
            FROM conversation
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,),
        )

    # ── Private blob registry (not exposed to LLM) ──────────────────────────

    async def find_blob(self, user_id: int, blake3: str) -> dict[str, Any] | None:
        return await self.fetchone(
            "SELECT * FROM file_blob WHERE user_id = ? AND blake3 = ?",
            (user_id, blake3),
        )

    async def insert_blob(
        self,
        *,
        user_id: int,
        blake3: str,
        minio_key: str,
        content_type: str,
        size_bytes: int,
        page_count: int,
    ) -> int:
        return await self.execute(
            """
            INSERT INTO file_blob
                (user_id, blake3, minio_key, content_type, size_bytes, page_count)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, blake3, minio_key, content_type, size_bytes, page_count),
        )

    async def upsert_blob_page(
        self,
        *,
        blob_id: int,
        page: int,
        page_blake3: str,
        page_minio_key: str,
    ) -> None:
        await self.execute(
            """
            INSERT INTO file_blob_page (blob_id, page, page_blake3, page_minio_key)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(blob_id, page) DO UPDATE SET
                page_blake3 = excluded.page_blake3,
                page_minio_key = excluded.page_minio_key
            """,
            (blob_id, page, page_blake3, page_minio_key),
        )

    async def get_cached_extraction(
        self, user_id: int, page_blake3: str
    ) -> dict[str, Any] | None:
        return await self.fetchone(
            """
            SELECT extraction_json, ocr_model, schema_version, created_at
            FROM blob_extraction
            WHERE user_id = ? AND page_blake3 = ?
            """,
            (user_id, page_blake3),
        )

    async def upsert_extraction(
        self,
        *,
        user_id: int,
        page_blake3: str,
        extraction_json: str,
        ocr_model: str | None,
        schema_version: str | None,
    ) -> None:
        await self.execute(
            """
            INSERT INTO blob_extraction
                (user_id, page_blake3, extraction_json, ocr_model, schema_version)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, page_blake3) DO UPDATE SET
                extraction_json = excluded.extraction_json,
                ocr_model = excluded.ocr_model,
                schema_version = excluded.schema_version
            """,
            (user_id, page_blake3, extraction_json, ocr_model, schema_version),
        )

    async def link_metadata_file_blob(
        self, metadata_file_id: int, blob_id: int
    ) -> None:
        await self.execute(
            """
            INSERT INTO metadata_file_blob (metadata_file_id, blob_id)
            VALUES (?, ?)
            ON CONFLICT(metadata_file_id) DO UPDATE SET blob_id = excluded.blob_id
            """,
            (metadata_file_id, blob_id),
        )
