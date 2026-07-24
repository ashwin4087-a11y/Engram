"""
Query Service — "Ask the World Model" direct query console.
Bypasses the agent turn runtime to query knowledge graph facts and vector embeddings directly.
"""
from __future__ import annotations

import time
from uuid import UUID
import structlog

from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.llm.base import LLMProvider
from app.memory.retrieval.engine import HybridRetrievalEngine
from app.schemas.memory import QueryRequest, QueryResponse

log = structlog.get_logger(__name__)


class QueryService:
    def __init__(
        self,
        fact_repo: FactRepository,
        episode_repo: EpisodeRepository,
        llm: LLMProvider,
    ) -> None:
        self.retrieval_engine = HybridRetrievalEngine(fact_repo, episode_repo)
        self.llm = llm

    async def query_world_model(self, req: QueryRequest) -> QueryResponse:
        start_t = time.perf_counter()
        retrieval_res = await self.retrieval_engine.retrieve(
            req.session_id, req.query, top_k=req.max_results
        )

        facts_text = "\n".join([f"- {m.content} (score: {m.score})" for m in retrieval_res.memories])
        sys_prompt = f"You are a World Model direct query interface. Synthesize a direct factual answer using strictly the following stored facts:\n\n{facts_text}"

        llm_res = await self.llm.complete(
            messages=[{"role": "user", "content": req.query}],
            system=sys_prompt,
            temperature=0.0,
        )

        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        return QueryResponse(
            session_id=req.session_id,
            query=req.query,
            answer=llm_res.content,
            supporting_memories=retrieval_res.memories,
            retrieval_latency_ms=elapsed_ms,
        )
