"""GLM-OCR client: direct image/PDF -> structured JSON extraction.

GLM-OCR outputs JSON matching EXTRACTION_SCHEMA in one pass — no separate
OCR text + LLM extraction step. While the model is still fine-tuning a mock
payload is returned (toggle via USE_MOCK_OCR env flag).
"""

from __future__ import annotations

import base64
import copy
import io
import json
import logging
from typing import Any

import httpx
import pypdfium2 as pdfium

from app.exceptions import OCRError
from app.services.core.observability import LangfuseService
from app.services.extraction.agents.config import EXTRACTION_SCHEMA
from config.settings import Settings

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = (
    "请按下列JSON格式输出图中信息:\n"
    + json.dumps(EXTRACTION_SCHEMA, ensure_ascii=False, indent=2)
)

MOCK_EXTRACTION_JSON: dict[str, Any] = {
    "info": {
        "store_name": "INDOMARET",
        "store_location": "Jl. Poros Raha No.123",
        "store_contacts": [{"type": "phone", "value": "0401-123456"}],
        "tax_id": "01.234.567.8-901.000",
        "receipt_id": "INV-2025-0001",
        "payment_date": "2025-01-30",
        "payment_time": "14:30:00",
        "time_unit": "WITA",
    },
    "items": [
        {
            "item_name": "Indomie Goreng",
            "quantity": "2",
            "unit_price": "3500",
            "discount_label": "",
            "discount_price": "0",
            "tax_label": "PPN",
            "total_price": "7000",
        },
        {
            "item_name": "Teh Botol Sosro",
            "quantity": "1",
            "unit_price": "4000",
            "discount_label": "",
            "discount_price": "0",
            "tax_label": "PPN",
            "total_price": "4000",
        },
        {
            "item_name": "Aqua 600ml",
            "quantity": "1",
            "unit_price": "3000",
            "discount_label": "",
            "discount_price": "0",
            "tax_label": "PPN",
            "total_price": "3000",
        },
    ],
    "returned_items": [],
    "payment": {
        "total_items": "4",
        "currency": "IDR",
        "subtotal_price": "14000",
        "discounts": [],
        "taxes": [{"tax_name": "PPN 11%", "amount": "1540"}],
        "additional_charges": [],
        "grand_total": "15540",
        "rounding": "0",
        "payment_method": "QRIS",
        "tendered": "15540",
        "change": "0",
    },
}


class OCRClient:
    """Wraps the GLM-OCR vLLM endpoint; returns extraction JSON directly."""

    def __init__(
        self, settings: Settings, langfuse: LangfuseService | None = None
    ) -> None:
        self._base_url = settings.vllm_base_url
        self._auth_token = settings.auth_token
        self._model = settings.vllm_ocr_model
        self._use_mock = settings.use_mock_ocr
        self._client = httpx.AsyncClient(timeout=120.0)
        self._langfuse = langfuse

    async def extract_json_from_image(self, image_bytes: bytes) -> dict[str, Any]:
        """Return extracted JSON for a single image."""
        span_cm = (
            self._langfuse.span(
                "glm-ocr.extract_image",
                as_type="generation",
                metadata={
                    "model": self._model,
                    "mock": self._use_mock,
                    "image_bytes": len(image_bytes),
                },
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            if self._use_mock:
                logger.info("USE_MOCK_OCR=true → returning mock extraction JSON")
                result = copy.deepcopy(MOCK_EXTRACTION_JSON)
                if obs is not None:
                    try:
                        obs.update(output=result, model=f"{self._model}-mock")
                    except Exception:
                        pass
                return result

            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            payload = {
                "model": self._model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_b64}"
                                },
                            },
                            {"type": "text", "text": _EXTRACTION_PROMPT},
                        ],
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.2,
                "top_p": 0.9,
            }
            headers = {
                "Authorization": f"Bearer {self._auth_token}",
                "Content-Type": "application/json",
            }
            try:
                resp = await self._client.post(
                    self._base_url, json=payload, headers=headers
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = _parse_json_content(content)
                if obs is not None:
                    try:
                        obs.update(output=parsed, model=self._model)
                    except Exception:
                        pass
                return parsed
            except Exception as e:
                logger.error(f"GLM-OCR request failed: {e}")
                if obs is not None:
                    try:
                        obs.update(level="ERROR", status_message=str(e))
                    except Exception:
                        pass
                raise OCRError(f"GLM-OCR failed: {e}") from e

    async def extract_json_from_pdf(self, pdf_bytes: bytes) -> list[dict[str, Any]]:
        """Return one extraction JSON per PDF page."""
        try:
            pdf = pdfium.PdfDocument(pdf_bytes)
        except Exception as e:
            raise OCRError(f"Failed to open PDF: {e}") from e

        results: list[dict[str, Any]] = []
        for i in range(len(pdf)):
            page = pdf[i]
            pil_image = page.render(scale=200 / 72).to_pil()
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            results.append(await self.extract_json_from_image(buf.getvalue()))
        return results

    async def process_file(
        self, data: bytes, content_type: str
    ) -> list[dict[str, Any]]:
        """Dispatch to PDF or image handler. Always returns a list (one per page)."""
        if content_type == "application/pdf":
            return await self.extract_json_from_pdf(data)
        return [await self.extract_json_from_image(data)]

    async def shutdown(self) -> None:
        await self._client.aclose()


from contextlib import contextmanager


@contextmanager
def _nullspan():
    yield None


def _parse_json_content(content: str) -> dict[str, Any]:
    """Strip markdown code fences if present, then json.loads."""
    text = content.strip()
    if text.startswith("```json"):
        text = text.split("```json", 1)[1]
        text = text.rsplit("```", 1)[0]
    elif text.startswith("```"):
        text = text.split("```", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())
