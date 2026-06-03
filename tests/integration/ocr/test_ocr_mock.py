"""KIE client mock-mode smoke test.

Mock is content-keyed: KIEClient hashes the canonical JPG bytes and looks
up the matching label JSON from sample-data/labels/. Tests use real
fixture bytes so they exercise the same code path production hits.
"""

from pathlib import Path

import pytest

from app.services.extraction.infra.kie_client import KIEClient
from app.services.extraction.infra.normalizer import to_canonical_jpg
from config.settings import Settings


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_SAMPLE_IMAGE = _PROJECT_ROOT / "sample-data" / "receipt" / "1000-receipt.jpg"


@pytest.fixture
def settings_mock():
    return Settings(MOCK_KIE=True)


@pytest.mark.asyncio
async def test_mock_image_returns_full_schema(settings_mock):
    client = KIEClient(settings_mock)
    try:
        pages = await client.process_file(_SAMPLE_IMAGE.read_bytes(), "image/jpeg")
        assert len(pages) == 1
        ext = pages[0]
        assert set(ext.keys()) >= {"info", "items", "payment"}
        assert ext["info"]["store_name"] == "GREEN FIELD"
    finally:
        await client.shutdown()


@pytest.mark.asyncio
async def test_mock_returns_deep_copy(settings_mock):
    """Mutating returned dict must not affect subsequent calls."""
    client = KIEClient(settings_mock)
    try:
        jpg = to_canonical_jpg(_SAMPLE_IMAGE.read_bytes())
        first = await client.extract_from_image(jpg)
        first["info"]["store_name"] = "MUTATED"
        second = await client.extract_from_image(jpg)
        assert second["info"]["store_name"] == "GREEN FIELD"
    finally:
        await client.shutdown()


@pytest.mark.asyncio
async def test_mock_unknown_content_falls_back(settings_mock):
    """Bytes with no matching fixture should still return a valid schema shell."""
    client = KIEClient(settings_mock)
    try:
        from PIL import Image
        import io

        buf = io.BytesIO()
        Image.new("RGB", (1, 1), "white").save(buf, format="JPEG")
        jpg = buf.getvalue()
        result = await client.extract_from_image(jpg)
        assert result["info"]["store_name"] == "MOCK_FALLBACK"
        assert isinstance(result["items"], list)
        assert isinstance(result["payment"], dict)
    finally:
        await client.shutdown()


@pytest.mark.asyncio
async def test_legacy_usemockocr_alias_still_honored():
    """Settings should still respect USE_MOCK_OCR=true for one cycle."""
    s = Settings(USE_MOCK_OCR=True, MOCK_KIE=False)
    assert s.mock_kie is True
