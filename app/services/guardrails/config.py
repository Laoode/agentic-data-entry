from dataclasses import dataclass


@dataclass
class GuardrailsConfig:
    groq_api_key: str
    groq_model: str = "meta-llama/llama-prompt-guard-2-86m"
    guardrails_model: str = "gemini-3.1-flash-lite-preview"
    # blacklisted_topics removed — output.py prompt is hardcoded with SARA +
    # Financial Advice logic. scope.py uses its own prompt templates (SARA_CHECK_PROMPT,
    # FINANCIAL_ADVICE_CHECK_PROMPT). Dynamic topic injection is not used anywhere.