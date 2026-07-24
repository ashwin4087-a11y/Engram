"""
Query endpoint route handler — Ask the World Model directly.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.deps import get_fact_repo, get_episode_repo
from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.domain.services.query_service import QueryService
from app.llm.factory import get_llm_provider
from app.schemas.memory import QueryRequest, QueryResponse

router = APIRouter(tags=["World Model Query Console"])


@router.post("/query", response_model=QueryResponse)
async def query_world_model(
    req: QueryRequest,
    fact_repo: FactRepository = Depends(get_fact_repo),
    episode_repo: EpisodeRepository = Depends(get_episode_repo),
) -> QueryResponse:
    """Directly query the World Model without running a full agent turn."""
    llm = get_llm_provider()
    service = QueryService(fact_repo, episode_repo, llm)
    return await service.query_world_model(req)
