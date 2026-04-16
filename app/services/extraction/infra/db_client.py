import logging
from typing import Any
from uuid import uuid4

import aiosqlite

from config.settings import Settings

logger = logging.getLogger(__name__)


class AppDBClient:
    """Thin async SQLite client for app-side queries (conversation history, session management)."""

    def __init__(self, settings: Settings) -> None:
        self._db_path = settings.sqlite_db
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        logger.info(f"App DB connected: {self._db_path}")

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

    async def create_session(self, user_id: int, session_name: str | None = None) -> int:
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
