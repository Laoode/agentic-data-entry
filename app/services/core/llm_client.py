import logging
from typing import Any

import httpx

from app.exceptions import LLMError
from config.settings import Settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Async OpenAI-compatible client for Gemini via Google's OpenAI endpoint."""

    def __init__(self, settings: Settings) -> None:
        self._endpoint = settings.llm_endpoint.rstrip("/")
        self._api_key = settings.llm_api_key
        self._model = settings.llm_model
        self._temperature = settings.llm_temperature
        self._client = httpx.AsyncClient(timeout=120.0)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Send a chat completion request and return the assistant message content."""
        payload = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self._temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = await self._client.post(
                f"{self._endpoint}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"].get("content") or ""
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code} - {e.response.text}")
            raise LLMError(f"LLM request failed: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise LLMError(str(e)) from e

    async def shutdown(self) -> None:
        await self._client.aclose()
