"""Graph visualization schemas — maps to React Flow format."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel


class GraphNode(BaseModel):
    """A node in the knowledge graph (React Flow compatible)."""
    id: str
    data: dict[str, Any]
    position: dict[str, float] = {"x": 0.0, "y": 0.0}
    type: str = "default"


class GraphEdge(BaseModel):
    """An edge in the knowledge graph (React Flow compatible)."""
    id: str
    source: str
    target: str
    label: str | None = None
    animated: bool = False
    data: dict[str, Any] | None = None


class GraphResponse(BaseModel):
    """Full graph payload for the frontend brain visualizer."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    entity_count: int = 0
    relationship_count: int = 0
    fact_count: int = 0
