"""
Stage 2: Entity Extractor stage.
Extracts structured named entities (Person, Org, Location, Project, Task, Tech, etc.).
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import ExtractedEntityData, PipelineContext


class EntityExtractionStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        schema = {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "entity_type": {"type": "string"},
                            "importance": {"type": "number"},
                            "aliases": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "entity_type"],
                    },
                }
            },
            "required": ["entities"],
        }
        res = await llm.extract_structured(
            text=context.normalized_text,
            schema=schema,
            system="Extract all named entities (people, places, tools, projects, concepts).",
        )
        for e in res.get("entities", []):
            context.entities.append(
                ExtractedEntityData(
                    name=e["name"],
                    entity_type=e.get("entity_type", "concept"),
                    importance=float(e.get("importance", 0.5)),
                    aliases=e.get("aliases", []),
                )
            )
        return context
