"""Graph and Entity routes."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import get_entity_repo, get_graph_engine
from app.domain.repositories.entity_repo import EntityRepository
from app.memory.graph.engine import KnowledgeGraphEngine
from app.schemas.entity import EntityResponse
from app.schemas.graph import GraphResponse

router = APIRouter(tags=["Knowledge Graph"])


@router.get("/graph", response_model=GraphResponse)
async def get_graph(
    session_id: UUID = Query(...),
    graph_engine: KnowledgeGraphEngine = Depends(get_graph_engine),
) -> GraphResponse:
    """Fetch complete knowledge graph formatted for React Flow brain visualizer."""
    return await graph_engine.get_graph(session_id)


@router.get("/entities", response_model=list[EntityResponse])
async def list_entities(
    session_id: UUID = Query(...),
    entity_repo: EntityRepository = Depends(get_entity_repo),
) -> list[EntityResponse]:
    """List all entities for a session."""
    entities = await entity_repo.get_by_session(session_id, active_only=True)
    return [EntityResponse.model_validate(e) for e in entities]
