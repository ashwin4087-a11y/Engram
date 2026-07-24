"""Entity schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import EngramBase


class EntityResponse(EngramBase):
    id: UUID
    session_id: UUID
    entity_type: str
    name: str
    description: str | None = None
    importance: float
    confidence: float
    access_count: int
    is_active: bool
    aliases: list[str] = []
    created_at: datetime
    updated_at: datetime


class EntityBrief(BaseModel):
    """Lightweight entity representation for graph nodes."""
    id: UUID
    name: str
    entity_type: str
    importance: float
    is_active: bool


class EntityListResponse(BaseModel):
    entities: list[EntityResponse]
    total: int
