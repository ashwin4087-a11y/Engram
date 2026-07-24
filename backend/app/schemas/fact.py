"""Fact schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import EngramBase


class FactResponse(EngramBase):
    id: UUID
    session_id: UUID
    entity_id: UUID | None = None
    statement: str
    status: str
    importance: float
    confidence: float
    access_count: int
    source_text: str | None = None
    created_at: datetime


class FactBrief(BaseModel):
    """Lightweight fact for context bundles."""
    id: UUID
    statement: str
    importance: float
    confidence: float
    entity_name: str | None = None
