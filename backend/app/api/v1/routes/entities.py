"""Entities endpoint route handler."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from uuid import UUID
from typing import List

from app.domain.repositories.entity_repo import EntityRepository
from app.api.v1.deps import get_entity_repo
from app.schemas.entity import EntityResponse

router = APIRouter(tags=["Entities"])

@router.get("/entities", response_model=List[EntityResponse])
async def get_entities(
    session_id: UUID,
    entity_repo: EntityRepository = Depends(get_entity_repo)
) -> List[EntityResponse]:
    """Get all active entities for a session."""
    entities = await entity_repo.get_by_session(session_id, active_only=True)
    return [EntityResponse(
        id=e.id,
        name=e.name,
        entity_type=e.entity_type,
        aliases=e.aliases,
        importance=e.importance,
        confidence=e.confidence,
        access_count=e.access_count
    ) for e in entities]
