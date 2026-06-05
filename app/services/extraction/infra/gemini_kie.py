"""Gemini-3-flash KIE client.

Two entrypoints share the same prompt:
    extract_from_image(jpg_bytes) — multimodal, Gemini sees the receipt image
    extract_from_text(ocr_text)   — text-only, used after Qwen3.5-4B text recog

Both return a raw dict (caller runs validate_and_merge for schema hygiene).
google-genai's `response_mime_type='application/json'` forces JSON output;
malformed cases still go through the project's 3-layer parser.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.exceptions import LLMError
from app.services.core.observability import LangfuseService
from app.services.extraction.agents.config import EXTRACTION_SCHEMA
from app.services.extraction.agents.parser import parse_extraction_json
from app.services.extraction.agents.prompt import (
    EXTRACTION_RULES,
    FEW_SHOT_OUTPUT,
    FEW_SHOT_RECEIPT_TEXT,
)
from config.settings import Settings

logger = logging.getLogger(__name__)


def _build_system_prompt() -> str:
    schema_json = json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)
    few_shot_json = json.dumps(FEW_SHOT_OUTPUT, ensure_ascii=False, indent=2)
    return (
        "You are a receipt Key-Information-Extraction (KIE) assistant.\n"
        "Output ONLY a JSON object that strictly matches the schema below.\n\n"
        f"{EXTRACTION_RULES}\n\n"
        "## JSON SCHEMA (shape) — your output MUST match these keys exactly:\n"
        f"```json\n{schema_json}\n```\n\n"
        "## FEW-SHOT EXAMPLE\n"
        "Receipt (text representation):\n"
        f"{FEW_SHOT_RECEIPT_TEXT}\n\n"
        "Expected JSON output:\n"
        f"```json\n{few_shot_json}\n```"
    )


class GeminiKIEClient:
    """Gemini wrapper that returns extraction JSON for receipt input.

    Holds its own google-genai client because the LLMClient used by Klaudia
    agents (router, supervisor) is tuned for chat completion and we want a
    separate temperature/config profile for extraction.
    """

    def __init__(
        self,
        settings: Settings,
        langfuse: LangfuseService | None = None,
    ) -> None:
        self._model = settings.kie_model
        self._langfuse = langfuse
        if settings.google_genai_use_vertexai:
            if not settings.google_cloud_project:
                raise ValueError(
                    "GOOGLE_GENAI_USE_VERTEXAI=True but GOOGLE_CLOUD_PROJECT is empty"
                )
            self._client = genai.Client(
                vertexai=True,
                project=settings.google_cloud_project,
                location=settings.google_cloud_location or "global",
            )
            logger.info("GeminiKIEClient: Vertex AI mode model=%s", self._model)
        else:
            if not settings.llm_api_key:
                raise ValueError(
                    "LLM_API_KEY required when GOOGLE_GENAI_USE_VERTEXAI=False"
                )
            self._client = genai.Client(api_key=settings.llm_api_key)
            logger.info("GeminiKIEClient: Developer API mode model=%s", self._model)

        self._system_prompt = _build_system_prompt()

    @property
    def model_id(self) -> str:
        return self._model

    async def extract_from_image(self, jpg_bytes: bytes) -> dict[str, Any]:
        """Multimodal call: Gemini reads the receipt image directly."""
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=jpg_bytes, mime_type="image/jpeg"),
                    types.Part(
                        text="Extract this receipt into the JSON schema. "
                        "Follow every rule above. Output only the JSON object."
                    ),
                ],
            )
        ]
        return await self._generate(contents, span_name="gemini.kie.image")

    async def extract_from_text(self, ocr_text: str) -> dict[str, Any]:
        """Text-only call — for the OCR_MODE=true path, where Qwen3.5-4B provides
        plain text and Gemini does the KIE step."""
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=(
                            "Extract the following receipt text into the JSON "
                            "schema. Follow every rule above. Output only JSON.\n\n"
                            "## RECEIPT TEXT\n"
                            f"{ocr_text}"
                        )
                    ),
                ],
            )
        ]
        return await self._generate(contents, span_name="gemini.kie.text")

    async def _generate(
        self,
        contents: list[types.Content],
        *,
        span_name: str,
    ) -> dict[str, Any]:
        config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            response_mime_type="application/json",
            # KIE is pure extraction, not reasoning — disable thinking so the
            # full output budget goes to the JSON response, not internal thought.
            # gemini-3-flash-preview is a thinking model; without this the model
            # can exhaust max_output_tokens on thinking tokens and emit nothing.
            # (mirrors D15: thinking_budget=0 on all non-reasoning paths)
            thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL),
            temperature=0.1,
            top_p=0.95,
            max_output_tokens=4096,
        )

        span_cm = (
            self._langfuse.span(
                span_name,
                as_type="generation",
                metadata={"model": self._model},
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            try:
                response = await self._client.aio.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=config,
                )
            except Exception as e:
                logger.error("Gemini KIE call failed: %s", e)
                if obs is not None:
                    try:
                        obs.update(level="ERROR", status_message=str(e))
                    except Exception:
                        pass
                raise LLMError(f"Gemini KIE failed: {e}") from e

            raw = response.text or ""
            if not raw and response.candidates:
                # Fallback: aggregate non-thought text parts directly.
                # On thinking models response.text can be None when the SDK
                # doesn't find a plain text part in the first candidate.
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    parts_text = [
                        p.text
                        for p in candidate.content.parts
                        if p.text and not getattr(p, "thought", False)
                    ]
                    raw = "".join(parts_text)
                    if raw:
                        logger.debug(
                            "Gemini KIE: response.text was empty, "
                            "recovered from %d part(s)",
                            len(parts_text),
                        )

            if not raw:
                finish_reason = (
                    response.candidates[0].finish_reason
                    if response.candidates
                    else "NO_CANDIDATES"
                )
                parts_count = (
                    len(response.candidates[0].content.parts)
                    if response.candidates
                    and response.candidates[0].content
                    and response.candidates[0].content.parts
                    else 0
                )
                logger.error(
                    "Gemini KIE empty response "
                    "(model=%s finish_reason=%s candidates=%d parts=%d)",
                    self._model,
                    finish_reason,
                    len(response.candidates) if response.candidates else 0,
                    parts_count,
                )
                if obs is not None:
                    try:
                        obs.update(
                            level="ERROR",
                            status_message=(
                                f"empty response finish_reason={finish_reason}"
                            ),
                        )
                    except Exception:
                        pass
                raise LLMError(
                    f"Gemini KIE returned empty response "
                    f"(finish_reason={finish_reason})"
                )
            try:
                parsed = parse_extraction_json(raw)
            except Exception as e:
                logger.error("Gemini KIE JSON parse failed: %s", e)
                if obs is not None:
                    try:
                        obs.update(level="ERROR", status_message=str(e))
                    except Exception:
                        pass
                raise LLMError(f"Gemini KIE JSON unparseable: {e}") from e

            if obs is not None:
                try:
                    obs.update(output=parsed, model=self._model)
                except Exception:
                    pass
            return parsed


from contextlib import contextmanager


@contextmanager
def _nullspan():
    yield None
