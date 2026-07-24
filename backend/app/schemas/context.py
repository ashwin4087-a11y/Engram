"""Context compiler schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.memory import RetrievedMemory


class ContextRequest(BaseModel):
    session_id: UUID
    query: str | None = None
    token_budget: int = Field(default=1500, ge=500, le=8000)


class ContextBundleResponse(BaseModel):
    """The compiled context bundle — ready for LLM consumption."""
    session_id: UUID
    turn_number: int
    token_count: int
    token_budget: int
    memories: list[RetrievedMemory]
    context_text: str
    compilation_latency_ms: int = 0
    created_at: datetime


class ReasonRequest(BaseModel):
    """Request for the /reason endpoint — one agent reasoning step."""
    session_id: UUID
    query: str = Field(..., min_length=1, max_length=10000)
    token_budget: int = Field(default=1500, ge=500, le=8000)


class ReasonResponse(BaseModel):
    """Response from the agent runtime."""
    session_id: UUID
    response: str
    context_token_count: int
    llm_latency_ms: int = 0
    total_latency_ms: int = 0
    memories_used: int = 0
