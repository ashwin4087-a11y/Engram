"""
Stage 4: Relationship Extractor stage.
Extracts directed typed graph edges between entities.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import ExtractedRelationshipData, PipelineContext


class RelationshipExtractionStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        schema = {
            "type": "object",
            "properties": {
                "relationships": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "source": {"type": "string"},
                            "target": {"type": "string"},
                            "relation_type": {"type": "string"},
                            "confidence": {"type": "number"},
                        },
                        "required": ["source", "target", "relation_type"],
                    },
                }
            },
            "required": ["relationships"],
        }
        res = await llm.extract_structured(
            text=context.normalized_text,
            schema=schema,
            system="Extract relationships between entities (e.g. located_in, works_on, prefers, uses).",
        )
        for r in res.get("relationships", []):
            context.relationships.append(
                ExtractedRelationshipData(
                    source=r["source"],
                    target=r["target"],
                    relation_type=r["relation_type"],
                    confidence=float(r.get("confidence", 1.0)),
                    source_text=context.normalized_text[:200],
                )
            )
        return context
