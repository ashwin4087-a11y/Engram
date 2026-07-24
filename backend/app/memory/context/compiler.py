"""
Context Budget Compiler — packs highest quality retrieved memories into a tight token budget.
Prompt token count is strictly capped (e.g. 1000, 1500, 2000 tokens).
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from uuid import UUID
import structlog

from app.core.config import settings
from app.core.redis import redis_manager
from app.core.socket import event_emitter
from app.memory.retrieval.engine import HybridRetrievalEngine
from app.schemas.context import ContextBundleResponse
from app.schemas.memory import RetrievedMemory
from app.utils.text import estimate_tokens

log = structlog.get_logger(__name__)


class ContextCompiler:
    def __init__(self, retrieval_engine: HybridRetrievalEngine) -> None:
        self.retrieval_engine = retrieval_engine

    async def compile_context(
        self,
        session_id: UUID,
        query: str,
        token_budget: int = 1500,
        turn_number: int = 1,
    ) -> ContextBundleResponse:
        start_t = time.perf_counter()

        # Check working memory cache in Redis
        cached_bundle = await redis_manager.get_working_memory(str(session_id))
        if cached_bundle and cached_bundle.get("query") == query and cached_bundle.get("token_budget") == token_budget:
            log.info("context.compiler.cache_hit", session_id=str(session_id))
            return ContextBundleResponse(**cached_bundle)

        # 1. Retrieve candidate memories
        retrieval_res = await self.retrieval_engine.retrieve(session_id, query, top_k=25)
        candidates = retrieval_res.memories

        # 2. Greedily pack memories under token budget
        packed_memories: list[RetrievedMemory] = []
        current_tokens = 0
        header_tokens = estimate_tokens("### WORLD MODEL CONTEXT BUNDLE\n")

        current_tokens += header_tokens
        formatted_blocks: list[str] = ["### WORLD MODEL CONTEXT BUNDLE"]

        for mem in candidates:
            block = f"- [{mem.memory_type.upper()}] {mem.content} (score: {mem.score})"
            mem_tokens = estimate_tokens(block)

            if current_tokens + mem_tokens <= token_budget:
                packed_memories.append(mem)
                formatted_blocks.append(block)
                current_tokens += mem_tokens
            else:
                break  # Budget filled

        context_text = "\n".join(formatted_blocks)
        elapsed_ms = int((time.perf_counter() - start_t) * 1000)

        response = ContextBundleResponse(
            session_id=session_id,
            turn_number=turn_number,
            token_count=current_tokens,
            token_budget=token_budget,
            memories=packed_memories,
            context_text=context_text,
            compilation_latency_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc),
        )

        # Cache working memory in Redis
        await redis_manager.set_working_memory(str(session_id), response.model_dump(mode="json"))

        # Emit real-time WebSocket event
        await event_emitter.emit_context_compiled(
            session_id=str(session_id),
            token_count=current_tokens,
            memory_count=len(packed_memories),
        )

        log.info("context.compiler.complete", session_id=str(session_id), tokens=current_tokens, budget=token_budget)
        return response
