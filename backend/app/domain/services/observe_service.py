"""
Observation & Agent Turn Service — orchestrates the complete 8-step execution flow:
User Message -> Memory Compiler -> Embedding Generation -> Knowledge Graph Update -> Hybrid Retrieval -> Context Compiler -> LLM Provider -> Assistant Response -> Persistence -> WebSocket Events
"""
from __future__ import annotations

import time
from uuid import UUID
import structlog

from app.core.exceptions import SessionNotFoundError
from app.core.redis import redis_manager
from app.core.security import sanitize_input
from app.core.socket import EventType, event_emitter
from app.domain.entities.models import ContextBundle, Entity, EntityType, Episode, Fact, Relationship, RelationType
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.episode_repo import EpisodeRepository
from app.domain.repositories.fact_repo import FactRepository
from app.domain.repositories.metrics_repo import ContradictionLogRepository, ContextBundleRepository, MetricsRepository
from app.domain.repositories.relationship_repo import RelationshipRepository
from app.domain.repositories.session_repo import SessionRepository
from app.llm.base import LLMProvider
from app.memory.compiler.embeddings import generate_embedding
from app.memory.compiler.pipeline import MemoryCompilerPipeline
from app.memory.compiler.types import PipelineInput
from app.memory.context.compiler import ContextCompiler
from app.memory.graph.contradiction import ContradictionEngine
from app.memory.retrieval.engine import HybridRetrievalEngine
from app.schemas.entity import EntityResponse
from app.schemas.fact import FactResponse
from app.schemas.observe import CompilerResult, ObserveRequest, ObserveResponse
from app.schemas.relationship import RelationshipResponse

log = structlog.get_logger(__name__)


class ObserveService:
    def __init__(
        self,
        session_repo: SessionRepository,
        entity_repo: EntityRepository,
        fact_repo: FactRepository,
        episode_repo: EpisodeRepository,
        rel_repo: RelationshipRepository,
        metrics_repo: MetricsRepository,
        contradiction_repo: ContradictionLogRepository,
        bundle_repo: ContextBundleRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self.session_repo = session_repo
        self.entity_repo = entity_repo
        self.fact_repo = fact_repo
        self.episode_repo = episode_repo
        self.rel_repo = rel_repo
        self.metrics_repo = metrics_repo
        self.bundle_repo = bundle_repo
        self.llm_provider = llm_provider
        self.compiler_pipeline = MemoryCompilerPipeline(llm_provider)
        self.contradiction_engine = ContradictionEngine(fact_repo, contradiction_repo)
        self.retrieval_engine = HybridRetrievalEngine(fact_repo, episode_repo)
        self.context_compiler = ContextCompiler(self.retrieval_engine)

    async def observe(self, req: ObserveRequest, token_budget: int = 1500) -> ObserveResponse:
        start_t = time.perf_counter()
        session = await self.session_repo.get_by_id(req.session_id)
        if not session:
            raise SessionNotFoundError(f"Session '{req.session_id}' not found.")

        # 1. User Message Input Sanitization
        clean_text = sanitize_input(req.text)
        turn_number = await self.session_repo.increment_turn(req.session_id)

        # 2. Memory Compiler Pipeline Execution
        pipe_input = PipelineInput(session_id=req.session_id, raw_text=clean_text)
        compiled_ctx = await self.compiler_pipeline.execute(pipe_input)

        saved_entities: list[EntityResponse] = []
        saved_facts: list[FactResponse] = []
        saved_rels: list[RelationshipResponse] = []
        contradictions_count = 0
        entity_map: dict[str, UUID] = {}

        # 3. Knowledge Graph Update & Embedding Generation
        # A. Entities
        for ent_data in compiled_ctx.entities:
            existing = await self.entity_repo.find_by_name(req.session_id, ent_data.name)
            if existing:
                entity_map[ent_data.name.lower()] = existing.id
                saved_entities.append(EntityResponse.model_validate(existing))
            else:
                try:
                    e_type = EntityType(ent_data.entity_type.lower())
                except ValueError:
                    e_type = EntityType.CONCEPT

                ent_vec = await generate_embedding(ent_data.name)
                new_entity = Entity(
                    session_id=req.session_id,
                    name=ent_data.name,
                    entity_type=e_type,
                    importance=ent_data.importance,
                    embedding=ent_vec,
                )
                created_e = await self.entity_repo.create(new_entity)
                entity_map[ent_data.name.lower()] = created_e.id

                for alias in ent_data.aliases:
                    await self.entity_repo.add_alias(created_e.id, alias)

                await event_emitter.emit_entity_created(
                    str(req.session_id), str(created_e.id), created_e.name, created_e.entity_type.value
                )
                saved_entities.append(EntityResponse.model_validate(created_e))

        # B. Facts & Contradiction Resolution with Embeddings
        for fact_data in compiled_ctx.facts:
            ent_id = entity_map.get(fact_data.entity_name.lower()) if fact_data.entity_name else None
            fact_vec = await generate_embedding(fact_data.statement)

            new_fact = Fact(
                session_id=req.session_id,
                entity_id=ent_id,
                statement=fact_data.statement,
                importance=fact_data.importance,
                source_text=fact_data.source_text,
                embedding=fact_vec,
            )
            created_f = await self.fact_repo.create(new_fact)

            if ent_id:
                had_conflict = await self.contradiction_engine.check_and_resolve(
                    req.session_id, ent_id, fact_data.statement, created_f.id, new_fact_vec=fact_vec
                )
                if had_conflict:
                    contradictions_count += 1

            await event_emitter.emit_fact_added(
                str(req.session_id), str(created_f.id), created_f.statement, fact_data.entity_name or "General"
            )
            saved_facts.append(FactResponse.model_validate(created_f))

        # C. Relationships
        for rel_data in compiled_ctx.relationships:
            src_id = entity_map.get(rel_data.source.lower())
            tgt_id = entity_map.get(rel_data.target.lower())
            if src_id and tgt_id:
                try:
                    r_type = RelationType(rel_data.relation_type.lower())
                except ValueError:
                    r_type = RelationType.RELATED_TO

                new_rel = Relationship(
                    session_id=req.session_id,
                    source_entity_id=src_id,
                    target_entity_id=tgt_id,
                    relation_type=r_type,
                    confidence=rel_data.confidence,
                )
                created_r = await self.rel_repo.create(new_rel)
                await event_emitter.emit_relationship_created(
                    str(req.session_id), str(created_r.id), rel_data.source, rel_data.target, r_type.value
                )
                saved_rels.append(RelationshipResponse.model_validate(created_r))

        # D. Episode Log with Embedding
        if compiled_ctx.episode_summary:
            ep_vec = await generate_embedding(compiled_ctx.episode_summary)
            ep = Episode(
                session_id=req.session_id,
                summary=compiled_ctx.episode_summary,
                level=0,
                turn_number=turn_number,
                embedding=ep_vec,
            )
            await self.episode_repo.create(ep)

        # Invalidate working memory cache
        await redis_manager.invalidate_working_memory(str(req.session_id))
        compiler_ms = int((time.perf_counter() - start_t) * 1000)

        # 4 & 5. Hybrid Retrieval & Context Compiler
        context_bundle = await self.context_compiler.compile_context(
            session_id=req.session_id,
            query=clean_text,
            token_budget=token_budget,
            turn_number=turn_number,
        )

        # 6. LLM Provider Execution
        system_prompt = (
            "You are Engram, an intelligent assistant powered by a live, structured World Model.\n"
            "Answer the user's message concisely using the provided context bundle.\n\n"
            f"{context_bundle.context_text}"
        )

        await event_emitter.emit(
            EventType.PROMPT_GENERATED,
            str(req.session_id),
            {"token_count": context_bundle.token_count, "context": context_bundle.context_text[:200]},
        )

        llm_res = await self.llm_provider.complete(
            messages=[{"role": "user", "content": clean_text}],
            system=system_prompt,
            temperature=0.3,
        )

        assistant_reply = llm_res.content

        await event_emitter.emit(
            EventType.LLM_RESPONSE_RECEIVED,
            str(req.session_id),
            {"response": assistant_reply[:200], "prompt_tokens": llm_res.prompt_tokens},
        )

        # 7. Persist Response Snapshot
        bundle_record = ContextBundle(
            session_id=req.session_id,
            turn_number=turn_number,
            token_count=context_bundle.token_count,
            bundle_json=context_bundle.model_dump(mode="json"),
            latency_ms=int((time.perf_counter() - start_t) * 1000),
        )
        await self.bundle_repo.create(bundle_record)

        # Record Metrics
        total_ms = int((time.perf_counter() - start_t) * 1000)
        await self.metrics_repo.record(req.session_id, "turn_latency_ms", float(total_ms), turn_number=turn_number)
        await self.metrics_repo.record(req.session_id, "context_tokens", float(context_bundle.token_count), turn_number=turn_number)

        compiler_res = CompilerResult(
            entities=saved_entities,
            facts=saved_facts,
            relationships=saved_rels,
            episode_summary=compiled_ctx.episode_summary,
            contradictions_detected=contradictions_count,
            compiler_latency_ms=compiler_ms,
        )

        # 8. Return response payload
        return ObserveResponse(
            session_id=req.session_id,
            turn_number=turn_number,
            compiler_result=compiler_res,
            reply=assistant_reply,
            timestamp=session.updated_at,
        )
