"""Long-term memory for Klaudia, backed by mem0 OSS (self-hosted).

This is the soft semantic layer (durable preferences, sheet aliases, entity
schemas, episodes), distinct from the deterministic Tier 1 continuity read.
mem0 does LLM fact-extraction + conflict-aware update on write and embedding
retrieval on read; we self-host all of it: pgvector on the app's Postgres,
DeepSeek for extraction, and services/embed for embeddings.

Discipline:
  - Memory content is stored in ENGLISH (LLM extraction accuracy), regardless of
    Klaudia's reply language.
  - Hard tenant boundary: every call is scoped by user_id. Cross-user recall is
    a leak. Spreadsheet lives in metadata so a deleted spreadsheet's memories
    can be purged (cascade), without splitting the entity scope that recall
    relies on.
  - Everything is fail-soft: memory never breaks a chat turn. Writes run in the
    background (the reply is already sent); reads degrade to empty context.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Protocol

from config.settings import Settings
from klaudia.core.supervisor.tools.context import build_memory_context

# mem0 reads MEM0_TELEMETRY at import time; keep user financial data on-prem by
# defaulting telemetry off before mem0 is ever imported (lazy, in from_settings).
os.environ.setdefault("MEM0_TELEMETRY", "False")

logger = logging.getLogger(__name__)

# English, finance-tuned extraction guidance for mem0's fact extractor. Capture
# durable, reusable facts; leave transactional numbers to the ledger.
MEMORY_EXTRACTION_INSTRUCTIONS = """
You are the long-term memory of a finance data-entry assistant. Store memories in
English regardless of the conversation language.

EXTRACT and remember durable, reusable facts:
- User preferences and rules (e.g. "categorizes GoFood as Transport", "fiscal
  month starts on the 25th", "prefers amounts without decimals").
- Names/aliases the user uses for their sheets or spreadsheets.
- The structure of a sheet the user works with (its columns/headers).
- Recurring merchants, categories, or workflows the user relies on.

DO NOT store:
- One-off transaction amounts, dates, or receipt line items (those live in the
  ledger, not memory).
- Transient chatter, greetings, or acknowledgements.
- Anything the user did not actually assert as a lasting fact.
""".strip()


class MemoryBackend(Protocol):
    """Subset of mem0 AsyncMemory the service depends on (so tests fake it)."""

    async def add(
        self,
        messages: Any,
        *,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        infer: bool = True,
    ) -> Any: ...

    async def search(
        self, query: str, *, filters: dict[str, Any] | None = None, top_k: int = 20
    ) -> Any: ...

    async def get_all(
        self, *, filters: dict[str, Any] | None = None, top_k: int = 20
    ) -> Any: ...

    async def delete(self, memory_id: str) -> Any: ...

    async def reset(self) -> Any: ...


def _results(payload: Any) -> list[dict[str, Any]]:
    """Normalize mem0's {"results": [...]} (or a bare list) to a list of dicts."""
    if isinstance(payload, dict):
        return payload.get("results") or []
    return payload or []


class MemoryService:
    """Thin, fail-soft wrapper over a mem0 AsyncMemory backend."""

    def __init__(self, backend: MemoryBackend, *, top_k: int = 6) -> None:
        self._m = backend
        self._top_k = top_k

    @classmethod
    def from_settings(cls, settings: Settings) -> "MemoryService | None":
        """Build a MemoryService, or None if mem0 cannot be initialized.

        Fail-soft: any construction error (missing deps, DB down, bad config)
        disables memory rather than breaking app startup.
        """
        try:
            from mem0 import AsyncMemory

            config = {
                "llm": {
                    "provider": "openai",
                    "config": {
                        "model": settings.memory_llm_model,
                        "openai_base_url": settings.deepseek_base_url,
                        "api_key": settings.deepseek_api_key,
                        "temperature": 0.0,
                    },
                },
                "embedder": {
                    "provider": "openai",
                    "config": {
                        "model": settings.memory_embed_model,
                        "openai_base_url": settings.memory_embed_base_url,
                        "api_key": "not-needed",
                        "embedding_dims": settings.memory_embed_dims,
                    },
                },
                "vector_store": {
                    "provider": "pgvector",
                    "config": {
                        "connection_string": settings.database_url,
                        "collection_name": settings.memory_collection,
                        "embedding_model_dims": settings.memory_embed_dims,
                    },
                },
                "custom_instructions": MEMORY_EXTRACTION_INSTRUCTIONS,
            }
            backend = AsyncMemory.from_config(config)
        except Exception as exc:
            logger.warning("Memory disabled (mem0 init failed, fail-soft): %s", exc)
            return None
        logger.info(
            "Memory enabled: mem0 pgvector collection=%s embed=%s llm=%s",
            settings.memory_collection,
            settings.memory_embed_model,
            settings.memory_llm_model,
        )
        return cls(backend, top_k=settings.memory_top_k)

    async def recall(self, user_id: int, query: str) -> str:
        """Return a formatted memory-context block for the system prompt.

        Fail-soft: returns "" on any error (e.g. embed service down).
        """
        if not query:
            return ""
        try:
            payload = await self._m.search(
                query, filters={"user_id": str(user_id)}, top_k=self._top_k
            )
        except Exception as exc:
            logger.warning("Memory recall failed (fail-soft): %s", exc)
            return ""
        memories = [item.get("memory", "") for item in _results(payload)]
        return build_memory_context(memories)

    async def remember(
        self,
        user_id: int,
        spreadsheet_id: str | None,
        user_text: str,
        assistant_text: str,
        *,
        strict: bool = False,
    ) -> None:
        """Persist a turn as long-term memory (fact extraction runs in mem0).

        Called in the background: the reply is already sent, so latency and
        errors here never reach the user.

        Args:
            strict: When True, re-raise on failure so a Taskiq worker can retry.
                The inline path leaves it False (swallow, never break a turn).
        """
        messages = [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ]
        metadata = {"spreadsheet_id": spreadsheet_id} if spreadsheet_id else None
        try:
            await self._m.add(messages, user_id=str(user_id), metadata=metadata)
        except Exception as exc:
            logger.warning("Memory write failed (fail-soft): %s", exc)
            if strict:
                raise

    async def purge_spreadsheet(self, user_id: int, spreadsheet_id: str) -> int:
        """Delete every memory tagged with a spreadsheet (cascade on delete)."""
        return await self._purge(
            user_id,
            lambda item: (
                (item.get("metadata") or {}).get("spreadsheet_id") == spreadsheet_id
            ),
        )

    async def purge_sheet(self, user_id: int, spreadsheet_id: str, sheet: str) -> int:
        """Delete memories tied to a specific sheet in a spreadsheet.

        Matches on explicit sheet metadata or a mention of the sheet name in the
        memory text (best-effort: most memories are not tagged per-sheet).
        """
        needle = sheet.lower()

        def matches(item: dict[str, Any]) -> bool:
            meta = item.get("metadata") or {}
            if meta.get("spreadsheet_id") != spreadsheet_id:
                return False
            return (
                meta.get("sheet") == sheet
                or needle in (item.get("memory") or "").lower()
            )

        return await self._purge(user_id, matches)

    async def reset(self) -> None:
        """Clear all memories (used by the eval harness for case isolation)."""
        await self._m.reset()

    async def _purge(self, user_id: int, predicate) -> int:
        """Delete a user's memories matching a predicate. Returns count deleted."""
        try:
            payload = await self._m.get_all(
                filters={"user_id": str(user_id)}, top_k=1000
            )
        except Exception as exc:
            logger.warning("Memory purge get_all failed (fail-soft): %s", exc)
            return 0
        deleted = 0
        for item in _results(payload):
            if not predicate(item):
                continue
            memory_id = item.get("id")
            try:
                await self._m.delete(memory_id)
                deleted += 1
            except Exception as exc:
                logger.warning("Memory delete failed for %s: %s", memory_id, exc)
        return deleted
