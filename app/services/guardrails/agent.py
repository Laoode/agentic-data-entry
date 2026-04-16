import asyncio
import logging
from dataclasses import dataclass

from app.services.core.llm_client import LLMClient
from app.services.guardrails.base import check_prompt_injection
from app.services.guardrails.config import GuardrailsConfig
from app.services.guardrails.output import check_output
from app.services.guardrails.prompts import REJECTION_MESSAGES
from app.services.guardrails.scope import check_scope

logger = logging.getLogger(__name__)


@dataclass
class GuardrailResult:
    passed: bool
    rejection_message: str | None = None


class GuardrailsAgent:
    """Runs input validation checks in parallel: prompt injection + scope."""

    def __init__(self, llm_client: LLMClient, config: GuardrailsConfig) -> None:
        self._llm_client = llm_client
        self._config = config

    async def validate_input(self, text: str) -> GuardrailResult:
        """Run prompt injection and scope checks in parallel.

        Raises GuardrailError if rejected.
        """
        # Run both checks concurrently
        injection_task = check_prompt_injection(text, self._config)
        scope_task = check_scope(text, self._llm_client, self._config)

        is_injection, is_blacklisted = await asyncio.gather(
            injection_task, scope_task
        )

        if is_injection:
            msg = REJECTION_MESSAGES["prompt_injection"]
            logger.warning(f"Input rejected: prompt injection")
            return GuardrailResult(passed=False, rejection_message=msg)

        if is_blacklisted:
            msg = REJECTION_MESSAGES["blacklisted_topic"]
            logger.warning(f"Input rejected: blacklisted topic")
            return GuardrailResult(passed=False, rejection_message=msg)

        return GuardrailResult(passed=True)

    async def validate_output(self, response_text: str) -> GuardrailResult:
        """Validate assistant output against blacklisted topics."""
        is_blocked = await check_output(response_text, self._llm_client, self._config)
        if is_blocked:
            msg = REJECTION_MESSAGES["blacklisted_topic"]
            return GuardrailResult(passed=False, rejection_message=msg)
        return GuardrailResult(passed=True)
