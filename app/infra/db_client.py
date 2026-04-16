from typing import Any

import aiosqlite

from app.engines.config import get_db_path
from app.utils.logger import logger

SCHEMA_SQL = """
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
"""

# Seed a dev user so user_id=1 exists
SEED_SQL = """
INSERT OR IGNORE INTO user (user_id, username, email, password_hash)
VALUES (1, 'dev', 'dev@local', 'not-a-real-hash');
"""


class DBClient:
    def __init__(self) -> None:
        self._db_path = get_db_path()
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.executescript(SEED_SQL)
        await self._conn.commit()
        logger.info(f"Database connected: {self._db_path}")

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
        if row is None:
            return None
        return dict(row)

    async def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        cursor = await self.conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def execute(self, sql: str, params: tuple = ()) -> int:
        cursor = await self.conn.execute(sql, params)
        await self.conn.commit()
        return cursor.lastrowid or 0

    async def execute_returning(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        cursor = await self.conn.execute(sql, params)
        await self.conn.commit()
        row = await cursor.fetchone()
        return dict(row) if row else None
