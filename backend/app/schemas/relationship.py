"""Relationship schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import EngramBase


class RelationshipResponse(EngramBase):
    id: UUID
    session_id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: str
    confidence: float
    is_active: bool
    source_text: str | None = None
    valid_from: datetime
    valid_until: datetime | None = None
    created_at: datetime


class RelationshipBrief(BaseModel):
    """Lightweight relationship for graph edges."""
    id: UUID
    source_entity_id: UUID
    target_entity_id: UUID
    relation_type: str
    confidence: float
    is_active: bool
