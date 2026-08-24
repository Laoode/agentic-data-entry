"""PostgreSQL contract tests for mem0 history storage."""

from collections.abc import Iterator

import pytest
import psycopg

from app.services.core.memory_history import PostgresHistoryStore
from tests.integration.postgres import POSTGRES_TEST_URL


@pytest.fixture(scope="module")
def postgres_history_store() -> Iterator[PostgresHistoryStore]:
    """Provide a mem0 history store in the test database."""
    try:
        with psycopg.connect(POSTGRES_TEST_URL, connect_timeout=1):
            pass
        store = PostgresHistoryStore(POSTGRES_TEST_URL)
    except Exception:
        pytest.skip("The isolated PostgreSQL test database is unavailable")
    yield store
    store.close()


@pytest.fixture
def memory_history(postgres_history_store) -> Iterator[PostgresHistoryStore]:
    """Clear the shared mem0 history store before and after one test."""
    postgres_history_store.reset()
    yield postgres_history_store
    postgres_history_store.reset()


def test_history_round_trip_preserves_mem0_fields(memory_history):
    memory_history.add_history(
        "memory-1",
        None,
        "prefers concise reports",
        "ADD",
        created_at="2026-08-24T01:00:00+00:00",
        actor_id="user-1",
        role="user",
    )
    memory_history.add_history(
        "memory-1",
        "prefers concise reports",
        "prefers concise weekly reports",
        "UPDATE",
        created_at="2026-08-24T01:00:00+00:00",
        updated_at="2026-08-24T02:00:00+00:00",
    )

    records = memory_history.get_history("memory-1")

    assert [record["event"] for record in records] == ["ADD", "UPDATE"]
    assert records[0]["actor_id"] == "user-1"
    assert records[0]["role"] == "user"
    assert records[1]["old_memory"] == "prefers concise reports"
    assert records[1]["is_deleted"] is False


def test_batch_history_is_scoped_by_memory_id(memory_history):
    memory_history.batch_add_history(
        [
            {
                "memory_id": "memory-a",
                "new_memory": "A",
                "event": "ADD",
                "created_at": "2026-08-24T01:00:00+00:00",
            },
            {
                "memory_id": "memory-b",
                "new_memory": "B",
                "event": "ADD",
                "created_at": "2026-08-24T01:00:00+00:00",
            },
        ]
    )

    records = memory_history.get_history("memory-a")

    assert [record["new_memory"] for record in records] == ["A"]


def test_recent_messages_keep_last_ten_per_scope(memory_history):
    for number in range(12):
        memory_history.save_messages(
            [{"role": "user", "content": f"message-{number}", "name": None}],
            "user_id=1",
        )
    memory_history.save_messages(
        [{"role": "user", "content": "other-user", "name": None}],
        "user_id=2",
    )

    messages = memory_history.get_last_messages("user_id=1", limit=20)

    assert [message["content"] for message in messages] == [
        f"message-{number}" for number in range(2, 12)
    ]


def test_reset_clears_history_and_messages(memory_history):
    memory_history.add_history("memory-1", None, "A", "ADD")
    memory_history.save_messages(
        [{"role": "user", "content": "hello", "name": None}],
        "user_id=1",
    )

    memory_history.reset()

    assert memory_history.get_history("memory-1") == []
    assert memory_history.get_last_messages("user_id=1") == []
