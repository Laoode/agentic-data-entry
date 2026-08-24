from typing import Any

from app.infra.db_client import DBClient


async def list_pages(db: DBClient, metadata_file_id: int) -> list[dict[str, Any]]:
    """Return every page for an archived document."""
    return await db.fetchall(
        "SELECT * FROM pages WHERE metadata_file_id = $1 ORDER BY page",
        (metadata_file_id,),
    )


async def get_page(
    db: DBClient, metadata_file_id: int, page_number: int
) -> dict[str, Any] | None:
    """Return one page by document ID and page number."""
    return await db.fetchone(
        "SELECT * FROM pages WHERE metadata_file_id = $1 AND page = $2",
        (metadata_file_id, page_number),
    )


async def create_page(
    db: DBClient,
    metadata_file_id: int,
    page_number: int,
) -> int:
    """Create an archived page and return its ID."""
    page_id = await db.fetchval(
        """
        INSERT INTO pages (metadata_file_id, page, status)
        VALUES ($1, $2, 'pending')
        RETURNING id
        """,
        (metadata_file_id, page_number),
    )
    return int(page_id)


async def update_page(
    db: DBClient,
    page_id: int,
    agent_extracted: str | None = None,
    status: str | None = None,
    status_message: str | None = None,
) -> None:
    """Update the provided fields on an archived page."""
    sets: list[str] = []
    params: list[Any] = []
    if agent_extracted is not None:
        params.append(agent_extracted)
        sets.append(f"agent_extracted = ${len(params)}")
    if status is not None:
        params.append(status)
        sets.append(f"status = ${len(params)}")
    if status_message is not None:
        params.append(status_message)
        sets.append(f"status_message = ${len(params)}")
    if not sets:
        return
    params.append(page_id)
    await db.execute(
        f"UPDATE pages SET {', '.join(sets)} WHERE id = ${len(params)}", tuple(params)
    )
