"""Consolidation route handler."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends

from app.api.v1.deps import get_entity_repo, get_episode_repo
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.episode_repo import EpisodeRepository
from app.llm.factory import get_llm_provider
from app.memory.consolidation.engine import ConsolidationEngine

router = APIRouter(tags=["Consolidation Engine"])


@router.post("/consolidate")
async def trigger_consolidation(
    session_id: UUID,
    episode_repo: EpisodeRepository = Depends(get_episode_repo),
    entity_repo: EntityRepository = Depends(get_entity_repo),
) -> dict[str, str | int]:
    """Manually trigger the memory consolidation (sleep cycle) engine."""
    llm = get_llm_provider()
    engine = ConsolidationEngine(episode_repo=episode_repo, entity_repo=entity_repo, llm=llm)
    return await engine.consolidate_session(session_id)
