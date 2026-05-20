from dataclasses import dataclass


@dataclass
class GuardrailsConfig:
    groq_api_key: str
    groq_model: str = "meta-llama/llama-prompt-guard-2-86m"
    guardrails_model: str = "gemini-3.1-flash-lite-preview"
    # Blacklisted topics
    blacklisted_topics: tuple[str, ...] = ("SARA", "Financial Advice")
