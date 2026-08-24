from typing import Any

from app.infra.db_client import DBClient


async def get_document(db: DBClient, document_id: int) -> dict[str, Any] | None:
    """Return one archived document by ID."""
    return await db.fetchone(
        "SELECT * FROM metadata_file WHERE id = $1", (document_id,)
    )


async def list_documents(db: DBClient, session_id: int) -> list[dict[str, Any]]:
    """Return the documents in a session."""
    return await db.fetchall(
        "SELECT * FROM metadata_file WHERE session_id = $1 ORDER BY created_at",
        (session_id,),
    )


async def create_document(
    db: DBClient,
    session_id: int,
    user_id: int,
    file_type: str,
    file_name: str,
    total_pages: int,
) -> int:
    """Create an archived document and return its ID."""
    document_id = await db.fetchval(
        """
        INSERT INTO metadata_file (session_id, user_id, type, file_name, total_pages, status)
        VALUES ($1, $2, $3, $4, $5, 'pending')
        RETURNING id
        """,
        (session_id, user_id, file_type, file_name, total_pages),
    )
    return int(document_id)


async def update_document_status(
    db: DBClient,
    document_id: int,
    status: str,
    status_message: str | None = None,
) -> None:
    """Update an archived document's status."""
    await db.execute(
        "UPDATE metadata_file SET status = $1, status_message = $2 WHERE id = $3",
        (status, status_message, document_id),
    )
