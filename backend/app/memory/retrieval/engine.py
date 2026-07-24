"""
Hybrid Retrieval Engine — combines:
1. Vector similarity (pgvector cosine distance via search_by_embedding)
2. Recency score (time decay)
3. Importance score
4. Confidence score

Calculates a final composite quality score for each memory.
"""
from __future__ import annotations

import time
from uuid import UUID
import structlog

from app.core.config import settings
from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.memory.compiler.embeddings import generate_embedding
from app.schemas.memory import MemoryResponse, RetrievedMemory
from app.utils.time import recency_score

log = structlog.get_logger(__name__)


class HybridRetrievalEngine:
    def __init__(
        self,
        fact_repo: FactRepository,
        episode_repo: EpisodeRepository,
    ) -> None:
        self.fact_repo = fact_repo
        self.episode_repo = episode_repo

    async def retrieve(
        self,
        session_id: UUID,
        query: str,
        query_embedding: list[float] | None = None,
        top_k: int = 15,
    ) -> MemoryResponse:
        start_t = time.perf_counter()
        memories: list[RetrievedMemory] = []

        # Generate query vector embedding if not provided
        if not query_embedding and query.strip():
            query_embedding = await generate_embedding(query)

        # 1. Vector Search on Facts
        if query_embedding:
            similar_facts = await self.fact_repo.search_by_embedding(
                session_id, query_embedding, limit=30, active_only=True
            )
            for fact, dist in similar_facts:
                sim_s = max(0.0, 1.0 - float(dist)) if dist is not None else 0.5
                rec_s = recency_score(fact.created_at)
                imp_s = fact.importance
                conf_s = fact.confidence

                composite_score = (
                    (settings.RETRIEVAL_WEIGHT_SIMILARITY * sim_s)
                    + (settings.RETRIEVAL_WEIGHT_RECENCY * rec_s)
                    + (settings.RETRIEVAL_WEIGHT_IMPORTANCE * imp_s)
                    + (settings.RETRIEVAL_WEIGHT_CONFIDENCE * conf_s)
                )

                memories.append(
                    RetrievedMemory(
                        memory_type="fact",
                        content=fact.statement,
                        score=round(composite_score, 4),
                        source_id=fact.id,
                        similarity_score=round(sim_s, 4),
                        recency_score=round(rec_s, 4),
                        importance_score=imp_s,
                        confidence_score=conf_s,
                    )
                )

        # Fallback to general fact query if vector list is empty
        if not memories:
            facts = await self.fact_repo.get_by_session(session_id, active_only=True, limit=30)
            for f in facts:
                rec_s = recency_score(f.created_at)
                composite_score = (
                    (settings.RETRIEVAL_WEIGHT_SIMILARITY * 0.5)
                    + (settings.RETRIEVAL_WEIGHT_RECENCY * rec_s)
                    + (settings.RETRIEVAL_WEIGHT_IMPORTANCE * f.importance)
                    + (settings.RETRIEVAL_WEIGHT_CONFIDENCE * f.confidence)
                )
                memories.append(
                    RetrievedMemory(
                        memory_type="fact",
                        content=f.statement,
                        score=round(composite_score, 4),
                        source_id=f.id,
                        similarity_score=0.5,
                        recency_score=round(rec_s, 4),
                        importance_score=f.importance,
                        confidence_score=f.confidence,
                    )
                )

        # 2. Vector Search on Episodes
        if query_embedding:
            similar_episodes = await self.episode_repo.search_by_embedding(
                session_id, query_embedding, limit=15, active_only=True
            )
            for ep, dist in similar_episodes:
                sim_s = max(0.0, 1.0 - float(dist)) if dist is not None else 0.4
                rec_s = recency_score(ep.created_at)
                composite_score = (
                    (settings.RETRIEVAL_WEIGHT_SIMILARITY * sim_s)
                    + (settings.RETRIEVAL_WEIGHT_RECENCY * rec_s)
                    + (settings.RETRIEVAL_WEIGHT_IMPORTANCE * ep.importance)
                    + (settings.RETRIEVAL_WEIGHT_CONFIDENCE * ep.confidence)
                )
                memories.append(
                    RetrievedMemory(
                        memory_type="episode",
                        content=f"[Episode L{ep.level}] {ep.summary}",
                        score=round(composite_score, 4),
                        source_id=ep.id,
                        similarity_score=round(sim_s, 4),
                        recency_score=round(rec_s, 4),
                        importance_score=ep.importance,
                        confidence_score=ep.confidence,
                    )
                )

        # Sort by composite quality score
        memories.sort(key=lambda m: m.score, reverse=True)
        top_memories = memories[:top_k]

        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        log.info("retrieval.complete", session_id=str(session_id), returned=len(top_memories), latency_ms=elapsed_ms)

        return MemoryResponse(
            session_id=session_id,
            query=query,
            memories=top_memories,
            total_retrieved=len(top_memories),
            retrieval_latency_ms=elapsed_ms,
        )
