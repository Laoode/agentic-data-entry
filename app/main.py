import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.helpers.ratelimit import attach_rate_limiter
from app.routes import v1_router
from app.services.core.container import KlaudiaContainer
from app.services.core.orchestrator import KlaudiaOrchestrator
from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.validate_production_secrets()
    logger.info(f"Starting {settings.service_name} v{settings.version}")

    container = await KlaudiaContainer.create(settings)
    orchestrator = KlaudiaOrchestrator(container)

    app.state.container = container
    app.state.orchestrator = orchestrator

    yield

    await container.shutdown()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Klaudia Chatbot",
    version="1.0.0",
    lifespan=lifespan,
)

attach_rate_limiter(app)
app.include_router(v1_router)
