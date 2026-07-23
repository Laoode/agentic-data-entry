"""Taskiq task for durable long-term memory writes.

When MEMORY_WRITE_MODE=taskiq, the orchestrator enqueues each turn here instead
of running mem0.add in-process. A Taskiq worker then runs the fact extraction, so
a slow or failed write never touches the request and queued writes survive an app
restart. MEMORY_WRITE_MODE=inline (the default) needs no worker and runs the
write in an app background task.

Worker start (must include this module so the task registers):
    taskiq worker app.services.extraction.queue.broker:broker \\
        app.services.extraction.queue.tasks app.services.core.memory_tasks
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.core.memory import MemoryService
from app.services.extraction.queue.broker import broker
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Worker-local MemoryService, built once and reused across task invocations.
_service: MemoryService | None = None


def _memory_service() -> MemoryService | None:
    """Return the worker's MemoryService, building it on first use (fail-soft)."""
    global _service
    if _service is None:
        _service = MemoryService.from_settings(get_settings())
    return _service


@broker.task(task_name="memory.persist", retry_on_error=True, max_retries=2, delay=2)
async def persist_memory_task(
    *,
    user_id: int,
    spreadsheet_id: str | None,
    user_text: str,
    assistant_text: str,
) -> dict[str, Any]:
    """Persist one turn to long-term memory in a worker.

    Runs strict so a genuine failure propagates and Taskiq retries it; a disabled
    memory config is a clean skip, not a failure.
    """
    service = _memory_service()
    if service is None:
        logger.warning("persist_memory_task: memory disabled in worker; dropping")
        return {"status": "skipped"}
    await service.remember(
        user_id, spreadsheet_id, user_text, assistant_text, strict=True
    )
    return {"status": "ok"}
