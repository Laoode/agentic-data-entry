"""Bind the e2e suite to its own datastores, away from the development ones.

The suite writes real rows: users, sessions, conversations, ledger grids, blobs,
dedup keys. Sharing a database with development means a bench run and ordinary
work corrupt each other - which already happened once, when a Postgres test that
truncates the app tables wiped a bench's live sessions mid-run.

So the sandbox gets its own Postgres instance (compose profile `sandbox`, port
5433), its own Redis logical database, and its own object-store bucket. Every
one of those is reachable by changing an environment variable, and the MCP
servers are spawned with `dict(os.environ)`, so rebinding here before the
container is built carries all the way down to the ledger subprocess.

Import this module for its effect BEFORE anything calls `get_settings()`: the
settings object is built once and cached, so a late rebind would be ignored.
`conftest.py` does that at import time.

Opt out with `E2E_SANDBOX=0` to run against whatever `.env` says. Override any
single target with `E2E_DATABASE_URL`, `E2E_REDIS_URL`, `E2E_MINIO_BUCKET`.
"""

from __future__ import annotations

import os

# Where the sandbox lives when nothing overrides it. The Postgres port is 5433,
# not 5432: a separate server, not a separate database on the development one,
# so the whole store can be dropped and rebuilt without touching real data.
SANDBOX_DEFAULTS: dict[str, str] = {
    "DATABASE_URL": "postgresql://klaudia:klaudia@localhost:5433/klaudia_sandbox",
    "REDIS_URL": "redis://localhost:6379/9",
    "MINIO_BUCKET": "klaudia-sandbox-blobs",
}

# Set on the environment so a test can report which store it ran against.
MARKER = "E2E_SANDBOX_ACTIVE"


class SandboxNotIsolated(RuntimeError):
    """The sandbox resolved to the same store development is using."""


def sandbox_enabled(env: dict[str, str] | None = None) -> bool:
    """True unless the runner explicitly opted out with E2E_SANDBOX=0."""
    environ = os.environ if env is None else env
    return environ.get("E2E_SANDBOX", "1").strip().lower() not in ("0", "false", "no")


def bind_sandbox(env: dict[str, str] | None = None) -> dict[str, str]:
    """Repoint the datastore env vars at the sandbox and return what changed.

    Args:
        env: Environment mapping to mutate. Defaults to `os.environ`.

    Returns:
        The variables that were rebound, as {name: sandbox value}. Empty when
        the sandbox is disabled.

    Raises:
        SandboxNotIsolated: If a resolved sandbox target equals the development
            value it is meant to replace. Falling through silently would let the
            suite write its fixtures into the development store while every log
            line still claimed it was sandboxed.
    """
    environ = os.environ if env is None else env
    if not sandbox_enabled(environ):
        return {}
    if environ.get(MARKER) == "1":
        # Already bound. Re-checking would compare the sandbox values against
        # themselves and read as a collision, so a second import must be a
        # no-op rather than an error.
        return {key: environ[key] for key in SANDBOX_DEFAULTS if key in environ}

    applied: dict[str, str] = {}
    for key, default in SANDBOX_DEFAULTS.items():
        development = environ.get(key, "")
        sandbox = environ.get(f"E2E_{key}") or default
        if development and development == sandbox:
            raise SandboxNotIsolated(
                f"{key} is identical for development and sandbox ({sandbox!r}). "
                f"Point E2E_{key} somewhere else, or set E2E_SANDBOX=0 to run "
                f"against the development store on purpose."
            )
        environ[key] = sandbox
        applied[key] = sandbox

    environ[MARKER] = "1"
    return applied


def describe(env: dict[str, str] | None = None) -> str:
    """One line naming the stores in use, for the run header."""
    environ = os.environ if env is None else env
    if environ.get(MARKER) != "1":
        return "e2e sandbox OFF — running against the development stores"
    return "e2e sandbox ON — " + ", ".join(
        f"{key}={environ.get(key, '')}" for key in SANDBOX_DEFAULTS
    )
