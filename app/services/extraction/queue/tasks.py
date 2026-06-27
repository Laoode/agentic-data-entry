"""Worker-side extraction tasks.

A task takes a blob_page reference (resolved via the private file_blob_page
table) and runs OCR + cache persistence. The orchestrator publishes one
task per page; results land in:
    - blob_extraction (SQLite L2 cache)
    - dedup cache (Redis L1)
    - pages.agent_extracted (LLM-visible)
    - pubsub channel `extraction:file:<file_id>:progress` for SSE streaming

Idempotency: each task is keyed by (user_id, page_blake3). A duplicate
fire is harmless — both writes converge to the same JSON.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.exceptions import OCRError
from app.services.extraction.agents.config import get_default_extraction
from app.services.extraction.agents.schema import validate_and_merge
from app.services.extraction.queue.broker import broker
from app.services.extraction.queue.state import get_context

logger = logging.getLogger(__name__)


PROGRESS_CHANNEL_FMT = "extraction:file:{file_id}:progress"


@broker.task(
    task_name="ocr.extract_page",
    retry_on_error=True,
    max_retries=3,
    delay=2,
)
async def extract_page_task(
    *,
    user_id: int,
    file_id: int,
    blob_id: int,
    page: int,
) -> dict[str, Any]:
    """Run OCR for one page. Publishes a progress event regardless of outcome
    so the orchestrator can stream completion to the client.
    """
    ctx = get_context()
    db = ctx.db
    cache = ctx.cache
    store = ctx.store
    ocr = ctx.ocr

    # Resolve page reference (hash + minio key) from the private join table.
    row = await db.fetchone(
        """
        SELECT page_blake3, page_minio_key
        FROM file_blob_page
        WHERE blob_id = ? AND page = ?
        """,
        (blob_id, page),
    )
    if row is None:
        msg = f"file_blob_page missing blob_id={blob_id} page={page}"
        logger.error(msg)
        await _publish_progress(cache, file_id, page, status="failed", error=msg)
        return {"status": "failed", "error": msg}

    page_blake3 = row["page_blake3"]
    page_key = row["page_minio_key"]

    # L1
    cached = await _safe_get(cache.get_extraction, user_id, page_blake3)
    if cached is not None:
        await _persist_page_row(db, file_id, page, cached, source="redis")
        await _publish_progress(
            cache, file_id, page, status="cached", cache_layer="redis"
        )
        return {"status": "cached", "cache_layer": "redis"}

    # L2
    sqlite_row = await db.get_cached_extraction(user_id, page_blake3)
    if sqlite_row is not None:
        try:
            extraction = json.loads(sqlite_row["extraction_json"])
            await _safe_set(cache.set_extraction, user_id, page_blake3, extraction)
            await _persist_page_row(db, file_id, page, extraction, source="sqlite")
            await _publish_progress(
                cache, file_id, page, status="cached", cache_layer="sqlite"
            )
            return {"status": "cached", "cache_layer": "sqlite"}
        except json.JSONDecodeError:
            logger.warning("blob_extraction row corrupted; re-extracting")

    # Miss → fetch JPG from MinIO and call OCR
    try:
        jpg = await store.get(page_key)
    except Exception as e:
        msg = f"object_store.get({page_key!r}) failed: {e}"
        logger.error(msg)
        await _persist_failure(db, file_id, page, msg)
        await _publish_progress(cache, file_id, page, status="failed", error=msg)
        return {"status": "failed", "error": msg}

    try:
        raw = await ocr.extract_from_image(jpg)
        validated = validate_and_merge(raw)
    except OCRError as e:
        await _persist_failure(db, file_id, page, str(e))
        await _publish_progress(cache, file_id, page, status="failed", error=str(e))
        return {"status": "failed", "error": str(e)}

    await db.upsert_extraction(
        user_id=user_id,
        page_blake3=page_blake3,
        extraction_json=json.dumps(validated, ensure_ascii=False),
        ocr_model=ocr.model_id,
        schema_version=ocr.schema_version,
    )
    await _safe_set(cache.set_extraction, user_id, page_blake3, validated)
    await _persist_page_row(db, file_id, page, validated, source=None)
    await _publish_progress(cache, file_id, page, status="extracted")
    return {"status": "extracted"}


async def _persist_page_row(
    db, file_id: int, page: int, extraction: dict[str, Any], *, source: str | None
) -> None:
    """Upsert into the LLM-visible `pages` table.

    We store one row per (file_id, page); reruns (e.g. retries) replace it.
    """
    existing = await db.fetchone(
        "SELECT id FROM pages WHERE metadata_file_id = ? AND page = ?",
        (file_id, page),
    )
    msg = "cached" if source else "extracted"
    if existing is None:
        await db.execute(
            """
            INSERT INTO pages (metadata_file_id, page, agent_extracted, status, status_message)
            VALUES (?, ?, ?, 'extracted', ?)
            """,
            (file_id, page, json.dumps(extraction, ensure_ascii=False), msg),
        )
    else:
        await db.execute(
            """
            UPDATE pages
            SET agent_extracted = ?, status = 'extracted', status_message = ?
            WHERE id = ?
            """,
            (json.dumps(extraction, ensure_ascii=False), msg, existing["id"]),
        )


async def _persist_failure(db, file_id: int, page: int, message: str) -> None:
    existing = await db.fetchone(
        "SELECT id FROM pages WHERE metadata_file_id = ? AND page = ?",
        (file_id, page),
    )
    if existing is None:
        await db.execute(
            """
            INSERT INTO pages (metadata_file_id, page, status, status_message)
            VALUES (?, ?, 'failed', ?)
            """,
            (file_id, page, message),
        )
    else:
        await db.execute(
            "UPDATE pages SET status = 'failed', status_message = ? WHERE id = ?",
            (message, existing["id"]),
        )


async def _publish_progress(
    cache,
    file_id: int,
    page: int,
    *,
    status: str,
    cache_layer: str | None = None,
    error: str | None = None,
) -> None:
    channel = PROGRESS_CHANNEL_FMT.format(file_id=file_id)
    payload = {
        "file_id": file_id,
        "page": page,
        "status": status,
        "cache_layer": cache_layer,
        "error": error,
    }
    try:
        await cache.client.publish(channel, json.dumps(payload, ensure_ascii=False))
    except Exception as e:
        logger.warning("publish progress failed (%s): %s", channel, e)


async def _safe_get(getter, *args):
    try:
        return await getter(*args)
    except Exception as e:
        logger.warning("cache get failed: %s", e)
        return None


async def _safe_set(setter, *args):
    try:
        await setter(*args)
    except Exception as e:
        logger.warning("cache set failed: %s", e)
