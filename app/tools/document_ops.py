from typing import Any

from app.infra.db_client import DBClient


async def get_document(db: DBClient, document_id: int) -> dict[str, Any] | None:
    return await db.fetchone(
        "SELECT * FROM metadata_file WHERE id = ?", (document_id,)
    )


async def list_documents(
    db: DBClient, session_id: int
) -> list[dict[str, Any]]:
    return await db.fetchall(
        "SELECT * FROM metadata_file WHERE session_id = ? ORDER BY created_at",
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
    return await db.execute(
        """
        INSERT INTO metadata_file (session_id, user_id, type, file_name, total_pages, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        """,
        (session_id, user_id, file_type, file_name, total_pages),
    )


async def update_document_status(
    db: DBClient,
    document_id: int,
    status: str,
    status_message: str | None = None,
) -> None:
    await db.execute(
        "UPDATE metadata_file SET status = ?, status_message = ? WHERE id = ?",
        (status, status_message, document_id),
    )
