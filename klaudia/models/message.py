from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    """Response from any agent in the system."""

    content: str
    tools_called: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
