"""Pubsub-based progress aggregator for queued extraction tasks.

Workers publish a JSON event per page completion to
    extraction:file:<file_id>:progress

The orchestrator subscribes to all relevant channels for a turn, yields each
event to the SSE client, and stops once the expected page count has been
seen across all files. A timeout bounds the wait so a stuck worker can't
hang the response — the caller surfaces a `deferred` event for missing
pages instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import AsyncIterator

import redis.asyncio as aioredis

from app.services.extraction.queue.tasks import PROGRESS_CHANNEL_FMT

logger = logging.getLogger(__name__)


@dataclass
class ProgressEvent:
    file_id: int
    page: int
    status: str  # 'extracted' | 'cached' | 'failed'
    cache_layer: str | None = None
    error: str | None = None


async def stream_progress(
    redis_client: aioredis.Redis,
    *,
    file_pages: dict[int, int],   # file_id -> expected page count
    timeout_seconds: float,
) -> AsyncIterator[ProgressEvent]:
    """Yield ProgressEvent per worker publish until all expected pages have
    reported or the global timeout expires.

    Caller is responsible for translating events into SSE frames and for
    handling the timeout gap (i.e. publishing 'deferred' for pages that
    didn't complete in time).
    """
    if not file_pages:
        return

    pubsub = redis_client.pubsub()
    channels = [
        PROGRESS_CHANNEL_FMT.format(file_id=fid) for fid in file_pages
    ]
    await pubsub.subscribe(*channels)

    expected = sum(file_pages.values())
    seen: dict[int, int] = {fid: 0 for fid in file_pages}

    try:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while sum(seen.values()) < expected:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                logger.warning(
                    "stream_progress timed out: seen=%s expected=%d",
                    seen,
                    expected,
                )
                return
            try:
                msg = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True),
                    timeout=remaining,
                )
            except asyncio.TimeoutError:
                logger.warning("stream_progress: pubsub deadline reached")
                return
            if msg is None or msg.get("type") != "message":
                continue
            try:
                payload = json.loads(msg["data"])
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("malformed progress payload: %s", e)
                continue
            event = ProgressEvent(
                file_id=int(payload["file_id"]),
                page=int(payload["page"]),
                status=payload.get("status", "unknown"),
                cache_layer=payload.get("cache_layer"),
                error=payload.get("error"),
            )
            if event.file_id not in seen:
                # Not for us; ignore (possible if cross-test bleed-through).
                continue
            seen[event.file_id] += 1
            yield event
    finally:
        try:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()
        except Exception:  # pragma: no cover
            pass
