"""
Stage 8: Confidence Estimator stage.
Estimates the certainty of extracted facts based on linguistic hedges (e.g., "might", "probably").
"""
from __future__ import annotations

from app.llm.base import LLMProvider
from app.memory.compiler.types import PipelineContext


class ConfidenceEstimatorStage:
    async def process(self, context: PipelineContext, llm: LLMProvider) -> PipelineContext:
        uncertainty_keywords = ["might", "maybe", "probably", "possibly", "think", "guess"]
        lower_text = context.normalized_text.lower()
        has_uncertainty = any(k in lower_text for k in uncertainty_keywords)
        
        confidence_penalty = 0.5 if has_uncertainty else 0.0

        for f in context.facts:
            f.confidence = max(0.1, f.confidence - confidence_penalty)
        for r in context.relationships:
            r.confidence = max(0.1, r.confidence - confidence_penalty)

        return context
