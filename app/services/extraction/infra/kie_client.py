"""KIEClient — single seam IngestService + workers depend on.

Owns the mode-routing logic so callers don't have to know the difference
between mock / direct / separated KIE. Modes:

    mock      MOCK_KIE=true                        fixture lookup
    direct    MOCK_KIE=false + OCR_MODE=false      Gemini image -> JSON (one call)
    separated MOCK_KIE=false + OCR_MODE=true       GLM-OCR text -> Gemini KIE -> JSON

The content-keyed mock fixture map lives here (used to be in OCRClient) so
ingest tests can swap modes without changing the dep wiring.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from app.exceptions import OCRError
from app.services.core.observability import LangfuseService
from app.services.extraction.agents.config import EXTRACTION_SCHEMA
from app.services.extraction.infra.gemini_kie import GeminiKIEClient
from app.services.extraction.infra.hasher import hash_bytes
from app.services.extraction.infra.normalizer import to_canonical_jpg
from app.services.extraction.infra.pdf_splitter import iter_pages_as_jpg
from app.services.extraction.infra.text_ocr import TextOCRClient
from config.settings import Settings

logger = logging.getLogger(__name__)

# Returned when mock mode can't find a fixture for the input. Intentionally
# obvious so unit tests catch unexpected paths instead of silently passing.
_FALLBACK_MOCK: dict[str, Any] = copy.deepcopy(EXTRACTION_SCHEMA)
_FALLBACK_MOCK["info"]["store_name"] = "MOCK_FALLBACK"


class KIEClient:
    def __init__(
        self,
        settings: Settings,
        langfuse: LangfuseService | None = None,
    ) -> None:
        self._mock_kie = settings.mock_kie
        self._ocr_mode = settings.ocr_mode
        self._kie_model = settings.kie_model
        self._lora_name = settings.ocr_lora_name or settings.vllm_ocr_model
        self._schema_version = settings.ocr_schema_version

        # Lazy-build subclients so unit tests that only use mock mode don't
        # need GCP creds / vLLM URL.
        self._gemini: GeminiKIEClient | None = None
        self._text_ocr: TextOCRClient | None = None
        self._langfuse = langfuse
        self._settings = settings

        self._mock_lookup: dict[str, dict[str, Any]] = {}
        if self._mock_kie:
            self._mock_lookup = _build_mock_lookup()
            logger.info(
                "KIE mock mode: %d sample fixtures indexed by content hash",
                len(self._mock_lookup),
            )

    @property
    def mode(self) -> str:
        if self._mock_kie:
            return "mock"
        return "separated" if self._ocr_mode else "direct"

    @property
    def model_id(self) -> str:
        """Identifier of the model that produced the final JSON. Used for
        provenance in blob_extraction.ocr_model so we can re-run later when
        the model is upgraded."""
        if self._mock_kie:
            return f"{self._kie_model}-mock"
        if self._ocr_mode:
            return f"{self._settings.vllm_ocr_model}+{self._kie_model}"
        return self._kie_model

    @property
    def lora_name(self) -> str:
        return self._lora_name

    @property
    def schema_version(self) -> str:
        return self._schema_version

    async def extract_from_image(self, jpg_bytes: bytes) -> dict[str, Any]:
        if self._mock_kie:
            return self._mock_extract(jpg_bytes)
        if self._ocr_mode:
            return await self._separated_extract(jpg_bytes)
        return await self._direct_extract(jpg_bytes)

    def _mock_extract(self, jpg_bytes: bytes) -> dict[str, Any]:
        h = hash_bytes(jpg_bytes)
        result = self._mock_lookup.get(h)
        if result is None:
            logger.warning(
                "Mock KIE: no fixture for hash %s; returning fallback", h[:12]
            )
            return copy.deepcopy(_FALLBACK_MOCK)
        return copy.deepcopy(result)

    async def _direct_extract(self, jpg_bytes: bytes) -> dict[str, Any]:
        if self._gemini is None:
            self._gemini = GeminiKIEClient(self._settings, self._langfuse)
        return await self._gemini.extract_from_image(jpg_bytes)

    async def _separated_extract(self, jpg_bytes: bytes) -> dict[str, Any]:
        if self._text_ocr is None:
            self._text_ocr = TextOCRClient(self._settings, self._langfuse)
        if self._gemini is None:
            self._gemini = GeminiKIEClient(self._settings, self._langfuse)

        text = await self._text_ocr.recognize_text(jpg_bytes)
        if not text.strip():
            raise OCRError("GLM-OCR returned empty text for separated KIE path")
        return await self._gemini.extract_from_text(text)

    # Legacy compatibility shim — old OCRClient.process_file accepted raw
    # bytes + content type. Kept so the few remaining callers in tests don't
    # have to know about the JPG normalization step. Production paths go
    # through IngestService and bypass this entirely.
    async def process_file(
        self, data: bytes, content_type: str
    ) -> list[dict[str, Any]]:
        if content_type == "application/pdf":
            return [
                await self.extract_from_image(jpg)
                for _page, jpg in iter_pages_as_jpg(data)
            ]
        return [await self.extract_from_image(to_canonical_jpg(data))]

    async def shutdown(self) -> None:
        if self._text_ocr is not None:
            await self._text_ocr.shutdown()


# ─── Mock fixture loading ─────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _build_mock_lookup() -> dict[str, dict[str, Any]]:
    """Build hash -> label map from sample-data/.

    Same idea as the old ocr_client._build_mock_lookup: normalize each
    fixture image, hash the canonical JPG, point at its label JSON. PDF
    pages are rendered then normalized, so dedup logic exercises the same
    path production hits.
    """
    lookup: dict[str, dict[str, Any]] = {}

    images_dir = _PROJECT_ROOT / "sample-data" / "receipt"
    image_labels_dir = _PROJECT_ROOT / "sample-data" / "labels" / "images"
    if images_dir.is_dir() and image_labels_dir.is_dir():
        for img_path in sorted(images_dir.glob("*.jpg")):
            label_path = image_labels_dir / f"{img_path.stem}.json"
            if not label_path.is_file():
                continue
            try:
                jpg = to_canonical_jpg(img_path.read_bytes())
                label = json.loads(label_path.read_text(encoding="utf-8"))
                lookup[hash_bytes(jpg)] = label
            except Exception as e:  # pragma: no cover
                logger.warning("Mock fixture skipped %s: %s", img_path, e)

    pdf_dir = _PROJECT_ROOT / "sample-data" / "pdf"
    pdf_labels_dir = _PROJECT_ROOT / "sample-data" / "labels" / "pdf"
    if pdf_dir.is_dir() and pdf_labels_dir.is_dir():
        for pdf_path in sorted(pdf_dir.glob("*.pdf")):
            label_subdir = pdf_labels_dir / pdf_path.stem
            if not label_subdir.is_dir():
                continue
            try:
                pdf_bytes = pdf_path.read_bytes()
                for page_num, jpg in iter_pages_as_jpg(pdf_bytes):
                    label_file = label_subdir / f"{page_num}.json"
                    if not label_file.is_file():
                        continue
                    label = json.loads(label_file.read_text(encoding="utf-8"))
                    lookup[hash_bytes(jpg)] = label
            except Exception as e:  # pragma: no cover
                logger.warning("Mock PDF fixture skipped %s: %s", pdf_path, e)

    return lookup
