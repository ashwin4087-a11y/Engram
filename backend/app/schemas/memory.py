"""Memory and retrieval schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievedMemory(BaseModel):
    """A single memory unit retrieved by the hybrid retrieval engine."""
    memory_type: str  # "fact" | "episode" | "entity"
    content: str
    score: float = Field(ge=0.0, le=1.0)
    source_id: UUID
    entity_name: str | None = None

    # Score breakdown for explainability
    similarity_score: float = 0.0
    recency_score: float = 0.0
    importance_score: float = 0.0
    confidence_score: float = 0.0


class MemoryResponse(BaseModel):
    """Response for /memory endpoint — retrieved memories with scores."""
    session_id: UUID
    query: str
    memories: list[RetrievedMemory]
    total_retrieved: int
    retrieval_latency_ms: int = 0


class QueryRequest(BaseModel):
    """Request for /query — ask the world model directly."""
    session_id: UUID
    query: str = Field(..., min_length=1, max_length=5000)
    max_results: int = Field(default=10, ge=1, le=100)


class QueryResponse(BaseModel):
    """Response for /query — direct world model answer."""
    session_id: UUID
    query: str
    answer: str
    supporting_memories: list[RetrievedMemory] = []
    retrieval_latency_ms: int = 0
