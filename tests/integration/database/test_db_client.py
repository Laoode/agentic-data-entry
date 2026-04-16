"""Integration tests for AppDBClient (app-side SQLite client)."""

import asyncio
import os
import pytest

# Set test DB before imports
os.environ["SQLITE_DB"] = "test_integration.db"

from app.services.extraction.infra.db_client import AppDBClient
from config.settings import Settings


@pytest.fixture
def settings():
    return Settings(SQLITE_DB="test_integration.db")


@pytest.fixture
async def db(settings):
    client = AppDBClient(settings)
    await client.connect()
    # Create schema (same as MCP-SQLite)
    await client.conn.executescript("""
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
            FOREIGN KEY (session_id) REFERENCES session(session_id)
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
            FOREIGN KEY (session_id) REFERENCES session(session_id)
        );
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metadata_file_id INTEGER NOT NULL,
            page INTEGER NOT NULL,
            ocr_output TEXT,
            agent_extracted TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            status_message TEXT,
            FOREIGN KEY (metadata_file_id) REFERENCES metadata_file(id)
        );
        INSERT OR IGNORE INTO user (user_id, username, email, password_hash)
        VALUES (1, 'dev', 'dev@local', 'not-a-real-hash');
    """)
    await client.conn.commit()
    yield client
    await client.close()
    # Cleanup
    if os.path.exists("test_integration.db"):
        os.remove("test_integration.db")


@pytest.mark.asyncio
async def test_create_session(db):
    session_id = await db.create_session(1, "Test Session")
    assert session_id > 0


@pytest.mark.asyncio
async def test_save_and_get_messages(db):
    session_id = await db.create_session(1, "Chat Test")
    msg_id = await db.save_message(session_id, 1, "user", "Hello Klaudia")
    assert isinstance(msg_id, str)
    assert len(msg_id) == 32  # uuid4 hex
    await db.save_message(session_id, 1, "assistant", "Halo! Ada yang bisa saya bantu?")

    history = await db.get_conversation_history(session_id, limit=10)
    assert len(history) == 2
    senders = {h["sender"] for h in history}
    assert senders == {"user", "assistant"}


@pytest.mark.asyncio
async def test_update_session_timestamp(db):
    session_id = await db.create_session(1)
    await db.update_session_timestamp(session_id)
    row = await db.fetchone("SELECT updated_at FROM session WHERE session_id = ?", (session_id,))
    assert row is not None


@pytest.mark.asyncio
async def test_get_session_files(db):
    session_id = await db.create_session(1)
    files = await db.get_session_files(session_id)
    assert files == []

    # Insert a file
    await db.execute(
        "INSERT INTO metadata_file (session_id, user_id, type, file_name, total_pages, status) VALUES (?, ?, ?, ?, ?, ?)",
        (session_id, 1, "image", "receipt.jpg", 1, "completed"),
    )
    files = await db.get_session_files(session_id)
    assert len(files) == 1
    assert files[0]["file_name"] == "receipt.jpg"
