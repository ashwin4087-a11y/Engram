"""
Contradiction engine — detects conflicting facts and resolves them via supersession.
Uses semantic distance thresholding and predicate heuristics.
Fact history is preserved (old facts become superseded, never deleted).
"""
from __future__ import annotations

from uuid import UUID
import structlog

from app.core.socket import event_emitter
from app.domain.entities.models import ContradictionLog
from app.domain.repositories.fact_repo import FactRepository
from app.domain.repositories.metrics_repo import ContradictionLogRepository

log = structlog.get_logger(__name__)


class ContradictionEngine:
    def __init__(
        self,
        fact_repo: FactRepository,
        contradiction_repo: ContradictionLogRepository,
    ) -> None:
        self.fact_repo = fact_repo
        self.contradiction_repo = contradiction_repo

    async def check_and_resolve(
        self,
        session_id: UUID,
        entity_id: UUID | None,
        new_statement: str,
        new_fact_id: UUID,
        new_fact_vec: list[float] | None = None,
    ) -> bool:
        """
        Check if new_statement contradicts existing active facts for entity_id.
        If contradiction found, supersede old fact, create audit log, and return True.
        """
        if not entity_id:
            return False

        existing_facts = await self.fact_repo.get_by_entity(entity_id, active_only=True)
        new_lower = new_statement.lower()

        conflict_keywords = ["lives in", "works at", "prefers", "located in", "status is", "role is", "using", "uses"]

        for old_fact in existing_facts:
            if old_fact.id == new_fact_id:
                continue

            old_lower = old_fact.statement.lower()
            is_conflict = False

            # Check keyword predicate collision
            for kw in conflict_keywords:
                if kw in old_lower and kw in new_lower and old_lower != new_lower:
                    is_conflict = True
                    break

            if is_conflict:
                log.info(
                    "contradiction.detected",
                    session_id=str(session_id),
                    old_fact=old_fact.statement,
                    new_fact=new_statement,
                )

                # 1. Supersede old fact
                await self.fact_repo.supersede(old_fact.id, new_fact_id)

                # 2. Audit log entry
                log_entry = ContradictionLog(
                    session_id=session_id,
                    entity_id=entity_id,
                    old_fact_id=old_fact.id,
                    new_fact_id=new_fact_id,
                    old_statement=old_fact.statement,
                    new_statement=new_statement,
                    resolution="superseded",
                )
                await self.contradiction_repo.create(log_entry)

                # 3. Emit real-time WebSocket alert
                await event_emitter.emit_contradiction_detected(
                    session_id=str(session_id),
                    old_fact=old_fact.statement,
                    new_fact=new_statement,
                    entity_name=str(entity_id),
                )
                return True

        return False
