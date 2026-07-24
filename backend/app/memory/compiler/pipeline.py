"""
Pipeline orchestrator and stage implementations for Memory Compiler.
Isolated stages:
Normalizer -> EntityExtraction -> FactExtraction -> RelationshipExtraction -> PreferenceDetector -> ImportanceScorer -> ConfidenceEstimator -> DuplicateDetector -> ContradictionDetector -> EmbeddingGenerator
"""
from __future__ import annotations

import structlog

from app.core.socket import event_emitter
from app.llm.base import LLMProvider
from app.memory.compiler.stages.confidence_estimator import ConfidenceEstimatorStage
from app.memory.compiler.stages.contradiction_detector import ContradictionDetectorStage
from app.memory.compiler.stages.duplicate_detector import DuplicateDetectorStage
from app.memory.compiler.stages.embedding_generator import EmbeddingGeneratorStage
from app.memory.compiler.stages.entity_extractor import EntityExtractionStage
from app.memory.compiler.stages.fact_extractor import FactExtractionStage
from app.memory.compiler.stages.importance_scorer import ImportanceScorerStage
from app.memory.compiler.stages.normalizer import NormalizerStage
from app.memory.compiler.stages.preference_detector import PreferenceDetectorStage
from app.memory.compiler.stages.relationship_extractor import RelationshipExtractionStage
from app.memory.compiler.types import PipelineContext, PipelineInput

log = structlog.get_logger(__name__)


class MemoryCompilerPipeline:
    """Orchestrates all extraction stages sequentially."""

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm = llm_provider
        self.stages = [
            NormalizerStage(),
            EntityExtractionStage(),
            FactExtractionStage(),
            RelationshipExtractionStage(),
            PreferenceDetectorStage(),
            ImportanceScorerStage(),
            ConfidenceEstimatorStage(),
            DuplicateDetectorStage(),
            ContradictionDetectorStage(),
            EmbeddingGeneratorStage(),
        ]

    async def execute(self, input_data: PipelineInput) -> PipelineContext:
        log.info("compiler.pipeline.start", session_id=str(input_data.session_id))
        context = PipelineContext(session_id=input_data.session_id, raw_text=input_data.raw_text)

        for stage in self.stages:
            stage_name = stage.__class__.__name__
            await event_emitter.emit_compiler_stage(str(input_data.session_id), stage_name, finished=False)
            context = await stage.process(context, self.llm)
            await event_emitter.emit_compiler_stage(str(input_data.session_id), stage_name, finished=True)

        log.info(
            "compiler.pipeline.complete",
            session_id=str(input_data.session_id),
            entities=len(context.entities),
            facts=len(context.facts),
            relationships=len(context.relationships),
        )
        return context
