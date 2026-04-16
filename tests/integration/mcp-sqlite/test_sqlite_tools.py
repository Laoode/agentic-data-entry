"""End-to-end MCP-SQLite tool invocation tests.

Requires the MCP-SQLite server running on port 8001 (via ./startup.sh).
Exercises the full document → page → extraction flow via SSE client.
"""

import json

import pytest
from mcp import ClientSession
from mcp.client.sse import sse_client


SSE_URL = "http://localhost:8001/sse"


async def _call(session: ClientSession, name: str, args: dict) -> dict:
    result = await session.call_tool(name, args)
    assert not result.isError, f"{name} errored: {result.content}"
    assert result.content, f"{name} returned no content"
    text = result.content[0].text
    return json.loads(text)


@pytest.mark.asyncio
async def test_full_document_flow():
    """Walk the full 7-step MCP-SQLite tool flow against a live server."""
    async with sse_client(SSE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            required = {
                "tool_create_document",
                "tool_create_page",
                "tool_save_extraction",
                "tool_get_document",
                "tool_list_pages",
                "tool_get_extraction",
                "tool_get_session_files",
                "tool_update_document_status",
                "tool_update_page",
                "tool_get_page",
                "tool_list_documents",
            }
            missing = required - names
            assert not missing, f"missing tools: {missing}"

            # 1. Create document.
            doc = await _call(
                session,
                "tool_create_document",
                {
                    "session_id": 1,
                    "user_id": 1,
                    "file_type": "image",
                    "file_name": "mcp-test-receipt.jpg",
                    "total_pages": 1,
                },
            )
            doc_id = doc["id"]
            assert isinstance(doc_id, int) and doc_id > 0

            # 2. Create page.
            page = await _call(
                session,
                "tool_create_page",
                {"metadata_file_id": doc_id, "page_number": 1},
            )
            page_id = page["id"]
            assert isinstance(page_id, int) and page_id > 0

            # 3. Save extraction.
            extraction = {
                "info": {"store_name": "INDOMARET"},
                "items": [{"item_name": "Indomie", "quantity": "2"}],
                "returned_items": [],
                "payment": {"grand_total": "15540", "currency": "IDR"},
            }
            saved = await _call(
                session,
                "tool_save_extraction",
                {"page_id": page_id, "extraction_json": json.dumps(extraction)},
            )
            assert saved == {"ok": True}

            # 4. Read document back.
            got_doc = await _call(
                session, "tool_get_document", {"document_id": doc_id}
            )
            assert got_doc["id"] == doc_id
            assert got_doc["file_name"] == "mcp-test-receipt.jpg"

            # 5. List pages.
            pages = await _call(
                session, "tool_list_pages", {"metadata_file_id": doc_id}
            )
            assert len(pages) == 1
            assert pages[0]["id"] == page_id

            # 6. Get extraction for page.
            ext = await _call(
                session,
                "tool_get_extraction",
                {"metadata_file_id": doc_id, "page_number": 1},
            )
            assert ext["info"]["store_name"] == "INDOMARET"
            assert ext["payment"]["grand_total"] == "15540"

            # 7. Get all session files.
            files = await _call(
                session, "tool_get_session_files", {"session_id": 1}
            )
            assert any(f["id"] == doc_id for f in files)


@pytest.mark.asyncio
async def test_missing_document_returns_error_payload():
    """get_document on unknown ID returns a JSON error instead of raising."""
    async with sse_client(SSE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await _call(
                session, "tool_get_document", {"document_id": 999999}
            )
            assert "error" in result


@pytest.mark.asyncio
async def test_update_document_status_persists():
    """Status updates round-trip through tool_get_document."""
    async with sse_client(SSE_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            doc = await _call(
                session,
                "tool_create_document",
                {
                    "session_id": 1,
                    "user_id": 1,
                    "file_type": "image",
                    "file_name": "status-test.jpg",
                    "total_pages": 1,
                },
            )
            doc_id = doc["id"]

            await _call(
                session,
                "tool_update_document_status",
                {
                    "document_id": doc_id,
                    "status": "completed",
                    "status_message": "ok",
                },
            )
            got = await _call(
                session, "tool_get_document", {"document_id": doc_id}
            )
            assert got["status"] == "completed"
            assert got["status_message"] == "ok"
