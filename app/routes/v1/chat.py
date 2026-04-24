import json
import logging
from typing import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.models.chat import KlaudiaRequest, KlaudiaResponse

logger = logging.getLogger(__name__)

router = APIRouter()

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


@router.post("/chat", response_model=KlaudiaResponse)
async def chat(request: KlaudiaRequest, req: Request) -> KlaudiaResponse:
    """Process a chat message through the Klaudia pipeline (non-streaming)."""
    orchestrator = req.app.state.orchestrator
    return await orchestrator.process(
        messages=request.messages,
        session_id=request.session_id,
        user_id=request.user_id,
        user_name=request.user_name,
    )


def _format_sse(event: dict) -> str:
    """Encode a dict event as an SSE frame."""
    name = event.get("type", "message")
    payload = json.dumps(event.get("data", {}), ensure_ascii=False)
    return f"event: {name}\ndata: {payload}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: KlaudiaRequest, req: Request) -> StreamingResponse:
    """Stream the Klaudia pipeline as Server-Sent Events."""
    orchestrator = req.app.state.orchestrator

    async def event_source() -> AsyncIterator[str]:
        try:
            async for event in orchestrator.stream(
                messages=request.messages,
                session_id=request.session_id,
                user_id=request.user_id,
                user_name=request.user_name,
            ):
                if await req.is_disconnected():
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
