"""
Stage 3: Fact Extractor stage.
Extracts atomic factual statements from user input.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import ExtractedFactData, PipelineContext


class FactExtractionStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        schema = {
            "type": "object",
            "properties": {
                "facts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity_name": {"type": "string"},
                            "statement": {"type": "string"},
                            "importance": {"type": "number"},
                        },
                        "required": ["statement"],
                    },
                },
                "episode_summary": {"type": "string"},
            },
            "required": ["facts", "episode_summary"],
        }
        res = await llm.extract_structured(
            text=context.normalized_text,
            schema=schema,
            system="Extract atomic facts and a concise 1-sentence episode summary.",
        )
        for f in res.get("facts", []):
            context.facts.append(
                ExtractedFactData(
                    entity_name=f.get("entity_name"),
                    statement=f["statement"],
                    importance=float(f.get("importance", 0.5)),
                    source_text=context.normalized_text[:200],
                )
            )
        context.episode_summary = res.get("episode_summary", f"Observation: {context.normalized_text[:80]}")
        return context
