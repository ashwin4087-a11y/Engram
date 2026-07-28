"""Graph routes."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_graph_engine
from app.memory.graph.engine import KnowledgeGraphEngine
from app.schemas.graph import GraphResponse

router = APIRouter(tags=["Knowledge Graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    session_id: UUID = Query(...),
    graph_engine: KnowledgeGraphEngine = Depends(get_graph_engine),
) -> GraphResponse:
    """Fetch complete knowledge graph formatted for React Flow brain visualizer."""
    return await graph_engine.get_graph(session_id)

