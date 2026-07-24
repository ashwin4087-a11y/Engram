"""Fact repository — CRUD, vector similarity, contradiction queries."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update

from app.domain.entities.models import Entity, Fact, FactStatus
from app.domain.repositories.base import BaseRepository


class FactRepository(BaseRepository[Fact]):
    model = Fact

    async def get_by_session(
        self,
        session_id: UUID,
        *,
        active_only: bool = True,
        limit: int = 100,
    ) -> Sequence[Fact]:
        """Fetch facts for a session."""
        stmt = select(Fact).where(Fact.session_id == session_id)
        if active_only:
            stmt = stmt.where(Fact.status == FactStatus.ACTIVE)
        stmt = stmt.order_by(Fact.importance.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_entity(
        self, entity_id: UUID, active_only: bool = True,
    ) -> Sequence[Fact]:
        """Fetch all facts associated with a specific entity."""
        stmt = select(Fact).where(Fact.entity_id == entity_id)
        if active_only:
            stmt = stmt.where(Fact.status == FactStatus.ACTIVE)
        stmt = stmt.order_by(Fact.importance.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def search_by_embedding(
        self,
        session_id: UUID,
        embedding: list[float],
        *,
        limit: int = 20,
        active_only: bool = True,
    ) -> Sequence[tuple[Fact, float]]:
        """
        Vector similarity search over fact embeddings.
        Returns (fact, distance) tuples ordered by cosine similarity.
        """
        stmt = select(
            Fact,
            Fact.embedding.cosine_distance(embedding).label("distance"),
        ).where(
            and_(
                Fact.session_id == session_id,
                Fact.embedding.isnot(None),
            )
        )
        if active_only:
            stmt = stmt.where(Fact.status == FactStatus.ACTIVE)
        stmt = stmt.order_by("distance").limit(limit)
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def find_similar(
        self,
        session_id: UUID,
        embedding: list[float],
        threshold: float = 0.15,
    ) -> Sequence[tuple[Fact, float]]:
        """
        Find facts similar to a given embedding within a distance threshold.
        Used for duplicate detection.
        """
        stmt = (
            select(
                Fact,
                Fact.embedding.cosine_distance(embedding).label("distance"),
            )
            .where(
                and_(
                    Fact.session_id == session_id,
                    Fact.status == FactStatus.ACTIVE,
                    Fact.embedding.isnot(None),
                )
            )
            .having(
                Fact.embedding.cosine_distance(embedding) < threshold,
            )
            .order_by("distance")
            .limit(10)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def supersede(self, old_fact_id: UUID, new_fact_id: UUID) -> None:
        """Mark a fact as superseded by another (contradiction resolution)."""
        await self.update_fields(
            old_fact_id,
            status=FactStatus.SUPERSEDED,
            superseded_by_id=new_fact_id,
        )

    async def increment_access(self, fact_id: UUID) -> None:
        from app.utils.time import utcnow
        await self.update_fields(fact_id, access_count=Fact.access_count + 1)

    async def count_by_session(
        self, session_id: UUID, active_only: bool = True,
    ) -> int:
        stmt = select(func.count()).select_from(Fact).where(
            Fact.session_id == session_id,
        )
        if active_only:
            stmt = stmt.where(Fact.status == FactStatus.ACTIVE)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_superseded(self, session_id: UUID) -> int:
        """Count contradictions resolved in a session."""
        stmt = (
            select(func.count())
            .select_from(Fact)
            .where(
                and_(
                    Fact.session_id == session_id,
                    Fact.status == FactStatus.SUPERSEDED,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
