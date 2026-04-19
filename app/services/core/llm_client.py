import logging
from typing import Any

from google import genai
from google.genai import types

from app.exceptions import LLMError
from config.settings import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Async client for Google Gemini via the google-genai SDK."""

    def __init__(self, settings: Settings) -> None:
        self._client = genai.Client(api_key=settings.llm_api_key)
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature

    # Thinking models (gemini-3-*) use output tokens for internal reasoning.
    # A low max_output_tokens budget gets exhausted by thinking, returning empty.
    MIN_OUTPUT_TOKENS = 256

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat request and return the assistant message content."""
        target_model = model or self._model
        temp = temperature if temperature is not None else self._temperature
        effective_tokens = max(max_tokens, self.MIN_OUTPUT_TOKENS)

        contents = _to_genai_contents(messages)

        try:
            response = await self._client.aio.models.generate_content(
                model=target_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    temperature=temp,
                    max_output_tokens=effective_tokens,
                ),
            )
            return response.text or ""
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMError(str(e)) from e

    async def shutdown(self) -> None:
        pass


def _to_genai_contents(
    messages: list[dict[str, Any]],
) -> list[types.Content]:
    """Convert OpenAI-style messages to google-genai Content objects."""
    contents: list[types.Content] = []
    system_parts: list[str] = []

    for msg in messages:
        role = msg["role"]
        text = msg.get("content", "")

        if role == "system":
            system_parts.append(text)
            continue

        genai_role = "model" if role == "assistant" else "user"

        if system_parts:
            text = "\n".join(system_parts) + "\n\n" + text
            system_parts.clear()

        contents.append(
            types.Content(
                role=genai_role,
                parts=[types.Part(text=text)],
            )
        )

    if system_parts and not contents:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text="\n".join(system_parts))],
            )
        )

    return contents
