from dataclasses import dataclass


@dataclass
class GuardrailsConfig:
    groq_api_key: str
    enabled: bool = True
    groq_model: str = "meta-llama/llama-prompt-guard-2-86m"
    guardrails_model: str = "gemini-3.1-flash-lite-preview"
    # Backend for the scope + output LLM checks. "google" (Gemini, default) routes
    # through the shared google-genai LLMClient; "deepseek" routes to DeepSeek V4
    # over the OpenAI-compatible API. Prompt-injection stays on Groq regardless.
    guardrails_provider: str = "google"
    # DeepSeek credentials (only read when guardrails_provider == "deepseek").
    deepseek_base_url: str = ""
    deepseek_api_key: str = ""
    # Force reasoning off. Gemini uses thinking_level=minimal (bound in LLMClient);
    # DeepSeek uses extra_body={"thinking": {"type": "disabled"}}. See docs/MODELS.md.
    disable_thinking: bool = True
    # blacklisted_topics removed — output.py prompt is hardcoded with SARA +
    # Financial Advice logic. scope.py uses its own prompt templates (SARA_CHECK_PROMPT,
    # FINANCIAL_ADVICE_CHECK_PROMPT). Dynamic topic injection is not used anywhere.
