"""PostgreSQL storage for mem0 history and recent messages."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import version
from typing import Any
from uuid import uuid4

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

SUPPORTED_MEM0_VERSION = "2.0.13"
_RECENT_MESSAGE_LIMIT = 10

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memory_history (
    id UUID PRIMARY KEY,
    memory_id TEXT,
    old_memory TEXT,
    new_memory TEXT,
    event TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    actor_id TEXT,
    role TEXT
);

CREATE INDEX IF NOT EXISTS idx_memory_history_memory_time
    ON memory_history(memory_id, created_at, updated_at);

CREATE TABLE IF NOT EXISTS memory_message (
    sequence BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_scope TEXT NOT NULL,
    role TEXT,
    content TEXT,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memory_message_scope_sequence
    ON memory_message(session_scope, sequence DESC);
"""


def _isoformat(value: Any) -> str | None:
    """Return a database timestamp in mem0's string form.

    Args:
        value: Timestamp returned by psycopg.

    Returns:
        An ISO timestamp or None.
    """
    if value is None or isinstance(value, str):
        return value
    return value.isoformat()


class PostgresHistoryStore:
    """Implement mem0's synchronous history contract with PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        """Open a PostgreSQL pool and create the memory tables.

        Args:
            database_url: PostgreSQL connection string.
        """
        self._pool: ConnectionPool | None = ConnectionPool(
            database_url,
            kwargs={"row_factory": dict_row},
            min_size=1,
            max_size=5,
            open=True,
        )
        try:
            self.pool.wait()
            with self.pool.connection() as connection:
                connection.execute(_SCHEMA_SQL)
        except Exception:
            self.close()
            raise

    @property
    def pool(self) -> ConnectionPool:
        """Return the active connection pool.

        Raises:
            RuntimeError: If the store has closed.
        """
        if self._pool is None:
            raise RuntimeError("Memory history store is closed")
        return self._pool

    def add_history(
        self,
        memory_id: str,
        old_memory: str | None,
        new_memory: str | None,
        event: str,
        *,
        created_at: str | None = None,
        updated_at: str | None = None,
        is_deleted: int = 0,
        actor_id: str | None = None,
        role: str | None = None,
    ) -> None:
        """Store one mem0 history event.

        Args:
            memory_id: Mem0 memory identifier.
            old_memory: Text before the event.
            new_memory: Text after the event.
            event: Mem0 event name.
            created_at: Original creation timestamp.
            updated_at: Event update timestamp.
            is_deleted: Whether the event deleted the memory.
            actor_id: Optional actor identifier.
            role: Optional message role.
        """
        with self.pool.connection() as connection:
            connection.execute(
                """
                INSERT INTO memory_history (
                    id, memory_id, old_memory, new_memory, event,
                    created_at, updated_at, is_deleted, actor_id, role
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    uuid4(),
                    memory_id,
                    old_memory,
                    new_memory,
                    event,
                    created_at,
                    updated_at,
                    bool(is_deleted),
                    actor_id,
                    role,
                ),
            )

    def batch_add_history(self, records: list[dict[str, Any]]) -> None:
        """Store a batch of mem0 history events.

        Args:
            records: History records in mem0's storage shape.
        """
        if not records:
            return
        values = [
            (
                uuid4(),
                record.get("memory_id"),
                record.get("old_memory"),
                record.get("new_memory"),
                record.get("event"),
                record.get("created_at"),
                record.get("updated_at"),
                bool(record.get("is_deleted", 0)),
                record.get("actor_id"),
                record.get("role"),
            )
            for record in records
        ]
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO memory_history (
                        id, memory_id, old_memory, new_memory, event,
                        created_at, updated_at, is_deleted, actor_id, role
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    values,
                )

    def get_history(self, memory_id: str) -> list[dict[str, Any]]:
        """Return one memory's history in time order.

        Args:
            memory_id: Mem0 memory identifier.

        Returns:
            History records in mem0's storage shape.
        """
        with self.pool.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, memory_id, old_memory, new_memory, event,
                       created_at, updated_at, is_deleted, actor_id, role
                FROM memory_history
                WHERE memory_id = %s
                ORDER BY created_at ASC NULLS FIRST,
                         updated_at ASC NULLS FIRST,
                         id ASC
                """,
                (memory_id,),
            ).fetchall()
        return [
            {
                **row,
                "id": str(row["id"]),
                "created_at": _isoformat(row["created_at"]),
                "updated_at": _isoformat(row["updated_at"]),
                "is_deleted": bool(row["is_deleted"]),
            }
            for row in rows
        ]

    def save_messages(self, messages: list[dict[str, Any]], session_scope: str) -> None:
        """Store messages and retain the newest ten for one mem0 scope.

        Args:
            messages: Chat messages used during fact extraction.
            session_scope: Mem0's escaped tenant scope.
        """
        if not messages:
            return
        values = [
            (
                session_scope,
                message.get("role"),
                message.get("content"),
                message.get("name"),
                datetime.now(timezone.utc),
            )
            for message in messages
        ]
        with self.pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO memory_message (
                        session_scope, role, content, name, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    values,
                )
                cursor.execute(
                    """
                    DELETE FROM memory_message
                    WHERE session_scope = %s
                      AND sequence NOT IN (
                          SELECT sequence
                          FROM memory_message
                          WHERE session_scope = %s
                          ORDER BY sequence DESC
                          LIMIT %s
                      )
                    """,
                    (session_scope, session_scope, _RECENT_MESSAGE_LIMIT),
                )

    def get_last_messages(
        self, session_scope: str, limit: int = _RECENT_MESSAGE_LIMIT
    ) -> list[dict[str, Any]]:
        """Return the newest messages for one scope in chat order.

        Args:
            session_scope: Mem0's escaped tenant scope.
            limit: Maximum messages to return.

        Returns:
            Recent messages in chronological order.
        """
        with self.pool.connection() as connection:
            rows = connection.execute(
                """
                SELECT role, content, name, created_at
                FROM (
                    SELECT role, content, name, created_at, sequence
                    FROM memory_message
                    WHERE session_scope = %s
                    ORDER BY sequence DESC
                    LIMIT %s
                ) recent
                ORDER BY sequence ASC
                """,
                (session_scope, limit),
            ).fetchall()
        return [{**row, "created_at": _isoformat(row["created_at"])} for row in rows]

    def reset(self) -> None:
        """Clear all mem0 history and recent messages."""
        with self.pool.connection() as connection:
            connection.execute(
                "TRUNCATE memory_history, memory_message RESTART IDENTITY"
            )

    def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            self._pool.close()
            self._pool = None


def install_postgres_history_store() -> None:
    """Replace mem0's hardcoded SQLite manager with PostgreSQL.

    Raises:
        RuntimeError: If the installed mem0 version or manager contract changed.
    """
    installed_version = version("mem0ai")
    if installed_version != SUPPORTED_MEM0_VERSION:
        raise RuntimeError(
            "Unsupported mem0ai version for PostgreSQL history adapter: "
            f"expected {SUPPORTED_MEM0_VERSION}, found {installed_version}"
        )

    from mem0.memory import main as mem0_memory

    current_manager = mem0_memory.SQLiteManager
    if current_manager is PostgresHistoryStore:
        return
    if (
        current_manager.__module__ != "mem0.memory.storage"
        or current_manager.__name__ != "SQLiteManager"
    ):
        raise RuntimeError("mem0 history manager contract changed")
    mem0_memory.SQLiteManager = PostgresHistoryStore
