from typing import Any

from app.infra.db_client import DBClient


async def list_pages(db: DBClient, metadata_file_id: int) -> list[dict[str, Any]]:
    return await db.fetchall(
        "SELECT * FROM pages WHERE metadata_file_id = ? ORDER BY page",
        (metadata_file_id,),
    )


async def get_page(
    db: DBClient, metadata_file_id: int, page_number: int
) -> dict[str, Any] | None:
    return await db.fetchone(
        "SELECT * FROM pages WHERE metadata_file_id = ? AND page = ?",
        (metadata_file_id, page_number),
    )


async def create_page(
    db: DBClient,
    metadata_file_id: int,
    page_number: int,
) -> int:
    return await db.execute(
        """
        INSERT INTO pages (metadata_file_id, page, status)
        VALUES (?, ?, 'pending')
        """,
        (metadata_file_id, page_number),
    )


async def update_page(
    db: DBClient,
    page_id: int,
    agent_extracted: str | None = None,
    status: str | None = None,
    status_message: str | None = None,
) -> None:
    sets: list[str] = []
    params: list[Any] = []
    if agent_extracted is not None:
        sets.append("agent_extracted = ?")
        params.append(agent_extracted)
    if status is not None:
        sets.append("status = ?")
        params.append(status)
    if status_message is not None:
        sets.append("status_message = ?")
        params.append(status_message)
    if not sets:
        return
    params.append(page_id)
    await db.execute(f"UPDATE pages SET {', '.join(sets)} WHERE id = ?", tuple(params))
