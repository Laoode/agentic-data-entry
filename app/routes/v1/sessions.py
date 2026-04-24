from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
import logging

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
async def list_sessions(req: Request, user_id: int = 1):
    db = req.app.state.container.db_client
    sessions = await db.get_sessions(user_id)
    return {"sessions": sessions}

@router.get("/sessions/{session_id}")
async def get_session(session_id: int, req: Request):
    db = req.app.state.container.db_client
    messages = await db.get_session_messages(session_id)
    return {"session_id": session_id, "messages": messages}