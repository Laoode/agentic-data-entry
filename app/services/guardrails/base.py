import logging

from groq import AsyncGroq

from app.services.guardrails.config import GuardrailsConfig

logger = logging.getLogger(__name__)


async def check_prompt_injection(text: str, config: GuardrailsConfig) -> bool:
    """Check for prompt injection using Groq Llama-Prompt-Guard.

    Returns True if the input is MALICIOUS.
    """
    client = AsyncGroq(api_key=config.groq_api_key)
    try:
        completion = await client.chat.completions.create(
            model=config.groq_model,
            messages=[{"role": "user", "content": text}],
        )
        raw = completion.choices[0].message.content.strip().upper()
        # Model may return "MALICIOUS"/"BENIGN" labels or a probability score (0.0-1.0)
        if raw in ("MALICIOUS", "BENIGN"):
            is_malicious = raw == "MALICIOUS"
        else:
            try:
                score = float(raw)
                is_malicious = score > 0.5
            except ValueError:
                is_malicious = "MALICIOUS" in raw
        if is_malicious:
            logger.warning(f"Prompt injection detected: {text[:80]}...")
        return is_malicious
    except Exception as e:
        logger.error(f"Prompt injection check failed: {e}")
        # Fail open - allow through if guard is down
        return False
    finally:
        await client.close()
