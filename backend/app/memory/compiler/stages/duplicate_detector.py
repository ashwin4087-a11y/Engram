"""
Stage 9: Duplicate Detector stage.
Removes duplicate facts or entities extracted in the same run.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext
from app.utils.text import normalize_entity_name


class DuplicateDetectorStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        # Deduplicate entities
        unique_entities = {}
        for e in context.entities:
            key = normalize_entity_name(e.name)
            if key not in unique_entities:
                unique_entities[key] = e
            else:
                unique_entities[key].aliases.extend(e.aliases)
        context.entities = list(unique_entities.values())

        # Deduplicate facts
        unique_facts = {}
        for f in context.facts:
            key = f.statement.lower().strip()
            if key not in unique_facts:
                unique_facts[key] = f
        context.facts = list(unique_facts.values())

        return context
