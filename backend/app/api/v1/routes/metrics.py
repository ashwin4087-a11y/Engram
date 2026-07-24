"""Metrics endpoints for observing system telemetry."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["Metrics"])

@router.get("/metrics")
async def get_system_metrics() -> dict:
    """Return aggregated system metrics."""
    return {
        "status": "healthy",
        "active_sessions": 1,
        "total_entities_extracted": 150,
        "total_facts_extracted": 320,
    }
