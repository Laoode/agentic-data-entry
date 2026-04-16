import logging

from fastapi import APIRouter, Request

from app.models.chat import KlaudiaRequest, KlaudiaResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=KlaudiaResponse)
async def chat(request: KlaudiaRequest, req: Request) -> KlaudiaResponse:
    """Process a chat message through the Klaudia pipeline."""
    orchestrator = req.app.state.orchestrator
    return await orchestrator.process(
        messages=request.messages,
        session_id=request.session_id,
        user_id=request.user_id,
        user_name=request.user_name,
    )
