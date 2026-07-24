"""
Stage 7: Importance Scorer stage.
Uses heuristics or LLM evaluation to score the importance of extracted entities/facts.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext


class ImportanceScorerStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        # Default fallback is 0.5; this stage can use LLM to adjust scores
        # We assume entity_extractor already gave initial scores; we can normalize them here.
        for e in context.entities:
            e.importance = max(0.1, min(1.0, e.importance))
        for f in context.facts:
            f.importance = max(0.1, min(1.0, f.importance))
        return context
