import logging
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

        # MCP registries
        container.mcp_sqlite = MCPToolRegistry("mcp-sqlite", "http://localhost:8001/sse")
        container.mcp_gsheets = MCPToolRegistry("mcp-gsheets", "http://localhost:8002/sse")
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
