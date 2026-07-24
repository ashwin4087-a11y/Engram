"""
Stage 5: Embedding Generator stage.
Generates 384-dimensional Sentence Transformer vectors for facts and entities.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.embeddings import generate_embedding
from app.memory.compiler.types import PipelineContext


class EmbeddingGeneratorStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        for f in context.facts:
            vec = await generate_embedding(f.statement)
            context.embeddings[f.statement] = vec
        for e in context.entities:
            vec = await generate_embedding(e.name)
            context.embeddings[e.name] = vec
        return context
