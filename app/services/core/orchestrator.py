import logging
import re
import time
from typing import Any

from app.models.chat import (
    ChatMetadata,
    KlaudiaMessage,
    KlaudiaResponse,
)
from app.services.core.container import KlaudiaContainer
from app.services.core.prompts import KLAUDIA_SYSTEM_PROMPT
from klaudia.core.supervisor.tools.context import build_extraction_context, build_session_context

logger = logging.getLogger(__name__)


class KlaudiaOrchestrator:
    """Main conversation orchestrator.

    Pipeline: context -> guardrails -> route (extraction/supervisor) -> response
    """

    def __init__(self, container: KlaudiaContainer) -> None:
        self._c = container
        self._extraction_agent = container.extraction_agent

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

        # 2. Get last user message text
        user_msg = messages[-1]
        user_text = user_msg.content

        # 3. Guardrails (input)
        guard_result = await self._c.guardrails.validate_input(user_text)
        if not guard_result.passed:
            return self._rejection_response(session_id, guard_result.rejection_message, start)

        # 4. Save user message
        await self._c.db_client.save_message(session_id, user_id, "user", user_text)

        # 5. Check for attachments
        extraction_data = None
        has_attachment = user_msg.attachments and len(user_msg.attachments) > 0
        if has_attachment:
            for att in user_msg.attachments:
                result = await self._extraction_agent.process(att, session_id, user_id)
                extraction_data = {
                    "file_id": result.file_id,
                    "file_name": result.file_name,
                    "pages": result.pages,
                    "status": result.status,
                    "summary": result.summary,
                }

        # 6. Build context
        history = await self._c.db_client.get_conversation_history(session_id, limit=10)
        session_files_raw = await self._c.db_client.get_session_files(session_id)

        meta = ChatMetadata(user_name=user_name)
        session_files_ctx = build_session_context(session_files_raw)
        system_prompt = KLAUDIA_SYSTEM_PROMPT.format(
            session_files=session_files_ctx,
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

        # Add extraction context if present
        if extraction_data:
            extraction_ctx = build_extraction_context(extraction_data)
            llm_messages.append({"role": "user", "content": extraction_ctx})

        # Add current user message
        llm_messages.append({"role": "user", "content": user_text})

        # 7. Invoke supervisor
        agent_response = await self._c.supervisor.process_conversation(
            messages=llm_messages,
            extraction_data=extraction_data,
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
