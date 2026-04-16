"""OCR client mock-mode smoke test (GLM-OCR direct JSON extraction)."""

import pytest

from app.services.extraction.infra.ocr_client import OCRClient
from config.settings import Settings


@pytest.fixture
def settings_mock():
    return Settings(USE_MOCK_OCR=True)


@pytest.mark.asyncio
async def test_mock_image_returns_full_schema(settings_mock):
    client = OCRClient(settings_mock)
    try:
        pages = await client.process_file(b"fake image", "image/jpeg")
        assert len(pages) == 1
        ext = pages[0]
        assert set(ext.keys()) >= {"info", "items", "returned_items", "payment"}
        assert ext["info"]["store_name"] == "INDOMARET"
        assert ext["payment"]["grand_total"] == "15540"
    finally:
        await client.shutdown()


@pytest.mark.asyncio
async def test_mock_returns_deep_copy(settings_mock):
    """Mutating returned dict must not affect subsequent calls."""
    client = OCRClient(settings_mock)
    try:
        first = await client.extract_json_from_image(b"x")
        first["info"]["store_name"] = "MUTATED"
        second = await client.extract_json_from_image(b"x")
        assert second["info"]["store_name"] == "INDOMARET"
    finally:
        await client.shutdown()
