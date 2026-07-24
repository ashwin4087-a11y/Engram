"""
Types and Context data structures for Memory Compiler pipeline.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID
from pydantic import BaseModel


class PipelineInput(BaseModel):
    session_id: UUID
    raw_text: str
    metadata: dict[str, Any] | None = None


class ExtractedEntityData(BaseModel):
    name: str
    entity_type: str
    importance: float = 0.5
    confidence: float = 1.0
    aliases: list[str] = []


class ExtractedFactData(BaseModel):
    entity_name: str | None = None
    statement: str
    importance: float = 0.5
    confidence: float = 1.0
    source_text: str | None = None


class ExtractedRelationshipData(BaseModel):
    source: str
    target: str
    relation_type: str
    confidence: float = 1.0
    source_text: str | None = None


class PipelineContext(BaseModel):
    session_id: UUID
    raw_text: str
    normalized_text: str = ""
    entities: list[ExtractedEntityData] = []
    facts: list[ExtractedFactData] = []
    relationships: list[ExtractedRelationshipData] = []
    preferences: list[str] = []
    tasks: list[str] = []
    episode_summary: str = ""
    contradictions: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    embeddings: dict[str, list[float]] = {}  # key -> vector
