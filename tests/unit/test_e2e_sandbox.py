"""Hermetic tests for the e2e sandbox binding.

The property that matters: a run either uses stores that are provably not the
development ones, or it refuses to start. A silent fallback to the development
database is the failure this guard exists to prevent.
"""

import pytest

from tests.e2e.sandbox import (
    MARKER,
    SANDBOX_DEFAULTS,
    SandboxNotIsolated,
    bind_sandbox,
    describe,
    sandbox_enabled,
)


def _development_env() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgresql://klaudia:klaudia@localhost:5432/klaudia",
        "REDIS_URL": "redis://localhost:6379/0",
        "MINIO_BUCKET": "klaudia-blobs",
    }


def test_binding_moves_every_store_off_the_development_one():
    env = _development_env()
    development = dict(env)

    applied = bind_sandbox(env)

    assert set(applied) == set(SANDBOX_DEFAULTS)
    for key in SANDBOX_DEFAULTS:
        assert env[key] != development[key], key
    assert env[MARKER] == "1"


def test_postgres_sandbox_is_a_separate_server_not_a_separate_database():
    """Port 5433 so the whole store can be dropped without touching dev data."""
    env = _development_env()
    bind_sandbox(env)
    assert ":5433/" in env["DATABASE_URL"]


def test_per_store_override_is_honored():
    env = _development_env()
    env["E2E_DATABASE_URL"] = "postgresql://u:p@somewhere:6000/other"

    bind_sandbox(env)

    assert env["DATABASE_URL"] == "postgresql://u:p@somewhere:6000/other"
    # The stores nobody overrode still move to their defaults.
    assert env["REDIS_URL"] == SANDBOX_DEFAULTS["REDIS_URL"]


def test_an_override_that_collides_with_development_is_refused():
    env = _development_env()
    env["E2E_DATABASE_URL"] = env["DATABASE_URL"]

    with pytest.raises(SandboxNotIsolated) as exc:
        bind_sandbox(env)

    assert "DATABASE_URL" in str(exc.value)
    # Nothing was rebound: the run stops rather than half-isolating.
    assert env["DATABASE_URL"] == _development_env()["DATABASE_URL"]


def test_opting_out_leaves_the_environment_untouched():
    env = _development_env()
    env["E2E_SANDBOX"] = "0"
    development = dict(env)

    assert bind_sandbox(env) == {}
    assert env == development
    assert not sandbox_enabled(env)


def test_binding_is_idempotent():
    """Re-importing (or a second call) must not chain the rebind onto itself."""
    env = _development_env()
    first = bind_sandbox(env)
    second = bind_sandbox(env)
    assert first == second


def test_an_empty_development_value_is_not_treated_as_a_collision():
    """A fresh checkout with no DATABASE_URL set still gets a sandbox."""
    env: dict[str, str] = {}
    bind_sandbox(env)
    assert env["DATABASE_URL"] == SANDBOX_DEFAULTS["DATABASE_URL"]


def test_describe_names_the_stores_when_active():
    env = _development_env()
    bind_sandbox(env)
    line = describe(env)
    assert "sandbox ON" in line
    assert "5433" in line


def test_describe_says_so_when_disabled():
    env = _development_env()
    env["E2E_SANDBOX"] = "0"
    bind_sandbox(env)
    assert "sandbox OFF" in describe(env)
