import logging

from app.services.core.llm_client import LLMClient
from app.services.guardrails.config import GuardrailsConfig
from app.services.guardrails.prompts import OUTPUT_CHECK_PROMPT

logger = logging.getLogger(__name__)


async def check_output(
    response_text: str, llm_client: LLMClient, config: GuardrailsConfig
) -> bool:
    """Check if assistant output contains blacklisted content.

    Returns True if blacklisted content is detected.
    """
    topics_str = ", ".join(config.blacklisted_topics)
    prompt = OUTPUT_CHECK_PROMPT.format(topics=topics_str, response=response_text)

    try:
        result = await llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            model=config.guardrails_model,
            temperature=0.0,
            max_tokens=10,
        )
        is_blocked = result.strip().upper().startswith("YES")
        if is_blocked:
            logger.warning("Output guardrail triggered")
        return is_blocked
    except Exception as e:
        logger.error(f"Output check failed: {e}")
        return False
