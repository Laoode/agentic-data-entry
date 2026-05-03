import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config.settings import Settings
from app.services.core.llm_client import LLMClient
from app.services.core.observability import LangfuseService
from app.services.extraction.infra.db_client import AppDBClient
from app.services.extraction.infra.ocr_client import OCRClient
from app.services.extraction.agents.base import ExtractionAgent
from app.services.guardrails import GuardrailsAgent, GuardrailsConfig
from klaudia.core.supervisor.agent import SupervisorAgent
from klaudia.interfaces.tool_registry import MCPToolRegistry

logger = logging.getLogger(__name__)

# Project root resolves to the repo root regardless of where uvicorn is launched.
# container.py lives at app/services/core/container.py — three parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[3]


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
        self.llm_client: Optional[LLMClient] = None
        self.ocr_client: Optional[OCRClient] = None
        self.db_client: Optional[AppDBClient] = None
        self.mcp_sqlite: Optional[MCPToolRegistry] = None
        self.mcp_gsheets: Optional[MCPToolRegistry] = None
        self.guardrails: Optional[GuardrailsAgent] = None
        self.supervisor: Optional[SupervisorAgent] = None
        self.extraction_agent: Optional[ExtractionAgent] = None
        self.langfuse: Optional[LangfuseService] = None

    @classmethod
    async def create(cls, settings: Settings) -> "KlaudiaContainer":
        container = cls()

        # Observability (must be first so other services can reference it)
        container.langfuse = LangfuseService(settings)

        # LLM clients
        container.llm_client = LLMClient(settings, langfuse=container.langfuse)
        container.ocr_client = OCRClient(settings, langfuse=container.langfuse)

        # Database
        container.db_client = AppDBClient(settings)
        await container.db_client.connect()

        # MCP registries (transport selected via MCP_TRANSPORT setting)
        container.mcp_sqlite, container.mcp_gsheets = _build_mcp_registries(settings)
        logger.info(f"MCP transport: {settings.mcp_transport}")
        await container.mcp_sqlite.connect()
        await container.mcp_gsheets.connect()

        # Extraction agent (no LLM dep — GLM-OCR returns JSON directly)
        container.extraction_agent = ExtractionAgent(
            ocr_client=container.ocr_client,
            db_client=container.db_client,
            langfuse=container.langfuse,
        )

        # Guardrails
        guardrails_config = GuardrailsConfig(
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
        )

        logger.info("KlaudiaContainer initialized")
        return container

    async def shutdown(self) -> None:
        logger.info("Starting graceful shutdown...")
        if self.llm_client:
            await self.llm_client.shutdown()
        if self.ocr_client:
            await self.ocr_client.shutdown()
        if self.mcp_sqlite:
            await self.mcp_sqlite.disconnect()
        if self.mcp_gsheets:
            await self.mcp_gsheets.disconnect()
        if self.db_client:
            await self.db_client.close()
        if self.langfuse:
            self.langfuse.shutdown()
        logger.info("Shutdown complete")
