import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config.settings import Settings
from app.services.core.llm_client import LLMClient
from app.services.core.observability import LangfuseService
from app.services.extraction.infra.db_client import AppDBClient
from app.services.extraction.infra.dedup_cache import DedupCache
from app.services.extraction.infra.kie_client import KIEClient
from app.services.extraction.infra.object_store import MinIOClient
from app.services.extraction.ingest import IngestService
from app.services.extraction.agents.base import ExtractionAgent
from app.services.guardrails import GuardrailsAgent, GuardrailsConfig
from klaudia.core.supervisor.agent import SupervisorAgent
from klaudia.interfaces.tool_registry import MCPToolRegistry

logger = logging.getLogger(__name__)

# Project root resolves to the repo root regardless of where uvicorn is launched.
# container.py lives at app/services/core/container.py — three parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _ensure_gcp_credentials(settings: Settings) -> None:
    """Resolve GOOGLE_APPLICATION_CREDENTIALS to an absolute path and export it.

    The Google SDKs (google-genai, google-auth used by langchain-google-vertexai)
    read this env var directly. A relative path breaks for MCP subprocesses that
    chdir into mcp-sqlite/ or mcp-gsheets/. Resolving once at startup keeps the
    file discoverable regardless of CWD and lets subprocesses inherit it.
    """
    raw = settings.google_application_credentials
    if not raw:
        return
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (_PROJECT_ROOT / raw).resolve()
    if not candidate.is_file():
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS=%s does not exist (resolved=%s)",
            raw,
            candidate,
        )
        return
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(candidate)
    logger.info("GOOGLE_APPLICATION_CREDENTIALS resolved to %s", candidate)


def _build_mcp_registries(settings: Settings) -> tuple[MCPToolRegistry, MCPToolRegistry]:
    """Construct (mcp_sqlite, mcp_gsheets) registries based on configured transport.

    stdio: spawn the server as a subprocess of FastAPI. No port, no SSE keep-alive
           required — the connection is a pipe owned by this process.
    sse:   legacy mode; servers must already be running on 8001/8002 (per startup.sh).
    """
    transport = (settings.mcp_transport or "stdio").lower()

    if transport == "stdio":
        python_bin = sys.executable
        sqlite_db_abs = str((_PROJECT_ROOT / settings.sqlite_db).resolve())
        # Subprocess inherits the FastAPI env so that LLM/OCR/etc. credentials
        # configured for the parent are also visible to the MCP server.
        # We override SQLITE_DB with an absolute path because mcp-sqlite's cwd
        # is its own directory, and a relative "app_dev.db" would resolve to
        # the wrong place there.
        sqlite_env = {**os.environ, "SQLITE_DB": sqlite_db_abs}

        sqlite_reg = MCPToolRegistry.from_stdio(
            "mcp-sqlite",
            command=python_bin,
            args=["main.py", "--transport", "stdio"],
            cwd=str(_PROJECT_ROOT / "mcp-sqlite"),
            env=sqlite_env,
        )
        gsheets_reg = MCPToolRegistry.from_stdio(
            "mcp-gsheets",
            command=python_bin,
            args=["main.py", "--transport", "stdio"],
            cwd=str(_PROJECT_ROOT / "mcp-gsheets"),
            env=dict(os.environ),
        )
        return sqlite_reg, gsheets_reg

    if transport == "sse":
        return (
            MCPToolRegistry("mcp-sqlite", "http://localhost:8001/sse"),
            MCPToolRegistry("mcp-gsheets", "http://localhost:8002/sse"),
        )

    raise ValueError(
        f"Unknown MCP_TRANSPORT={settings.mcp_transport!r}; expected 'stdio' or 'sse'"
    )


class KlaudiaContainer:
    """Service container - manages lifecycle of all services."""

    def __init__(self) -> None:
        self.settings: Optional[Settings] = None
        self.llm_client: Optional[LLMClient] = None
        self.kie_client: Optional[KIEClient] = None
        self.db_client: Optional[AppDBClient] = None
        self.dedup_cache: Optional[DedupCache] = None
        self.object_store: Optional[MinIOClient] = None
        self.ingest_service: Optional[IngestService] = None
        self.mcp_sqlite: Optional[MCPToolRegistry] = None
        self.mcp_gsheets: Optional[MCPToolRegistry] = None
        self.guardrails: Optional[GuardrailsAgent] = None
        self.supervisor: Optional[SupervisorAgent] = None
        self.extraction_agent: Optional[ExtractionAgent] = None
        self.langfuse: Optional[LangfuseService] = None

    @classmethod
    async def create(cls, settings: Settings) -> "KlaudiaContainer":
        container = cls()
        container.settings = settings

        # Resolve GCP creds path before any SDK touches it (MCP subprocesses
        # spawned later inherit os.environ).
        _ensure_gcp_credentials(settings)

        # Observability (must be first so other services can reference it)
        container.langfuse = LangfuseService(settings)

        # LLM clients
        container.llm_client = LLMClient(settings, langfuse=container.langfuse)
        container.kie_client = KIEClient(settings, langfuse=container.langfuse)

        # Database
        container.db_client = AppDBClient(settings)
        await container.db_client.connect()

        # Dedup cache (Redis) — fail-soft so dev can run without Redis
        container.dedup_cache = DedupCache(settings)
        try:
            await container.dedup_cache.connect()
        except Exception as e:
            logger.warning(
                "Redis unavailable (%s). Dedup cache disabled; SQLite-only fallback.",
                e,
            )
            container.dedup_cache = None

        # Object store (MinIO) — required; uploads have nowhere to go without it
        container.object_store = MinIOClient(settings)
        try:
            await container.object_store.ensure_bucket()
        except Exception as e:
            logger.error(
                "MinIO unavailable (%s). Image/PDF uploads will fail.", e
            )
            # Keep instance; calls will surface specific errors at upload time

        # MCP registries (transport selected via MCP_TRANSPORT setting)
        container.mcp_sqlite, container.mcp_gsheets = _build_mcp_registries(settings)
        logger.info(f"MCP transport: {settings.mcp_transport}")
        await container.mcp_sqlite.connect()
        await container.mcp_gsheets.connect()

        # Ingest service — drives dedup pipeline. ExtractionAgent is now a thin
        # observability facade over this.
        if container.dedup_cache is None:
            from app.services.extraction.infra.dedup_cache import DedupCache as _DC
            # Provide a minimal in-memory shim so IngestService works without
            # Redis. Cache misses always; persistence still goes to SQLite.
            container.dedup_cache = _NullDedupCache()  # type: ignore[assignment]

        container.ingest_service = IngestService(
            settings=settings,
            db=container.db_client,
            cache=container.dedup_cache,  # type: ignore[arg-type]
            store=container.object_store,
            ocr=container.kie_client,
            langfuse=container.langfuse,
        )

        # Extraction agent (now a facade)
        container.extraction_agent = ExtractionAgent(
            ingest_service=container.ingest_service,
            langfuse=container.langfuse,
        )

        # Guardrails
        guardrails_config = GuardrailsConfig(
            enabled=settings.guardrails_enabled,
            groq_api_key=settings.groq_api_key,
            groq_model=settings.llm_guardrails_prompt_inj,
            guardrails_model=settings.llm_guardrails_model,
        )
        container.guardrails = GuardrailsAgent(
            container.llm_client, guardrails_config, langfuse=container.langfuse
        )

        # Supervisor
        container.supervisor = SupervisorAgent(
            llm_api_key=settings.llm_api_key,
            llm_model=settings.llm_model,
            mcp_sqlite=container.mcp_sqlite,
            mcp_gsheets=container.mcp_gsheets,
            langfuse=container.langfuse,
            provider=settings.model_provider,
            use_vertexai=settings.google_genai_use_vertexai,
            google_cloud_project=settings.google_cloud_project,
            google_cloud_location=settings.google_cloud_location,
            openai_base_url=settings.llm_endpoint,
            openai_api_key=settings.llm_openai_api_key,
            disable_thinking=settings.llm_disable_thinking,
            temperature=settings.llm_temperature,
            thinking_level_routing=settings.llm_thinking_level_routing,
            thinking_level_worker=settings.llm_thinking_level_worker,
        )

        logger.info("KlaudiaContainer initialized")
        return container

    async def shutdown(self) -> None:
        logger.info("Starting graceful shutdown...")
        if self.llm_client:
            await self.llm_client.shutdown()
        if self.kie_client:
            await self.kie_client.shutdown()
        if self.mcp_sqlite:
            await self.mcp_sqlite.disconnect()
        if self.mcp_gsheets:
            await self.mcp_gsheets.disconnect()
        if isinstance(self.dedup_cache, DedupCache):
            await self.dedup_cache.close()
        if self.db_client:
            await self.db_client.close()
        if self.langfuse:
            self.langfuse.shutdown()
        logger.info("Shutdown complete")


class _NullDedupCache:
    """Null-object replacement for DedupCache when Redis is down.

    Every read misses, every write is a no-op. IngestService keeps working
    against SQLite alone — slower, but no functional regression.
    """

    async def get_blob(self, *_a, **_kw):  # noqa: D401
        return None

    async def set_blob(self, *_a, **_kw):
        return None

    async def get_extraction(self, *_a, **_kw):
        return None

    async def set_extraction(self, *_a, **_kw):
        return None

    async def queue_depth(self, *_a, **_kw):
        return 0

    async def close(self):
        return None