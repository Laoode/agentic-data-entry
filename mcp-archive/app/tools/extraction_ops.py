import json
from typing import Any

from app.infra.db_client import DBClient


async def get_extraction(
    db: DBClient, metadata_file_id: int, page_number: int
) -> dict[str, Any] | None:
    row = await db.fetchone(
        "SELECT agent_extracted FROM pages WHERE metadata_file_id = ? AND page = ?",
        (metadata_file_id, page_number),
    )
    if row and row["agent_extracted"]:
        return json.loads(row["agent_extracted"])
    return None


async def save_extraction(
    db: DBClient,
    page_id: int,
    extraction: dict[str, Any],
) -> None:
    await db.execute(
        "UPDATE pages SET agent_extracted = ?, status = 'extracted' WHERE id = ?",
        (json.dumps(extraction, ensure_ascii=False), page_id),
    )


async def get_session_files(db: DBClient, session_id: int) -> list[dict[str, Any]]:
    """Get all files with their page/extraction summary for a session."""
    files = await db.fetchall(
        "SELECT * FROM metadata_file WHERE session_id = ? ORDER BY created_at",
        (session_id,),
    )
    result = []
    for f in files:
        pages = await db.fetchall(
            "SELECT id, page, status, status_message FROM pages WHERE metadata_file_id = ? ORDER BY page",
            (f["id"],),
        )
        result.append({**f, "pages": pages})
    return result
