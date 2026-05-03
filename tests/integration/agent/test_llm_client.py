"""Integration tests for LLM client - real Gemini API calls via google-genai SDK."""

import pytest

from app.services.core.llm_client import LLMClient
from config.settings import get_settings


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def llm(settings):
    return LLMClient(settings)


def _have_llm_creds() -> bool:
    s = get_settings()
    return bool(s.google_cloud_project) if s.google_genai_use_vertexai else bool(s.llm_api_key)


pytestmark = pytest.mark.skipif(
    not _have_llm_creds(),
    reason="No Gemini credentials (set LLM_API_KEY or GOOGLE_GENAI_USE_VERTEXAI=True + GOOGLE_CLOUD_PROJECT)",
)


@pytest.mark.asyncio
async def test_gemini_chat_completion(llm):
    """Basic Gemini API call should return a response."""
    result = await llm.chat(
        messages=[{"role": "user", "content": "Say hello in one word."}],
        max_tokens=50,
    )
    assert len(result) > 0
    print(f"\nGemini response: {result}")
    await llm.shutdown()


@pytest.mark.asyncio
async def test_gemini_structured_response(llm):
    """Gemini should handle structured prompts."""
    result = await llm.chat(
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Respond in JSON."},
            {"role": "user", "content": 'Return {"status": "ok"} as JSON.'},
        ],
        temperature=0.0,
        max_tokens=50,
    )
    assert "ok" in result.lower() or "status" in result.lower()
    print(f"\nStructured response: {result}")
    await llm.shutdown()
