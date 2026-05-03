from fastapi import APIRouter

from app.routes.v1.chat import router as chat_router
from app.routes.v1.health import router as health_router
from app.routes.v1.sessions import router as sessions_router
from app.routes.v1.sheets import router as sheets_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(health_router)
v1_router.include_router(chat_router)
v1_router.include_router(sessions_router)
v1_router.include_router(sheets_router)

__all__ = ["v1_router"]
