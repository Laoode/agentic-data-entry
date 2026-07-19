import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.helpers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


class SessionItem(BaseModel):
    session_id: int
    session_name: Optional[str] = None
    created_at: str
    updated_at: str


class MessageItem(BaseModel):
    sender: str
    message_text: str
    file_id: Optional[int] = None
    timestamp: str


@router.get("/sessions")
async def list_sessions(req: Request, user_id: int = Depends(get_current_user)):
    db = req.app.state.container.db_client
    sessions = await db.get_sessions(user_id)
    return {"sessions": sessions}


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: int,
    req: Request,
    user_id: int = Depends(get_current_user),
):
    db = req.app.state.container.db_client
    owner = await db.get_session_owner(session_id)
    # 404 for both missing and foreign sessions: don't reveal which ids exist.
    if owner is None or owner != user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = await db.get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}
