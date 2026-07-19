import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import StreamingResponse

from app.helpers.auth import get_current_user
from app.helpers.ratelimit import chat_limit, limiter
from app.models.chat import KlaudiaRequest, KlaudiaResponse

logger = logging.getLogger(__name__)

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/chat", response_model=KlaudiaResponse)
@limiter.limit(chat_limit)
async def chat(
    body: KlaudiaRequest,
    request: Request,
    response: Response,
    user_id: int = Depends(get_current_user),
) -> KlaudiaResponse:
    """Process a chat message through the Klaudia pipeline (non-streaming)."""
    orchestrator = request.app.state.orchestrator
    return await orchestrator.process(
        messages=body.messages,
        session_id=body.session_id,
        user_id=user_id,
        user_name=body.user_name,
    )


def _format_sse(event: dict) -> str:
    """Encode a dict event as an SSE frame."""
    name = event.get("type", "message")
    payload = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {name}\ndata: {payload}\n\n"


@router.post("/chat/stream")
@limiter.limit(chat_limit)
async def chat_stream(
    body: KlaudiaRequest,
    request: Request,
    user_id: int = Depends(get_current_user),
) -> StreamingResponse:
    """Stream the Klaudia pipeline as Server-Sent Events."""
    orchestrator = request.app.state.orchestrator

    async def event_source() -> AsyncIterator[str]:
        try:
            async for event in orchestrator.stream(
                messages=body.messages,
                session_id=body.session_id,
                user_id=user_id,
                user_name=body.user_name,
            ):
                if await request.is_disconnected():
                    logger.info("Client disconnected; stopping stream")
                    return
                yield _format_sse(event)
        except Exception as exc:
            logger.exception("chat_stream failure")
            yield _format_sse({"type": "error", "data": {"message": str(exc)}})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
