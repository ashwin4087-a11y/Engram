"""Observe endpoint schemas — memory compiler input/output."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.entity import EntityResponse
from app.schemas.fact import FactResponse
from app.schemas.relationship import RelationshipResponse


class ObserveRequest(BaseModel):
    """User observation to be processed by the memory compiler."""
    text: str = Field(..., min_length=1, max_length=10000)
    session_id: UUID
    metadata: dict | None = None


class CompilerResult(BaseModel):
    """Structured output from the memory compiler pipeline."""
    entities: list[EntityResponse] = []
    facts: list[FactResponse] = []
    relationships: list[RelationshipResponse] = []
    episode_summary: str | None = None
    contradictions_detected: int = 0
    duplicates_merged: int = 0
    compiler_latency_ms: int = 0


class ObserveResponse(BaseModel):
    """Response from the /observe endpoint."""
    session_id: UUID
    turn_number: int
    compiler_result: CompilerResult
    reply: str | None = None
    timestamp: datetime
