"""
Engram Backend — Main Application Entry Point
"""
from __future__ import annotations

import structlog
import socketio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.socket import sio
from app.core.database import database_manager

log = structlog.get_logger(__name__)

app = FastAPI(
    title="Engram Engine API",
    version="1.0.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix="/api/v1")

# Mount Socket.IO app
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
)

@app.on_event("startup")
async def on_startup():
    log.info("system.startup", status="initializing")
    await database_manager.startup()
    log.info("system.startup", status="database_initialized")

@app.on_event("shutdown")
async def on_shutdown():
    await database_manager.shutdown()
    log.info("system.shutdown", status="complete")