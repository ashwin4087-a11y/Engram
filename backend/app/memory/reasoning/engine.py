"""
Agent Reasoning Engine — orchestrates multi-turn reasoning steps using context bundles.
"""
from __future__ import annotations

import time
from uuid import UUID
import structlog

from app.llm.base import LLMProvider
from app.memory.context.compiler import ContextCompiler
from app.schemas.context import ReasonRequest, ReasonResponse

log = structlog.get_logger(__name__)


class ReasoningEngine:
    def __init__(self, context_compiler: ContextCompiler, llm: LLMProvider) -> None:
        self.context_compiler = context_compiler
        self.llm = llm

    async def execute_turn(self, req: ReasonRequest) -> ReasonResponse:
        start_t = time.perf_counter()
        bundle = await self.context_compiler.compile_context(
            req.session_id, req.query, token_budget=req.token_budget
        )

        system_prompt = (
            "You are an AI assistant powered by Engram memory substrate.\n"
            f"Context Bundle:\n{bundle.context_text}"
        )
        res = await self.llm.complete(
            messages=[{"role": "user", "content": req.query}],
            system=system_prompt,
        )

        elapsed_ms = int((time.perf_counter() - start_t) * 1000)
        return ReasonResponse(
            session_id=req.session_id,
            response=res.content,
            context_token_count=bundle.token_count,
            total_latency_ms=elapsed_ms,
            memories_used=len(bundle.memories),
        )
