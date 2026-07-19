import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from pydantic import BaseModel, Field

from app.models.attachment import FileAttachment, MetadataFile

_GMT8 = timezone(timedelta(hours=8))


def _now_gmt8() -> datetime:
    """Current time in GMT+8.

    If ``E2E_FREEZE_NOW`` is set (ISO-8601, e.g. ``2026-06-30T19:22:00``), that
    fixed instant is returned instead. Only the E2E harness sets it, so the
    system prompt's CURRENT DATE/TIME stays pinned to June across runs (keeping
    "today" consistent with the June-based docs/TABLE.md fixtures). Production
    never sets the var and always sees the real wall clock.
    """
    frozen = os.environ.get("E2E_FREEZE_NOW")
    if frozen:
        try:
            dt = datetime.fromisoformat(frozen)
            return (
                dt.replace(tzinfo=_GMT8) if dt.tzinfo is None else dt.astimezone(_GMT8)
            )
        except ValueError:
            pass
    return datetime.now(tz=_GMT8)


class KlaudiaMessage(BaseModel):
    role: str  # user | assistant | system
    content: str
    attachments: Optional[list[FileAttachment]] = None


class KlaudiaRequest(BaseModel):
    messages: list[KlaudiaMessage]
    session_id: Optional[int] = None  # None = create new session
    # Identity comes from the Bearer token (app.helpers.auth), never the body.
    user_name: str = "User"


class ChatMetadata(BaseModel):
    """Per-turn metadata for personalization."""

    user_name: str = "User"
    date: str = Field(default_factory=lambda: _now_gmt8().strftime("%A, %d %B %Y"))
    time: str = Field(default_factory=lambda: _now_gmt8().strftime("%H:%M"))
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
