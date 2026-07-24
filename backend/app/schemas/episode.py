"""Episode schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.common import EngramBase


class EpisodeResponse(EngramBase):
    id: UUID
    session_id: UUID
    summary: str
    level: int
    importance: float
    confidence: float
    is_active: bool
    turn_number: int | None = None
    parent_episode_ids: list[UUID] | None = None
    created_at: datetime


class EpisodeBrief(BaseModel):
    """Lightweight episode for context bundles."""
    id: UUID
    summary: str
    level: int
    importance: float
