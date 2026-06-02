"""Qwen3.5-4B text-recognition client (vLLM).

Used only when OCR_MODE=true: the upstream model is the base Qwen3.5-4B
(Qwen/Qwen3.5-4B) running on Lightning AI. It produces raw text that is
then fed to the KIE model (Gemini) for structured extraction.

This is intentionally minimal — no JSON parsing, no schema validation. Its
sole job is image → plain text. The "Text Recognition:" prompt matches
the official Qwen3.5-4B usage example.
"""

from __future__ import annotations

import base64
import logging

import httpx

from app.exceptions import OCRError
from app.services.core.observability import LangfuseService
from config.settings import Settings

logger = logging.getLogger(__name__)

_TEXT_RECOGNITION_PROMPT = "Text Recognition:"


class TextOCRClient:
    def __init__(
        self,
        settings: Settings,
        langfuse: LangfuseService | None = None,
    ) -> None:
        self._base_url = settings.vllm_base_url
        self._auth_token = settings.auth_token
        self._model = settings.vllm_ocr_model
        self._client = httpx.AsyncClient(timeout=120.0)
        self._langfuse = langfuse

    @property
    def model_id(self) -> str:
        return self._model

    async def recognize_text(self, jpg_bytes: bytes) -> str:
        if not self._base_url:
            raise OCRError(
                "VLLM_BASE_URL is not configured; cannot run TextOCRClient. "
                "Either set OCR_MODE=false or fill VLLM_BASE_URL."
            )

        image_b64 = base64.b64encode(jpg_bytes).decode("utf-8")
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            },
                        },
                        {"type": "text", "text": _TEXT_RECOGNITION_PROMPT},
                    ],
                }
            ],
            # Receipts top out well under 2048; capping avoids runaway hallucination
            "max_tokens": 2048,
            "temperature": 0.0,
        }
        headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
        }

        span_cm = (
            self._langfuse.span(
                "qwen-3.5-4b.text_recognition",
                as_type="generation",
                metadata={
                    "model": self._model,
                    "image_bytes": len(jpg_bytes),
                },
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            try:
                resp = await self._client.post(
                    self._base_url, json=payload, headers=headers
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"] or ""
                if obs is not None:
                    try:
                        obs.update(output=text, model=self._model)
                    except Exception:
                        pass
                return text
            except Exception as e:
                logger.error("Qwen3.5-4B text recognition failed: %s", e)
                if obs is not None:
                    try:
                        obs.update(level="ERROR", status_message=str(e))
                    except Exception:
                        pass
                raise OCRError(f"Qwen3.5-4B text recognition failed: {e}") from e

    async def shutdown(self) -> None:
        await self._client.aclose()


from contextlib import contextmanager


@contextmanager
def _nullspan():
    yield None
