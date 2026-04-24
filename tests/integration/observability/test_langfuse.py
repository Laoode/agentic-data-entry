"""Live Langfuse smoke tests.

Skipped unless LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY are set in the env.
These emit real traces so the user can visually verify the pipeline on
https://cloud.langfuse.com. They do NOT assert on remote trace state —
Langfuse has no synchronous read-after-write guarantee.

Each test only asserts that:
  1. LangfuseService initialises without error
  2. The instrumented call path runs cleanly
  3. flush() succeeds (SDK acknowledges the batch was sent)

End-to-end Gemini/Groq-through-instrumentation is covered indirectly by the
existing `test_streaming.py` / `test_guardrails.py` suites — they exercise the
same LLMClient / GuardrailsAgent code paths that now carry spans.

Run manually:
    uv run pytest tests/integration/observability/ -v -s
"""

from __future__ import annotations

import pytest

from app.services.core.observability import LangfuseService
from config.settings import get_settings


def _creds_present() -> bool:
    s = get_settings()
    return bool(
        s.langfuse_enabled
        and s.langfuse_public_key
        and s.langfuse_secret_key
    )


pytestmark = pytest.mark.skipif(
    not _creds_present(),
    reason="Langfuse credentials not set — skipping live smoke tests",
)


@pytest.fixture(scope="module")
def langfuse():
    """Module-scoped: Langfuse 4.x uses a process-global OTel tracer, so
    repeatedly init/shutdown between tests can deadlock. One instance, one
    shutdown at the end of the module."""
    svc = LangfuseService(get_settings())
    yield svc
    svc.flush()
    svc.shutdown()


def test_service_initialises_with_real_credentials(langfuse):
    assert langfuse.enabled is True
    assert langfuse.client is not None
    assert langfuse.callback_handler is not None


def test_manual_span_emits_without_error(langfuse):
    with langfuse.span(
        "smoke.manual_span",
        as_type="span",
        input={"probe": "hello"},
        metadata={"test": "test_manual_span_emits_without_error"},
    ) as obs:
        assert obs is not None
        obs.update(output={"probe": "world"})


def test_trace_attributes_wraps_nested_spans(langfuse):
    with langfuse.trace_attributes(
        session_id=99999, user_id=1, tags=["smoke", "unit"]
    ):
        with langfuse.span("smoke.nested", as_type="agent") as obs:
            assert obs is not None


def test_langchain_config_shape_when_enabled(langfuse):
    cfg = langfuse.langchain_config(
        session_id=42,
        user_id=7,
        tags=["klaudia", "smoke"],
        run_name="smoke.run",
    )
    assert "callbacks" in cfg and cfg["callbacks"]
    assert cfg.get("metadata", {}).get("langfuse_session_id") == "42"
    assert cfg.get("metadata", {}).get("langfuse_user_id") == "7"
    assert cfg.get("metadata", {}).get("langfuse_tags") == ["klaudia", "smoke"]
    assert cfg.get("run_name") == "smoke.run"
