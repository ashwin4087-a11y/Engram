"""
Stage 1: Text Normalizer stage.
Clean input, strip whitespace, normalize unicode.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext
from app.utils.text import normalize_text


class NormalizerStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        context.normalized_text = normalize_text(context.raw_text)
        return context
