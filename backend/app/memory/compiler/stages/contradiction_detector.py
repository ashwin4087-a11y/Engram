"""
Stage 10: Contradiction Detector stage.
Flags internal contradictions within the *current* user input.
(Historical contradiction resolution is handled later in the pipeline by ContradictionEngine).
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext


class ContradictionDetectorStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        # Internal contradictions (e.g. "I live in Berlin and I live in Paris") are rare in a single turn,
        # but we could add an LLM pass here. For now, we rely on the ContradictionEngine against the historical DB.
        return context
