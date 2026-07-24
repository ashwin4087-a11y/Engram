"""Metrics schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MetricPoint(BaseModel):
    name: str
    value: float
    unit: str | None = None
    timestamp: datetime


class MetricsSummary(BaseModel):
    """Current metrics snapshot for a session."""
    session_id: UUID
    entity_count: int = 0
    fact_count: int = 0
    episode_count: int = 0
    relationship_count: int = 0
    contradiction_count: int = 0
    active_fact_count: int = 0
    graph_size: int = 0  # nodes + edges
    avg_context_tokens: float = 0.0
    total_observations: int = 0


class MetricsTimeline(BaseModel):
    """Time-series metrics for charts."""
    session_id: UUID
    series: dict[str, list[MetricPoint]]


class MetricsResponse(BaseModel):
    """Combined metrics response."""
    summary: MetricsSummary
    recent: list[MetricPoint] = []
