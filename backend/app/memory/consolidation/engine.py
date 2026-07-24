"""
Memory Consolidation Engine — compresses raw Level 0 episodes into Level 1 summaries,
decays old episodes and entity importance based on half-life decay curves,
and fires real-time consolidation events.
Never permanently deletes memory (marks inactive instead).
"""
from __future__ import annotations

from uuid import UUID
import structlog

from app.core.config import settings
from app.core.socket import event_emitter
from app.domain.entities.models import Episode
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.episode_repo import EpisodeRepository
from app.llm.base import LLMProvider
from app.utils.time import decay_factor

log = structlog.get_logger(__name__)


class ConsolidationEngine:
    def __init__(
        self,
        episode_repo: EpisodeRepository,
        entity_repo: EntityRepository | None = None,
        llm: LLMProvider | None = None,
    ) -> None:
        self.episode_repo = episode_repo
        self.entity_repo = entity_repo
        self.llm = llm

    async def consolidate_session(self, session_id: UUID, min_episodes: int = 2) -> dict[str, str | int]:
        """Compress raw level-0 episodes into higher-level consolidated summaries."""
        raw_episodes = await self.episode_repo.get_raw_undecayed(session_id, min_count=min_episodes)
        if not raw_episodes:
            return {"status": "skipped", "message": "Not enough raw episodes to consolidate."}

        await event_emitter.emit_consolidation_started(str(session_id), len(raw_episodes))

        episodes_text = "\n".join([f"- {ep.summary}" for ep in raw_episodes])
        consolidated_summary = f"Consolidated summary of {len(raw_episodes)} observations."

        if self.llm:
            sys_prompt = "You are an AI Memory Consolidation Engine. Compress raw episodic observations into a concise, unified summary capturing core facts."
            schema = {
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            }
            extracted = await self.llm.extract_structured(episodes_text, schema, system=sys_prompt)
            consolidated_summary = extracted.get("summary", consolidated_summary)

        parent_ids = [ep.id for ep in raw_episodes]
        parent_episode = Episode(
            session_id=session_id,
            summary=consolidated_summary,
            level=1,
            parent_episode_ids=parent_ids,
            is_active=True,
        )

        created_parent = await self.episode_repo.create(parent_episode)
        await self.episode_repo.deactivate_many(parent_ids)

        # Decay Entity Importance Scores
        if self.entity_repo:
            entities = await self.entity_repo.get_by_session(session_id, active_only=True)
            for ent in entities:
                factor = decay_factor(ent.created_at, half_life_days=settings.DECAY_HALF_LIFE_DAYS)
                new_importance = max(0.1, round(ent.importance * factor, 4))
                await self.entity_repo.update_fields(ent.id, importance=new_importance)

        await event_emitter.emit_consolidation_finished(
            str(session_id), len(raw_episodes), consolidated_summary
        )

        log.info("consolidation.complete", session_id=str(session_id), count=len(raw_episodes))
        return {
            "status": "success",
            "merged_count": len(raw_episodes),
            "parent_id": str(created_parent.id),
            "summary": consolidated_summary,
        }
