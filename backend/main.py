"""
Engram Backend — Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import socketio
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import database_manager
from app.core.logging import configure_logging
from app.core.redis import redis_manager
from app.core.security import RateLimitMiddleware, RequestIDMiddleware
from app.core.socket import sio

configure_logging()
log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("engram.startup", version="0.1.0", environment=settings.ENVIRONMENT)
    await database_manager.startup()
    await redis_manager.startup()
    log.info("engram.infrastructure.ready")
    yield
    log.info("engram.shutdown")
    await redis_manager.shutdown()
    await database_manager.shutdown()


def create_application() -> FastAPI:
    app = FastAPI(
        title="Engram — AI Memory Infrastructure",
        version="0.1.0",
        description="Production-grade AI memory platform with hybrid retrieval, knowledge graphs, and structured world models.",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Middleware chain
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Mount Socket.IO
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
    return socket_app  # type: ignore[return-value]


application = create_application()
