import json
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import Context, FastMCP

from app.infra.db_client import DBClient
from app.infra.db_client_pg import build_db_client
from app.tools import (
    create_document,
    create_page,
    get_document,
    get_extraction,
    get_page,
    get_session_files,
    list_documents,
    list_pages,
    save_extraction,
    update_document_status,
    update_page,
)
from app.utils.logger import logger

load_dotenv()


@asynccontextmanager
async def sqlite_lifespan(server: FastMCP) -> AsyncIterator[DBClient]:
    db = build_db_client()
    await db.connect()
    logger.info(f"MCP DB server ready (backend={type(db).__name__})")
    try:
        yield db
    finally:
        await db.close()
        logger.info("MCP DB server shut down")


HOST = os.environ.get("FASTMCP_HOST", "0.0.0.0")
PORT = int(os.environ.get("FASTMCP_PORT", "8001"))

mcp = FastMCP(
    name="mcp-archive",
    instructions=(
        "SQLite MCP Server for receipt data management. "
        "Provides tools for document, page, and extraction CRUD operations."
    ),
    lifespan=sqlite_lifespan,
    host=HOST,
    port=PORT,
)


# --- Document operations ---


@mcp.tool()
async def tool_get_document(document_id: int, ctx: Context = None) -> str:
    """
    Get a document (metadata_file) by ID.

    Args:
        document_id: The metadata_file ID.

    Returns:
        JSON string of the document record, or error message.
    """
    db: DBClient = ctx.request_context.lifespan_context
    doc = await get_document(db, document_id)
    if doc is None:
        return json.dumps({"error": f"Document {document_id} not found"})
    return json.dumps(doc, default=str)


@mcp.tool()
async def tool_list_documents(session_id: int, ctx: Context = None) -> str:
    """
    List all documents in a session.

    Args:
        session_id: The session ID.

    Returns:
        JSON array of document records.
    """
    db: DBClient = ctx.request_context.lifespan_context
    docs = await list_documents(db, session_id)
    return json.dumps(docs, default=str)


@mcp.tool()
async def tool_create_document(
    session_id: int,
    user_id: int,
    file_type: str,
    file_name: str,
    total_pages: int,
    ctx: Context = None,
) -> str:
    """
    Create a new document record.

    Args:
        session_id: Session ID.
        user_id: User ID.
        file_type: 'pdf' or 'image'.
        file_name: Original file name.
        total_pages: Number of pages.

    Returns:
        JSON with the new document ID.
    """
    db: DBClient = ctx.request_context.lifespan_context
    doc_id = await create_document(
        db, session_id, user_id, file_type, file_name, total_pages
    )
    return json.dumps({"id": doc_id})


@mcp.tool()
async def tool_update_document_status(
    document_id: int,
    status: str,
    status_message: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """
    Update a document's processing status.

    Args:
        document_id: The document ID.
        status: New status ('completed', 'partial', 'failed').
        status_message: Optional status detail.

    Returns:
        JSON confirmation.
    """
    db: DBClient = ctx.request_context.lifespan_context
    await update_document_status(db, document_id, status, status_message)
    return json.dumps({"ok": True})


# --- Page operations ---


@mcp.tool()
async def tool_list_pages(metadata_file_id: int, ctx: Context = None) -> str:
    """
    List all pages for a document.

    Args:
        metadata_file_id: The document ID.

    Returns:
        JSON array of page records.
    """
    db: DBClient = ctx.request_context.lifespan_context
    pages = await list_pages(db, metadata_file_id)
    return json.dumps(pages, default=str)


@mcp.tool()
async def tool_get_page(
    metadata_file_id: int, page_number: int, ctx: Context = None
) -> str:
    """
    Get a specific page by document ID and page number.

    Args:
        metadata_file_id: The document ID.
        page_number: Page number (1-indexed).

    Returns:
        JSON string of the page record.
    """
    db: DBClient = ctx.request_context.lifespan_context
    page = await get_page(db, metadata_file_id, page_number)
    if page is None:
        return json.dumps({"error": f"Page {page_number} not found"})
    return json.dumps(page, default=str)


@mcp.tool()
async def tool_create_page(
    metadata_file_id: int,
    page_number: int,
    ctx: Context = None,
) -> str:
    """
    Create a new page record for a document.

    Args:
        metadata_file_id: The document ID.
        page_number: Page number.

    Returns:
        JSON with the new page ID.
    """
    db: DBClient = ctx.request_context.lifespan_context
    page_id = await create_page(db, metadata_file_id, page_number)
    return json.dumps({"id": page_id})


@mcp.tool()
async def tool_update_page(
    page_id: int,
    agent_extracted: Optional[str] = None,
    status: Optional[str] = None,
    status_message: Optional[str] = None,
    ctx: Context = None,
) -> str:
    """
    Update a page record.

    Args:
        page_id: The page row ID.
        agent_extracted: JSON string of extraction result.
        status: New status.
        status_message: Status detail.

    Returns:
        JSON confirmation.
    """
    db: DBClient = ctx.request_context.lifespan_context
    await update_page(db, page_id, agent_extracted, status, status_message)
    return json.dumps({"ok": True})


# --- Extraction operations ---


@mcp.tool()
async def tool_get_extraction(
    metadata_file_id: int, page_number: int, ctx: Context = None
) -> str:
    """
    Get the extracted JSON data for a specific page.

    Args:
        metadata_file_id: The document ID.
        page_number: Page number.

    Returns:
        JSON string of the extraction, or null.
    """
    db: DBClient = ctx.request_context.lifespan_context
    data = await get_extraction(db, metadata_file_id, page_number)
    return json.dumps(data, default=str)


@mcp.tool()
async def tool_save_extraction(
    page_id: int,
    extraction_json: str,
    ctx: Context = None,
) -> str:
    """
    Save structured extraction JSON to a page.

    Args:
        page_id: The page row ID.
        extraction_json: JSON string of the extraction result.

    Returns:
        JSON confirmation.
    """
    db: DBClient = ctx.request_context.lifespan_context
    extraction = json.loads(extraction_json)
    await save_extraction(db, page_id, extraction)
    return json.dumps({"ok": True})


@mcp.tool()
async def tool_get_session_files(session_id: int, ctx: Context = None) -> str:
    """
    Get all files and their pages for a session.

    Args:
        session_id: The session ID.

    Returns:
        JSON array of files with nested page info.
    """
    db: DBClient = ctx.request_context.lifespan_context
    files = await get_session_files(db, session_id)
    return json.dumps(files, default=str)


def main() -> None:
    transport = "stdio"
    for i, arg in enumerate(sys.argv):
        if arg == "--transport" and i + 1 < len(sys.argv):
            transport = sys.argv[i + 1]
            break
    logger.info(
        f"Starting MCP SQLite server on {HOST}:{PORT} with {transport} transport"
    )
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
