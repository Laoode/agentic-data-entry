"""Integration tests for LLM client - real Gemini API calls."""

import pytest

from app.services.core.llm_client import LLMClient
from config.settings import get_settings


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def llm(settings):
    return LLMClient(settings)


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
