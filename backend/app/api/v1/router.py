"""
API V1 Master Router — combines all domain sub-routers.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import consolidation, graph, health, memory, metrics, observe, query, sessions, timeline, reason, entities

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(sessions.router)
api_router.include_router(observe.router)
api_router.include_router(graph.router)
api_router.include_router(memory.router)
api_router.include_router(consolidation.router)
api_router.include_router(query.router)
api_router.include_router(timeline.router)
api_router.include_router(metrics.router)
api_router.include_router(reason.router)
api_router.include_router(entities.router)
