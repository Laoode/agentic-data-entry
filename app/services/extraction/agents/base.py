"""Extraction Agent: GLM-OCR direct JSON -> validate -> persist."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.models.attachment import FileAttachment
from app.services.core.observability import LangfuseService
from app.services.extraction.agents.config import get_default_extraction
from app.services.extraction.infra.db_client import AppDBClient
from app.services.extraction.infra.ocr_client import OCRClient

logger = logging.getLogger(__name__)


@dataclass
class ExtractionResult:
    file_id: int
    file_name: str
    pages: list[dict[str, Any]] = field(default_factory=list)
    status: str = "completed"

    @property
    def summary(self) -> str:
        total_items = 0
        grand_total = 0
        for p in self.pages:
            extraction = p.get("extraction", {})
            total_items += len(extraction.get("items", []))
            gt = extraction.get("payment", {}).get("grand_total", 0)
            try:
                grand_total += int(gt) if gt not in ("", None) else 0
            except (ValueError, TypeError):
                pass
        return (
            f"File {self.file_name}: {len(self.pages)} page(s), "
            f"{total_items} item(s), total Rp {grand_total:,}"
        )


class ExtractionAgent:
    """GLM-OCR -> schema validation -> persistence."""

    def __init__(
        self,
        ocr_client: OCRClient,
        db_client: AppDBClient,
        langfuse: LangfuseService | None = None,
    ) -> None:
        self._ocr = ocr_client
        self._db = db_client
        self._langfuse = langfuse

    async def process(
        self,
        attachment: FileAttachment,
        session_id: int,
        user_id: int,
    ) -> ExtractionResult:
        logger.info(f"Processing attachment: {attachment.filename}")

        file_type = "pdf" if attachment.content_type == "application/pdf" else "image"

        span_cm = (
            self._langfuse.span(
                "extraction_agent.process",
                as_type="agent",
                input={
                    "file_name": attachment.filename,
                    "content_type": attachment.content_type,
                    "bytes": len(attachment.data),
                },
                metadata={
                    "session_id": session_id,
                    "user_id": user_id,
                    "file_type": file_type,
                },
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            result = await self._process_inner(attachment, session_id, user_id, file_type)
            if obs is not None:
                try:
                    obs.update(
                        output={
                            "file_id": result.file_id,
                            "pages": len(result.pages),
                            "status": result.status,
                            "summary": result.summary,
                        }
                    )
                except Exception:
                    pass
            return result

    async def _process_inner(
        self,
        attachment: FileAttachment,
        session_id: int,
        user_id: int,
        file_type: str,
    ) -> ExtractionResult:
        try:
            extractions = await self._ocr.process_file(
                attachment.data, attachment.content_type
            )
        except Exception as e:
            logger.error(f"OCR pipeline failed: {e}")
            file_id = await self._db.execute(
                """
                INSERT INTO metadata_file (session_id, user_id, type, file_name, total_pages, status, status_message)
                VALUES (?, ?, ?, ?, 0, 'failed', ?)
                """,
                (session_id, user_id, file_type, attachment.filename, str(e)),
            )
            return ExtractionResult(
                file_id=file_id, file_name=attachment.filename, pages=[], status="failed"
            )

        total_pages = len(extractions)
        file_id = await self._db.execute(
            """
            INSERT INTO metadata_file (session_id, user_id, type, file_name, total_pages, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (session_id, user_id, file_type, attachment.filename, total_pages),
        )

        pages_result: list[dict[str, Any]] = []
        failed_count = 0

        for page_num, raw_extraction in enumerate(extractions, 1):
            try:
                validated = self._validate_schema(raw_extraction)
                page_id = await self._db.execute(
                    """
                    INSERT INTO pages (metadata_file_id, page, agent_extracted, status, status_message)
                    VALUES (?, ?, ?, 'extracted', 'extracted')
                    """,
                    (file_id, page_num, json.dumps(validated, ensure_ascii=False)),
                )
                pages_result.append(
                    {"page_id": page_id, "page": page_num, "extraction": validated, "status": "extracted"}
                )
            except Exception as e:
                logger.error(f"Page {page_num} validation/persist failed: {e}")
                failed_count += 1
                await self._db.execute(
                    """
                    INSERT INTO pages (metadata_file_id, page, status, status_message)
                    VALUES (?, ?, 'failed', ?)
                    """,
                    (file_id, page_num, str(e)),
                )
                pages_result.append(
                    {"page": page_num, "extraction": get_default_extraction(), "status": "failed"}
                )

        if failed_count == 0:
            status, status_msg = "completed", f"All {total_pages} page(s) extracted"
        elif failed_count < total_pages:
            status, status_msg = "partial", f"{total_pages - failed_count}/{total_pages} page(s) extracted"
        else:
            status, status_msg = "failed", "All pages failed"

        await self._db.execute(
            "UPDATE metadata_file SET status = ?, status_message = ? WHERE id = ?",
            (status, status_msg, file_id),
        )

        return ExtractionResult(
            file_id=file_id, file_name=attachment.filename, pages=pages_result, status=status
        )

    def _validate_schema(self, data: dict[str, Any]) -> dict[str, Any]:
        """Fill missing fields with schema defaults; coerce obvious type mismatches."""
        default = get_default_extraction()
        out: dict[str, Any] = {}

        info = dict(data.get("info") or {})
        for key, default_val in default["info"].items():
            info.setdefault(key, default_val)
        out["info"] = info

        items_in = data.get("items") or []
        out["items"] = [self._fill_defaults(item, default["items"][0]) for item in items_in]

        returned_in = data.get("returned_items") or []
        out["returned_items"] = [
            self._fill_defaults(item, default["returned_items"][0]) for item in returned_in
        ]

        payment = dict(data.get("payment") or {})
        for key, default_val in default["payment"].items():
            payment.setdefault(key, default_val)
        out["payment"] = payment

        return out

    @staticmethod
    def _fill_defaults(item: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
        result = {}
        for k, v in template.items():
            result[k] = item.get(k, v)
        return result


from contextlib import contextmanager


@contextmanager
def _nullspan():
    yield None
