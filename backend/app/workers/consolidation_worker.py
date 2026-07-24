"""
Background workers module — non-blocking async tasks for consolidation, embedding generation, and metrics.
"""
from __future__ import annotations

from uuid import UUID
import structlog

from app.core.database import database_manager
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.episode_repo import EpisodeRepository
from app.llm.factory import get_llm_provider
from app.memory.consolidation.engine import ConsolidationEngine

log = structlog.get_logger(__name__)


async def run_background_consolidation(session_id: UUID) -> None:
    """Async background task for episodic memory consolidation."""
    log.info("worker.consolidation.start", session_id=str(session_id))
    try:
        async with database_manager.session() as db:
            episode_repo = EpisodeRepository(db)
            entity_repo = EntityRepository(db)
            llm = get_llm_provider()
            engine = ConsolidationEngine(episode_repo=episode_repo, entity_repo=entity_repo, llm=llm)
            result = await engine.consolidate_session(session_id, min_episodes=3)
            log.info("worker.consolidation.complete", session_id=str(session_id), result=result)
    except Exception as e:
        log.error("worker.consolidation.failed", session_id=str(session_id), error=str(e))
