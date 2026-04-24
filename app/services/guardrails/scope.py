import logging

from app.services.core.llm_client import LLMClient
from app.services.guardrails.config import GuardrailsConfig
from app.services.guardrails.prompts import SCOPE_CHECK_PROMPT

logger = logging.getLogger(__name__)


async def check_scope(
    text: str, llm_client: LLMClient, config: GuardrailsConfig
) -> bool:
    """Check if message contains blacklisted topics via Gemini.

    Returns True if blacklisted topic is detected.
    """
    topics_str = ", ".join(config.blacklisted_topics)
    prompt = SCOPE_CHECK_PROMPT.format(topics=topics_str, message=text)

    try:
        result = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=config.guardrails_model,
            temperature=0.0,
            max_tokens=10,
            span_name="guardrail.scope_check",
        )
        is_blocked = result.strip().upper().startswith("YES")
        if is_blocked:
            logger.warning(f"Blacklisted topic detected: {text[:80]}...")
        return is_blocked
    except Exception as e:
        logger.error(f"Scope check failed: {e}")
        return False
