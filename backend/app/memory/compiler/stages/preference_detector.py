"""
Stage 6: Preference Detector stage.
Extracts user preferences, constraints, or goals from the input.
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext


class PreferenceDetectorStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        schema = {
            "type": "object",
            "properties": {
                "preferences": {"type": "array", "items": {"type": "string"}},
                "tasks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["preferences", "tasks"],
        }
        res = await llm.extract_structured(
            text=context.normalized_text,
            schema=schema,
            system="Extract any explicit user preferences, implicit constraints, or active tasks/goals.",
        )
        context.preferences.extend(res.get("preferences", []))
        context.tasks.extend(res.get("tasks", []))
        return context
