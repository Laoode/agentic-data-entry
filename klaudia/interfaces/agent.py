from typing import Any, Protocol

from klaudia.models.message import AgentResponse


class BaseAgent(Protocol):
    """Protocol for all agents in the system."""

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AgentResponse: ...
