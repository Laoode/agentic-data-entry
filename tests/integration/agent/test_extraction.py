"""Integration tests for ExtractionAgent (GLM-OCR direct JSON flow)."""

import json
import os

import pytest

from app.models.attachment import FileAttachment
from app.services.extraction.agents.base import ExtractionAgent
from app.services.extraction.infra.db_client import AppDBClient
from app.services.extraction.infra.ocr_client import OCRClient
from config.settings import Settings


SCHEMA_FOR_TEST = """
CREATE TABLE IF NOT EXISTS user (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP
);
CREATE TABLE IF NOT EXISTS session (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
    session_name TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS metadata_file (
    id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL, type TEXT NOT NULL, total_pages INTEGER NOT NULL DEFAULT 0,
    file_name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
    status_message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, metadata_file_id INTEGER NOT NULL,
    page INTEGER NOT NULL, agent_extracted TEXT,
    status TEXT NOT NULL DEFAULT 'pending', status_message TEXT
);
INSERT OR IGNORE INTO user (user_id, username, email, password_hash) VALUES (1, 'dev', 'dev@local', 'hash');
"""


@pytest.fixture
def settings_mock():
    return Settings(USE_MOCK_OCR=True, SQLITE_DB="test_extraction.db")


@pytest.fixture
async def db_dev(settings_mock):
    client = AppDBClient(settings_mock)
    await client.connect()
    await client.conn.executescript(SCHEMA_FOR_TEST)
    await client.conn.commit()
    session_id = await client.create_session(1, "test")
    yield client, session_id
    await client.close()
    if os.path.exists("test_extraction.db"):
        os.remove("test_extraction.db")


@pytest.mark.asyncio
async def test_extraction_mock_image_produces_valid_schema(settings_mock, db_dev):
    """Mock OCR should produce full EXTRACTION_SCHEMA dict, persisted to DB."""
    db_client, session_id = db_dev
    ocr = OCRClient(settings_mock)
    agent = ExtractionAgent(ocr_client=ocr, db_client=db_client)

    attachment = FileAttachment(
        filename="test-receipt.jpg",
        content_type="image/jpeg",
        data=b"fake image bytes",
    )

    result = await agent.process(attachment, session_id, user_id=1)

    assert result.status == "completed"
    assert len(result.pages) == 1
    page = result.pages[0]
    assert page["status"] == "extracted"
    ext = page["extraction"]
    assert ext["info"]["store_name"] == "INDOMARET"
    assert len(ext["items"]) == 3
    assert ext["payment"]["grand_total"] == "15540"

    row = await db_client.fetchone(
        "SELECT agent_extracted FROM pages WHERE metadata_file_id = ?",
        (result.file_id,),
    )
    persisted = json.loads(row["agent_extracted"])
    assert persisted["info"]["store_name"] == "INDOMARET"

    await ocr.shutdown()


@pytest.mark.asyncio
async def test_extraction_validates_partial_input(settings_mock, db_dev):
    """Validator must fill missing schema fields with defaults."""
    db_client, _ = db_dev
    ocr = OCRClient(settings_mock)
    agent = ExtractionAgent(ocr_client=ocr, db_client=db_client)

    partial = {"info": {"store_name": "X"}, "items": [{"item_name": "A"}]}
    validated = agent._validate_schema(partial)

    assert validated["info"]["store_name"] == "X"
    assert validated["info"]["receipt_id"] == ""
    assert validated["items"][0]["quantity"] == ""
    assert validated["payment"]["grand_total"] == ""
    assert validated["returned_items"] == []

    await ocr.shutdown()
