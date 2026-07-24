"""Common schema types shared across all API schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class EngramBase(BaseModel):
    """Base model for all Engram schemas — enables orm_mode and forbids extra."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Any | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    database: str = "connected"
    redis: str = "connected"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime | None = None
