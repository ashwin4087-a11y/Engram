"""
FastAPI dependency injection module.
Injects repositories, services, DB session, and LLM provider into thin routes.
"""
from __future__ import annotations

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.domain.repositories.metrics_repo import ContradictionLogRepository, ContextBundleRepository, MetricsRepository
from app.domain.repositories.relationship_repo import RelationshipRepository
from app.domain.repositories.session_repo import SessionRepository
from app.domain.services.observe_service import ObserveService
from app.llm.factory import get_llm_provider
from app.memory.context.compiler import ContextCompiler
from app.memory.graph.engine import KnowledgeGraphEngine
from app.memory.retrieval.engine import HybridRetrievalEngine


def get_session_repo(db: AsyncSession = Depends(get_db_session)) -> SessionRepository:
    return SessionRepository(db)


def get_entity_repo(db: AsyncSession = Depends(get_db_session)) -> EntityRepository:
    return EntityRepository(db)


def get_fact_repo(db: AsyncSession = Depends(get_db_session)) -> FactRepository:
    return FactRepository(db)


def get_episode_repo(db: AsyncSession = Depends(get_db_session)) -> EpisodeRepository:
    return EpisodeRepository(db)


def get_rel_repo(db: AsyncSession = Depends(get_db_session)) -> RelationshipRepository:
    return RelationshipRepository(db)


def get_metrics_repo(db: AsyncSession = Depends(get_db_session)) -> MetricsRepository:
    return MetricsRepository(db)


def get_contradiction_repo(db: AsyncSession = Depends(get_db_session)) -> ContradictionLogRepository:
    return ContradictionLogRepository(db)


def get_bundle_repo(db: AsyncSession = Depends(get_db_session)) -> ContextBundleRepository:
    return ContextBundleRepository(db)


def get_observe_service(
    session_repo: SessionRepository = Depends(get_session_repo),
    entity_repo: EntityRepository = Depends(get_entity_repo),
    fact_repo: FactRepository = Depends(get_fact_repo),
    episode_repo: EpisodeRepository = Depends(get_episode_repo),
    rel_repo: RelationshipRepository = Depends(get_rel_repo),
    metrics_repo: MetricsRepository = Depends(get_metrics_repo),
    contradiction_repo: ContradictionLogRepository = Depends(get_contradiction_repo),
    bundle_repo: ContextBundleRepository = Depends(get_bundle_repo),
) -> ObserveService:
    llm = get_llm_provider()
    return ObserveService(
        session_repo=session_repo,
        entity_repo=entity_repo,
        fact_repo=fact_repo,
        episode_repo=episode_repo,
        rel_repo=rel_repo,
        metrics_repo=metrics_repo,
        contradiction_repo=contradiction_repo,
        bundle_repo=bundle_repo,
        llm_provider=llm,
    )


def get_graph_engine(
    entity_repo: EntityRepository = Depends(get_entity_repo),
    rel_repo: RelationshipRepository = Depends(get_rel_repo),
) -> KnowledgeGraphEngine:
    return KnowledgeGraphEngine(entity_repo=entity_repo, relationship_repo=rel_repo)


def get_retrieval_engine(
    fact_repo: FactRepository = Depends(get_fact_repo),
    episode_repo: EpisodeRepository = Depends(get_episode_repo),
) -> HybridRetrievalEngine:
    return HybridRetrievalEngine(fact_repo=fact_repo, episode_repo=episode_repo)


def get_context_compiler(
    retrieval_engine: HybridRetrievalEngine = Depends(get_retrieval_engine),
) -> ContextCompiler:
    return ContextCompiler(retrieval_engine=retrieval_engine)
