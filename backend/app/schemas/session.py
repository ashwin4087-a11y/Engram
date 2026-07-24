"""Session schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import EngramBase


class SessionCreate(BaseModel):
    title: str | None = Field(None, max_length=255)
    metadata: dict | None = None


class SessionResponse(EngramBase):
    id: UUID
    title: str | None
    is_active: bool
    turn_count: int
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
    total: int
