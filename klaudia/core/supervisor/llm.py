"""Provider-agnostic chat-LLM factory for the agentic stack.

One factory keeps the supervisor, routers, and react workers ignorant of which
backend they talk to. See docs/MODELS.md for the full provider matrix, the
per-provider thinking-mode mechanics, and the DeepSeek caveats.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

# Provider buckets. "openai" is kept as a back-compat alias for "vllm".
_GEMINI_PROVIDERS = frozenset({"google", "gemini", "vertexai"})
_VLLM_PROVIDERS = frozenset({"vllm", "qwen", "openai"})
_DEEPSEEK_PROVIDERS = frozenset({"deepseek"})
_OPENAI_COMPATIBLE = _VLLM_PROVIDERS | _DEEPSEEK_PROVIDERS

# Gemini 3 thinking budgets (generation_config). Binding is skipped when
# thinking_level is None, so legacy 1.x/2.x model strings stay unaffected.
_VALID_THINKING_LEVELS = frozenset({"none", "minimal", "low", "medium", "high"})

# OpenAI client rejects an empty api_key; a self-hosted vLLM started without
# --api-key ignores the value, so this placeholder is safe there.
_VLLM_PLACEHOLDER_KEY = "EMPTY"


def _openai_thinking_extra_body(
    provider: str, disable_thinking: bool
) -> Optional[dict[str, Any]]:
    """Return the provider-specific extra_body to turn reasoning off.

    Each OpenAI-compatible server toggles thinking differently:
        deepseek → {"thinking": {"type": "disabled"}}
        vllm/qwen → {"chat_template_kwargs": {"enable_thinking": False}}  (/no_think)
    None means "leave the server default untouched".
    """
    if not disable_thinking:
        return None
    if provider in _DEEPSEEK_PROVIDERS:
        return {"thinking": {"type": "disabled"}}
    if provider in _VLLM_PROVIDERS:
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return None


def build_chat_llm(
    *,
    model: str,
    provider: str = "google",
    temperature: float = 0.5,
    use_vertexai: bool = False,
    llm_api_key: Optional[str] = None,
    google_cloud_project: Optional[str] = None,
    google_cloud_location: Optional[str] = "global",
    openai_base_url: Optional[str] = None,
    openai_api_key: Optional[str] = None,
    thinking_level: Optional[str] = None,
    disable_thinking: bool = True,
) -> BaseChatModel:
    """Build a chat model for the configured provider.

    Args:
        provider: "google" (Gemini), "vllm" (Qwen on vLLM), or "deepseek".
        thinking_level: Gemini-only thinking budget. None = model default.
        disable_thinking: OpenAI-compatible only. Force thinking off via extra_body.
    """
    normalized = (provider or "google").strip().lower()
    if normalized in _OPENAI_COMPATIBLE:
        return _build_openai_llm(
            model=model,
            provider=normalized,
            temperature=temperature,
            base_url=openai_base_url,
            api_key=openai_api_key,
            disable_thinking=disable_thinking,
        )
    if normalized in _GEMINI_PROVIDERS:
        return _build_gemini_llm(
            model=model,
            temperature=temperature,
            use_vertexai=use_vertexai,
            llm_api_key=llm_api_key,
            google_cloud_project=google_cloud_project,
            google_cloud_location=google_cloud_location,
            thinking_level=thinking_level,
        )
    raise ValueError(
        f"Unknown MODEL_PROVIDER={provider!r}. "
        "Valid values: 'google', 'vllm', 'deepseek'."
    )


def _build_openai_llm(
    *,
    model: str,
    provider: str,
    temperature: float,
    base_url: Optional[str],
    api_key: Optional[str],
    disable_thinking: bool,
) -> BaseChatModel:
    """Build a ChatOpenAI bound to an OpenAI-compatible endpoint."""
    from langchain_openai import ChatOpenAI

    if not base_url:
        raise ValueError(
            f"MODEL_PROVIDER={provider} requires a base URL "
            "(DEEPSEEK_BASE_URL or VLLM_LLM_ENDPOINT)."
        )

    return ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=api_key or _VLLM_PLACEHOLDER_KEY,
        temperature=temperature,
        extra_body=_openai_thinking_extra_body(provider, disable_thinking),
    )


def _build_gemini_llm(
    *,
    model: str,
    temperature: float,
    use_vertexai: bool,
    llm_api_key: Optional[str],
    google_cloud_project: Optional[str],
    google_cloud_location: Optional[str],
    thinking_level: Optional[str],
) -> BaseChatModel:
    """Build a ChatGoogleGenerativeAI bound to Vertex AI or the Gemini Dev API."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    if use_vertexai:
        if not google_cloud_project:
            raise ValueError("use_vertexai=True but google_cloud_project is empty")
        llm: BaseChatModel = ChatGoogleGenerativeAI(
            model=model,
            vertexai=True,
            project=google_cloud_project,
            location=google_cloud_location or "global",
            temperature=temperature,
        )
    else:
        if not llm_api_key:
            raise ValueError("llm_api_key is required when use_vertexai=False")
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=llm_api_key,
            temperature=temperature,
        )

    if thinking_level is not None:
        level = thinking_level.lower()
        if level not in _VALID_THINKING_LEVELS:
            raise ValueError(
                f"Invalid thinking_level={thinking_level!r}. "
                f"Valid values: {sorted(_VALID_THINKING_LEVELS)}"
            )
        llm = llm.bind(generation_config={"thinking_config": {"thinking_level": level}})

    return llm


def _unwrap(llm: Any) -> Any:
    """Strip RunnableBinding layers (.bind()/.with_config()) to the base model."""
    base = llm
    while hasattr(base, "bound"):
        base = base.bound
    return base


def _is_openai_llm(llm: Any) -> bool:
    """True if llm is (or wraps) a ChatOpenAI instance."""
    return _unwrap(llm).__class__.__name__ == "ChatOpenAI"


def with_structured(llm: BaseChatModel, schema: Any):
    """Provider-agnostic structured output.

    Gemini uses its native path. For OpenAI-compatible servers the method is
    picked per backend: DeepSeek goes through function-calling (its reliable
    tool path), vLLM/Qwen through json_schema so the constraint rides on guided
    decoding even when the server lacks --enable-auto-tool-choice.
    """
    if not _is_openai_llm(llm):
        return llm.with_structured_output(schema)

    base = _unwrap(llm)
    model_name = (
        getattr(base, "model_name", None) or getattr(base, "model", "") or ""
    ).lower()
    method = "function_calling" if "deepseek" in model_name else "json_schema"
    return llm.with_structured_output(schema, method=method)


async def ainvoke_route(
    chain: Any, messages: Any, *, retries: int = 1
) -> Optional[dict]:
    """Invoke a structured-output router chain, tolerating malformed LLM output.

    OpenAI-compatible backends (notably DeepSeek function-calling) occasionally
    emit tool-call arguments that are not valid JSON — e.g. a long multi-line
    `response` value with unescaped newlines, or a truncated string. LangChain's
    tool parser then yields no object and `.ainvoke` returns None, which crashes
    any caller doing `result["next"]`. Resample up to `retries` extra times
    (temperature > 0 makes a retry a real second chance), then return None so the
    caller falls back deterministically instead of raising and killing the turn.
    """
    result: Any = None
    for attempt in range(retries + 1):
        try:
            result = await chain.ainvoke(messages)
        except Exception as exc:  # parser/transport failure — treat as no result
            logger.warning(
                "structured route invoke failed (attempt %d): %s", attempt + 1, exc
            )
            result = None
        if isinstance(result, dict):
            return result
        if attempt < retries:
            logger.warning(
                "structured route returned no valid object (attempt %d); retrying",
                attempt + 1,
            )
    return None
