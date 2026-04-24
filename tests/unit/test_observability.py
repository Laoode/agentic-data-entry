"""Unit tests for LangfuseService — fail-open semantics and config shape.

These are hermetic: they do not hit the Langfuse network. They verify that:
  1. Missing/disabled credentials degrade to no-op (enabled=False)
  2. langchain_config() returns {} when disabled
  3. span() yields None when disabled, never raises
  4. trace_attributes() is a no-op when disabled
  5. flush()/shutdown() are safe when disabled
"""

from __future__ import annotations

import pytest

from app.services.core.observability import LangfuseService
from config.settings import Settings


def _settings(**overrides) -> Settings:
    base = dict(
        LANGFUSE_ENABLED=True,
        LANGFUSE_PUBLIC_KEY="",
        LANGFUSE_SECRET_KEY="",
        LANGFUSE_BASE_URL="https://cloud.langfuse.com",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.mark.unit
def test_missing_credentials_disables_tracing():
    svc = LangfuseService(_settings())
    assert svc.enabled is False
    assert svc.client is None
    assert svc.callback_handler is None


@pytest.mark.unit
def test_explicit_disable_flag_disables_tracing():
    svc = LangfuseService(
        _settings(
            LANGFUSE_ENABLED=False,
            LANGFUSE_PUBLIC_KEY="pk-test",
            LANGFUSE_SECRET_KEY="sk-test",
        )
    )
    assert svc.enabled is False


@pytest.mark.unit
def test_langchain_config_is_empty_when_disabled():
    svc = LangfuseService(_settings())
    cfg = svc.langchain_config(session_id=1, user_id=2, tags=["t"])
    assert cfg == {}


@pytest.mark.unit
def test_span_yields_none_when_disabled():
    svc = LangfuseService(_settings())
    with svc.span("noop", as_type="span") as obs:
        assert obs is None


@pytest.mark.unit
def test_trace_attributes_is_noop_when_disabled():
    svc = LangfuseService(_settings())
    with svc.trace_attributes(session_id=1, user_id=2, tags=["x"]):
        pass


@pytest.mark.unit
def test_flush_and_shutdown_safe_when_disabled():
    svc = LangfuseService(_settings())
    svc.flush()
    svc.shutdown()
