from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from app.models.attachment import FileAttachment, MetadataFile


class KlaudiaMessage(BaseModel):
    role: str  # user | assistant | system
    content: str
    attachments: Optional[list[FileAttachment]] = None


class KlaudiaRequest(BaseModel):
    messages: list[KlaudiaMessage]
    session_id: Optional[int] = None  # None = create new session
    user_id: int = 1  # hardcoded for dev
    user_name: str = "User"


class ChatMetadata(BaseModel):
    """Per-turn metadata for personalization."""

    user_name: str = "User"
    date: str = Field(
        default_factory=lambda: datetime.now(
            tz=timezone(timedelta(hours=8))
        ).strftime("%A, %d %B %Y")
    )
    time: str = Field(
        default_factory=lambda: datetime.now(
            tz=timezone(timedelta(hours=8))
        ).strftime("%H:%M")
    )
    timezone: str = "GMT+8"


class ChatVariable(BaseModel):
    """Session file context injected into system prompt."""

    files: list[MetadataFile] = Field(default_factory=list)

    def format_context(self) -> str:
        if not self.files:
            return "No files in this session."
        lines: list[str] = []
        for i, f in enumerate(self.files, 1):
            lines.append(
                f"{i}. {f.file_name}\n"
                f"   - Type: {f.file_type}\n"
                f"   - Status: {f.status}\n"
                f"   - Pages: {f.total_pages}\n"
                f"   - File ID: {f.id}"
            )
        return "\n".join(lines)


class KlaudiaResponse(BaseModel):
    message: KlaudiaMessage
    session_id: int
    processing_time_ms: int
    tools_used: list[str] = Field(default_factory=list)
    metadata: ChatMetadata = Field(default_factory=ChatMetadata)
