import asyncio
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

from app.services.core.llm_client import LLMClient
from app.services.core.observability import LangfuseService
from app.services.guardrails.base import check_prompt_injection
from app.services.guardrails.config import GuardrailsConfig
from app.services.guardrails.output import check_output
from app.services.guardrails.prompts import REJECTION_MESSAGES
from app.services.guardrails.scope import check_scope

logger = logging.getLogger(__name__)


@contextmanager
def _nullspan():
    yield None


@dataclass
class GuardrailResult:
    passed: bool
    rejection_message: str | None = None


class GuardrailsAgent:
    """Runs input validation checks in parallel: prompt injection + scope."""

    def __init__(
        self,
        llm_client: LLMClient,
        config: GuardrailsConfig,
        langfuse: Optional[LangfuseService] = None,
    ) -> None:
        self._llm_client = llm_client
        self._config = config
        self._langfuse = langfuse

    async def validate_input(self, text: str) -> GuardrailResult:
        """Run prompt injection and scope checks in parallel.

        Raises GuardrailError if rejected.
        """
        span_cm = (
            self._langfuse.span(
                "guardrail.validate_input",
                as_type="guardrail",
                input=text,
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            # Run both checks concurrently
            injection_task = check_prompt_injection(text, self._config, self._langfuse)
            scope_task = check_scope(text, self._llm_client, self._config)

            is_injection, is_blacklisted = await asyncio.gather(
                injection_task, scope_task
            )

            if is_injection:
                msg = REJECTION_MESSAGES["prompt_injection"]
                logger.warning("Input rejected: prompt injection")
                if obs is not None:
                    try:
                        obs.update(output={"passed": False, "reason": "prompt_injection"})
                    except Exception:
                        pass
                return GuardrailResult(passed=False, rejection_message=msg)

            if is_blacklisted:
                msg = REJECTION_MESSAGES["blacklisted_topic"]
                logger.warning("Input rejected: blacklisted topic")
                if obs is not None:
                    try:
                        obs.update(output={"passed": False, "reason": "blacklisted_topic"})
                    except Exception:
                        pass
                return GuardrailResult(passed=False, rejection_message=msg)

            if obs is not None:
                try:
                    obs.update(output={"passed": True})
                except Exception:
                    pass
            return GuardrailResult(passed=True)

    async def validate_output(self, response_text: str) -> GuardrailResult:
        """Validate assistant output against blacklisted topics."""
        span_cm = (
            self._langfuse.span(
                "guardrail.validate_output",
                as_type="guardrail",
                input=response_text,
            )
            if self._langfuse is not None
            else _nullspan()
        )

        with span_cm as obs:
            is_blocked = await check_output(response_text, self._llm_client, self._config)
            if is_blocked:
                msg = REJECTION_MESSAGES["blacklisted_topic"]
                if obs is not None:
                    try:
                        obs.update(output={"passed": False, "reason": "blacklisted_topic"})
                    except Exception:
                        pass
                return GuardrailResult(passed=False, rejection_message=msg)
            if obs is not None:
                try:
                    obs.update(output={"passed": True})
                except Exception:
                    pass
            return GuardrailResult(passed=True)
