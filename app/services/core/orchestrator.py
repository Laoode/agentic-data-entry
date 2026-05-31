import logging
import re
import time
from contextlib import contextmanager
from typing import Any, AsyncIterator

from app.models.attachment import FileAttachment
from app.models.chat import (
    ChatMetadata,
    KlaudiaMessage,
    KlaudiaResponse,
)
from app.services.core.container import KlaudiaContainer
from app.services.core.prompts import KLAUDIA_SYSTEM_PROMPT
from app.services.extraction.infra.normalizer import is_pdf, is_supported_image
from klaudia.core.supervisor.tools.context import build_extraction_context, build_session_context

logger = logging.getLogger(__name__)


@contextmanager
def _nullctx():
    yield None


def _classify_attachments(
    attachments: list[FileAttachment],
) -> tuple[int, int, list[FileAttachment]]:
    """Return (image_count, pdf_count, unknown_attachments).

    Unknown = neither image nor pdf; rejected pre-OCR. Used by the orchestrator
    to enforce the 'max 5 images' rule before any GPU work.
    """
    images = 0
    pdfs = 0
    unknown: list[FileAttachment] = []
    for att in attachments:
        if is_pdf(att.filename, att.content_type):
            pdfs += 1
        elif is_supported_image(att.filename, att.content_type):
            images += 1
        else:
            unknown.append(att)
    return images, pdfs, unknown


def _check_attachment_shape(
    attachments: list[FileAttachment], max_images: int
) -> str | None:
    """Return rejection message if shape violates upload rules, else None.

    Rules:
        - <= 1 PDF
        - PDF and images cannot mix in the same turn
        - <= max_images standalone images
        - All attachments must be a supported image or pdf
    """
    images, pdfs, unknown = _classify_attachments(attachments)
    if pdfs > 1:
        return "Hanya satu PDF per pesan ya. Coba kirim ulang dengan 1 PDF saja."
    if pdfs == 1 and images > 0:
        return "Mau PDF atau gambar — tidak campur ya. Pilih salah satu."
    if images > max_images:
        return f"Maksimal {max_images} gambar per pesan. Ada {images} gambar terlampir."
    if unknown:
        names = ", ".join(a.filename for a in unknown)
        return f"Format tidak didukung: {names}. Upload JPG/PNG/HEIC/PDF saja."
    return None


class KlaudiaOrchestrator:
    """Main conversation orchestrator.

    Pipeline: context -> guardrails -> route (extraction/supervisor) -> response
    """

    def __init__(self, container: KlaudiaContainer) -> None:
        self._c = container
        self._extraction_agent = container.extraction_agent
        self._langfuse = container.langfuse

    async def process(
        self,
        messages: list[KlaudiaMessage],
        session_id: int | None,
        user_id: int,
        user_name: str = "User",
    ) -> KlaudiaResponse:
        start = time.time()

        # 1. Ensure session exists
        if session_id is None:
            session_id = await self._c.db_client.create_session(user_id)

        langfuse = self._langfuse
        trace_cm = (
            langfuse.trace_attributes(
                session_id=session_id, user_id=user_id, tags=["klaudia", "chat"]
            )
            if langfuse is not None
            else _nullctx()
        )
        span_cm = (
            langfuse.span(
                "klaudia.process",
                as_type="agent",
                input={"user_text": messages[-1].content, "user_name": user_name},
                metadata={"session_id": session_id, "user_id": user_id},
            )
            if langfuse is not None
            else _nullctx()
        )

        with trace_cm, span_cm as turn_obs:
            response = await self._process_inner(
                messages, session_id, user_id, user_name, start
            )
            if turn_obs is not None:
                try:
                    turn_obs.update(
                        output={
                            "content": response.message.content,
                            "tools_used": response.tools_used,
                            "processing_time_ms": response.processing_time_ms,
                        }
                    )
                except Exception:
                    pass

            return response

    async def _process_inner(
        self,
        messages: list[KlaudiaMessage],
        session_id: int,
        user_id: int,
        user_name: str,
        start: float,
    ) -> KlaudiaResponse:

        # 2. Get last user message text
        user_msg = messages[-1]
        user_text = user_msg.content

        # 3. Guardrails (input)
        guard_result = await self._c.guardrails.validate_input(user_text)
        if not guard_result.passed:
            return self._rejection_response(
                session_id, guard_result.rejection_message, start
            )

        # 4. Check for attachments. Accumulate per-attachment results so multi-
        # image uploads (1..N images, where N <= MAX_IMAGES_PER_UPLOAD) are
        # surfaced to the supervisor in upload order.
        extraction_results: list[dict[str, Any]] = []
        has_attachment = user_msg.attachments and len(user_msg.attachments) > 0
        if has_attachment:
            attachments = list(user_msg.attachments)
            max_images = self._c.settings.max_images_per_upload
            rejection = _check_attachment_shape(attachments, max_images)
            if rejection is not None:
                return self._rejection_response(session_id, rejection, start)

            # PRV: queue depth gate (only meaningful in async mode but cheap to check)
            prv_msg = await self._check_queue_pressure()
            if prv_msg is not None:
                return self._rejection_response(session_id, prv_msg, start)

            for att in attachments:
                # Note: process() (sync mode) and the async path both end up
                # writing to the same DB tables. We always go through
                # ExtractionAgent here because process() is non-streaming and
                # callers expect data ready on return.
                result = await self._extraction_agent.process(att, session_id, user_id)
                extraction_results.append({
                    "file_id": result.file_id,
                    "file_name": result.file_name,
                    "pages": result.pages,
                    "status": result.status,
                    "summary": result.summary,
                })

        # 5. Build context
        # NOTE: history is fetched BEFORE saving the current user msg so the
        # current msg is appended exactly once at the tail of llm_messages.
        # Saving first would double the user turn (history + explicit append),
        # which confuses the LLM (two identical consecutive user messages).
        import asyncio
        history, session_files_raw, available_sheets = await asyncio.gather(
            self._c.db_client.get_conversation_history(session_id, limit=10),
            self._c.db_client.get_session_files(session_id),
            self._c.supervisor.get_available_sheets(),
        )

        meta = ChatMetadata(user_name=user_name)
        session_files_ctx = build_session_context(session_files_raw)
        system_prompt = KLAUDIA_SYSTEM_PROMPT.format(
            session_files=session_files_ctx,
            available_sheets=available_sheets or "Tidak ada sheet tersedia.",
            date=meta.date,
            time=meta.time,
            timezone=meta.timezone,
        )

        # Build messages for supervisor
        llm_messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]

        # Add history (reversed to chronological)
        for row in reversed(history):
            llm_messages.append({
                "role": row["sender"],
                "content": row["message_text"],
            })

        # Add extraction context if present (one block per attachment, in order)
        for ext in extraction_results:
            extraction_ctx = build_extraction_context(ext)
            llm_messages.append({"role": "user", "content": extraction_ctx})

        # Add current user message
        llm_messages.append({"role": "user", "content": user_text})

        # 6. Persist the current user message NOW that history has been read.
        await self._c.db_client.save_message(session_id, user_id, "user", user_text)

        # 7. Invoke supervisor. Pass last extraction so legacy callers that
        # expect a single extraction_data still see something; the full list
        # is already encoded in llm_messages above.
        last_extraction = extraction_results[-1] if extraction_results else None
        agent_response = await self._c.supervisor.process_conversation(
            messages=llm_messages,
            extraction_data=last_extraction,
            session_id=session_id,
            user_id=user_id,
        )

        # 8. Post-process: remove thinking tokens
        content = re.sub(r"<think>.*?</think>", "", agent_response.content, flags=re.DOTALL).strip()

        # 9. Output guardrails
        output_guard = await self._c.guardrails.validate_output(content)
        if not output_guard.passed:
            content = output_guard.rejection_message

        # 10. Save assistant message
        await self._c.db_client.save_message(session_id, user_id, "assistant", content)
        await self._c.db_client.update_session_timestamp(session_id)

        elapsed = int((time.time() - start) * 1000)
        return KlaudiaResponse(
            message=KlaudiaMessage(role="assistant", content=content),
            session_id=session_id,
            processing_time_ms=elapsed,
            tools_used=agent_response.tools_called,
            metadata=meta,
        )

    async def stream(
        self,
        messages: list[KlaudiaMessage],
        session_id: int | None,
        user_id: int,
        user_name: str = "User",
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream the pipeline as structured SSE-ready events.

        Event shape: {"type": <name>, "data": <payload>}
        Types: session, guardrail, extraction, step, tool, token, done, error.
        """
        start = time.time()

        try:
            if session_id is None:
                session_id = await self._c.db_client.create_session(user_id)
            yield {"type": "session", "data": {"session_id": session_id}}

            langfuse = self._langfuse
            trace_cm = (
                langfuse.trace_attributes(
                    session_id=session_id, user_id=user_id, tags=["klaudia", "chat", "stream"]
                )
                if langfuse is not None
                else _nullctx()
            )
            span_cm = (
                langfuse.span(
                    "klaudia.stream",
                    as_type="agent",
                    input={"user_text": messages[-1].content, "user_name": user_name},
                    metadata={"session_id": session_id, "user_id": user_id},
                )
                if langfuse is not None
                else _nullctx()
            )
            # Intentionally NOT using `with` as an async generator wrapper so events
            # keep streaming; manually enter and ensure exit in finally block.
            _entered_trace = trace_cm.__enter__()
            turn_obs = span_cm.__enter__()

            user_msg = messages[-1]
            user_text = user_msg.content

            yield {"type": "guardrail", "data": {"stage": "input", "status": "checking"}}
            guard_result = await self._c.guardrails.validate_input(user_text)
            if not guard_result.passed:
                rejection = guard_result.rejection_message
                yield {
                    "type": "guardrail",
                    "data": {"stage": "input", "status": "rejected", "message": rejection},
                }
                yield {"type": "token", "data": {"text": rejection}}
                elapsed = int((time.time() - start) * 1000)
                yield {
                    "type": "done",
                    "data": {
                        "session_id": session_id,
                        "processing_time_ms": elapsed,
                        "tools_used": [],
                        "content": rejection,
                    },
                }
                return
            yield {"type": "guardrail", "data": {"stage": "input", "status": "passed"}}

            # User msg is persisted AFTER llm_messages is built (see the
            # equivalent step in process()) so history doesn't double-count it.

            extraction_results: list[dict[str, Any]] = []
            has_attachment = user_msg.attachments and len(user_msg.attachments) > 0
            if has_attachment:
                attachments = list(user_msg.attachments)
                max_images = self._c.settings.max_images_per_upload
                rejection_msg = _check_attachment_shape(attachments, max_images)
                if rejection_msg is not None:
                    yield {
                        "type": "guardrail",
                        "data": {"stage": "attachment", "status": "rejected", "message": rejection_msg},
                    }
                    yield {"type": "token", "data": {"text": rejection_msg}}
                    elapsed = int((time.time() - start) * 1000)
                    yield {
                        "type": "done",
                        "data": {
                            "session_id": session_id,
                            "processing_time_ms": elapsed,
                            "tools_used": [],
                            "content": rejection_msg,
                        },
                    }
                    return

                prv_msg = await self._check_queue_pressure()
                if prv_msg is not None:
                    yield {
                        "type": "guardrail",
                        "data": {"stage": "queue", "status": "rejected", "message": prv_msg},
                    }
                    yield {"type": "token", "data": {"text": prv_msg}}
                    elapsed = int((time.time() - start) * 1000)
                    yield {
                        "type": "done",
                        "data": {
                            "session_id": session_id,
                            "processing_time_ms": elapsed,
                            "tools_used": [],
                            "content": prv_msg,
                        },
                    }
                    return

                async for event in self._run_extraction_stream(
                    attachments, session_id, user_id
                ):
                    if event.get("__final__"):
                        extraction_results = event["payload"]
                        continue
                    yield event
            
            import asyncio
            history, session_files_raw, available_sheets = await asyncio.gather(
                self._c.db_client.get_conversation_history(session_id, limit=10),
                self._c.db_client.get_session_files(session_id),
                self._c.supervisor.get_available_sheets(),
            )

            meta = ChatMetadata(user_name=user_name)
            session_files_ctx = build_session_context(session_files_raw)
            system_prompt = KLAUDIA_SYSTEM_PROMPT.format(
                session_files=session_files_ctx,
                available_sheets=available_sheets or "Tidak ada sheet tersedia.",
                date=meta.date,
                time=meta.time,
                timezone=meta.timezone,
            )

            llm_messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
            for row in reversed(history):
                llm_messages.append({"role": row["sender"], "content": row["message_text"]})
            for ext in extraction_results:
                extraction_ctx = build_extraction_context(ext)
                llm_messages.append({"role": "user", "content": extraction_ctx})
            llm_messages.append({"role": "user", "content": user_text})

            await self._c.db_client.save_message(session_id, user_id, "user", user_text)

            last_extraction = extraction_results[-1] if extraction_results else None
            final_content = ""
            tools_used: list[str] = []
            any_token_emitted = False  # track whether supervisor emitted token events
            async for event in self._c.supervisor.stream_conversation(
                messages=llm_messages,
                extraction_data=last_extraction,
                session_id=session_id,
                user_id=user_id,
            ):
                if event["type"] == "final":
                    final_content = event["data"]["content"]
                    tools_used = event["data"]["tools_called"]
                    continue
                if event["type"] == "token":
                    any_token_emitted = True
                yield event

            content = re.sub(r"<think>.*?</think>", "", final_content, flags=re.DOTALL).strip()

            if not any_token_emitted and content:
                # RouterWithResponse inline FINISH path: supervisor assembled the
                # complete answer in one LLM call and emitted no token events.
                # Stream the content word-by-word now, running output_guard
                # concurrently so the guard adds zero latency to token delivery.
                output_guard_task = asyncio.create_task(
                    self._c.guardrails.validate_output(content)
                )
                words = content.split(" ")
                for i, word in enumerate(words):
                    token_text = word if i == len(words) - 1 else word + " "
                    yield {"type": "token", "data": {"text": token_text}}
                output_guard = await output_guard_task
            else:
                # final_llm path: tokens already streamed by supervisor.
                # Run output_guard sequentially (guard delay is post-stream, acceptable).
                output_guard = await self._c.guardrails.validate_output(content)

            if not output_guard.passed:
                content = output_guard.rejection_message
                yield {
                    "type": "guardrail",
                    "data": {"stage": "output", "status": "rejected", "message": content},
                }

            await self._c.db_client.save_message(session_id, user_id, "assistant", content)
            await self._c.db_client.update_session_timestamp(session_id)

            elapsed = int((time.time() - start) * 1000)
            if turn_obs is not None:
                try:
                    turn_obs.update(
                        output={
                            "content": content,
                            "tools_used": tools_used,
                            "processing_time_ms": elapsed,
                        }
                    )
                except Exception:
                    pass
            yield {
                "type": "done",
                "data": {
                    "session_id": session_id,
                    "processing_time_ms": elapsed,
                    "tools_used": tools_used,
                    "content": content,
                },
            }
            span_cm.__exit__(None, None, None)
            trace_cm.__exit__(None, None, None)

        except Exception as exc:
            logger.exception("Stream pipeline error")
            try:
                span_cm.__exit__(type(exc), exc, exc.__traceback__)
                trace_cm.__exit__(type(exc), exc, exc.__traceback__)
            except Exception:
                pass
            yield {"type": "error", "data": {"message": str(exc)}}

    def _rejection_response(
        self, session_id: int, message: str, start: float
    ) -> KlaudiaResponse:
        elapsed = int((time.time() - start) * 1000)
        return KlaudiaResponse(
            message=KlaudiaMessage(role="assistant", content=message),
            session_id=session_id,
            processing_time_ms=elapsed,
            tools_used=[],
        )

    async def _check_queue_pressure(self) -> str | None:
        """PRV: read queue depth from Redis. Reject if at hard cap, warn at soft.

        Returns rejection message if hard cap exceeded; otherwise None.
        Soft-cap warnings are emitted as SSE events by the streaming caller
        (we don't have a yield context here). In sync mode the soft cap is
        ignored — the queue is empty since extraction runs inline.
        """
        settings = self._c.settings
        if settings.extraction_mode != "async":
            return None
        cache = self._c.dedup_cache
        if cache is None or not hasattr(cache, "queue_depth"):
            return None
        try:
            depth = await cache.queue_depth(settings.taskiq_queue_name)
        except Exception:
            return None
        if depth >= settings.extraction_queue_depth_reject:
            logger.warning("Queue depth %d exceeds reject cap; rejecting upload", depth)
            return (
                f"Sistem lagi sibuk (antrian {depth} task). "
                "Coba lagi sebentar ya."
            )
        return None

    async def _run_extraction_stream(
        self,
        attachments: list[FileAttachment],
        session_id: int,
        user_id: int,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run extraction for each attachment, yielding SSE events as pages
        complete. Final yield carries `__final__: True` and `payload`: the
        list of extraction_data dicts the caller injects into llm_messages.
        """
        settings = self._c.settings
        mode = settings.extraction_mode

        if mode == "async":
            async for event in self._run_extraction_async(
                attachments, session_id, user_id
            ):
                yield event
            return

        # Sync mode: each attachment finishes inline, emit one extraction event each.
        results: list[dict[str, Any]] = []
        for att in attachments:
            yield {
                "type": "extraction",
                "data": {"status": "processing", "file_name": att.filename},
            }
            result = await self._extraction_agent.process(att, session_id, user_id)
            payload = {
                "file_id": result.file_id,
                "file_name": result.file_name,
                "pages": result.pages,
                "status": result.status,
                "summary": result.summary,
            }
            results.append(payload)
            yield {"type": "extraction", "data": payload}
        yield {"__final__": True, "payload": results}

    async def _run_extraction_async(
        self,
        attachments: list[FileAttachment],
        session_id: int,
        user_id: int,
    ) -> AsyncIterator[dict[str, Any]]:
        """Async path: enqueue per-page tasks, subscribe to pubsub, build the
        final extraction_results list from DB once all pages report.
        """
        from app.exceptions import IngestRejectedError
        from app.services.extraction.queue.progress import stream_progress

        settings = self._c.settings
        cache = self._c.dedup_cache
        ingest = self._c.ingest_service

        enqueued: list[Any] = []  # EnqueuedFile
        for att in attachments:
            yield {
                "type": "extraction",
                "data": {"status": "queueing", "file_name": att.filename},
            }
            try:
                ef = await ingest.enqueue(
                    att, session_id=session_id, user_id=user_id
                )
            except IngestRejectedError as e:
                yield {
                    "type": "extraction",
                    "data": {
                        "status": "rejected",
                        "file_name": att.filename,
                        "reason": e.reason,
                        "message": str(e),
                    },
                }
                continue
            enqueued.append(ef)
            yield {
                "type": "extraction",
                "data": {
                    "status": "queued",
                    "file_id": ef.file_id,
                    "file_name": ef.file_name,
                    "pages_total": len(ef.pages),
                    "queued": ef.queued,
                    "cached_hits": ef.cached_hits,
                },
            }

        if not enqueued:
            yield {"__final__": True, "payload": []}
            return

        # Wait for queued pages via pubsub. Cache hits are already in the DB
        # by now — we only subscribe for files that have queued pages > 0.
        file_pages = {ef.file_id: ef.queued for ef in enqueued if ef.queued > 0}
        timeout = settings.extraction_page_timeout_seconds * max(
            (max(file_pages.values()) if file_pages else 1), 1
        )

        if file_pages and cache is not None and hasattr(cache, "client"):
            async for event in stream_progress(
                cache.client,  # type: ignore[attr-defined]
                file_pages=file_pages,
                timeout_seconds=float(timeout),
            ):
                yield {
                    "type": "extraction",
                    "data": {
                        "status": "page_done",
                        "file_id": event.file_id,
                        "page": event.page,
                        "page_status": event.status,
                        "cache_layer": event.cache_layer,
                        "error": event.error,
                    },
                }

        # Build final extraction_results from DB so supervisor sees the same
        # shape sync mode produces.
        results: list[dict[str, Any]] = []
        for ef in enqueued:
            pages_rows = await self._c.db_client.fetchall(
                "SELECT page, agent_extracted, status FROM pages "
                "WHERE metadata_file_id = ? ORDER BY page",
                (ef.file_id,),
            )
            file_row = await self._c.db_client.fetchone(
                "SELECT status, status_message FROM metadata_file WHERE id = ?",
                (ef.file_id,),
            )
            import json as _json
            pages_payload = []
            for r in pages_rows:
                ext = {}
                if r["agent_extracted"]:
                    try:
                        ext = _json.loads(r["agent_extracted"])
                    except _json.JSONDecodeError:
                        pass
                pages_payload.append({
                    "page": r["page"],
                    "extraction": ext,
                    "status": r["status"],
                })
            payload = {
                "file_id": ef.file_id,
                "file_name": ef.file_name,
                "pages": pages_payload,
                "status": file_row["status"] if file_row else "completed",
                "summary": f"File {ef.file_name}: {len(pages_payload)} page(s)",
            }
            results.append(payload)
            yield {"type": "extraction", "data": payload}

        # Final aggregate status update on metadata_file (workers don't track
        # the per-file roll-up).
        for ef, payload in zip(enqueued, results):
            page_statuses = [p["status"] for p in payload["pages"]]
            ok = sum(1 for s in page_statuses if s == "extracted")
            total = len(page_statuses)
            if total == 0:
                final_status = "failed"
                msg = "no pages persisted"
            elif ok == total:
                final_status = "completed"
                msg = f"All {total} page(s) extracted"
            elif ok == 0:
                final_status = "failed"
                msg = "All pages failed"
            else:
                final_status = "partial"
                msg = f"{ok}/{total} page(s) extracted"
            await self._c.db_client.execute(
                "UPDATE metadata_file SET status = ?, status_message = ? WHERE id = ?",
                (final_status, msg, ef.file_id),
            )
            payload["status"] = final_status

        yield {"__final__": True, "payload": results}