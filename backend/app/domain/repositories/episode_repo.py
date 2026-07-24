"""Episode repository — CRUD, hierarchical queries, decay updates."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update

from app.domain.entities.models import Episode
from app.domain.repositories.base import BaseRepository


class EpisodeRepository(BaseRepository[Episode]):
    model = Episode

    async def get_by_session(
        self,
        session_id: UUID,
        *,
        active_only: bool = True,
        level: int | None = None,
        limit: int = 100,
    ) -> Sequence[Episode]:
        """Fetch episodes for a session, optionally filtered by level."""
        stmt = select(Episode).where(Episode.session_id == session_id)
        if active_only:
            stmt = stmt.where(Episode.is_active.is_(True))
        if level is not None:
            stmt = stmt.where(Episode.level == level)
        stmt = stmt.order_by(Episode.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_raw_undecayed(
        self, session_id: UUID, min_count: int = 3,
    ) -> Sequence[Episode]:
        """
        Fetch raw (level=0) active episodes eligible for consolidation.
        Returns episodes only if there are at least min_count of them.
        """
        stmt = (
            select(Episode)
            .where(
                and_(
                    Episode.session_id == session_id,
                    Episode.level == 0,
                    Episode.is_active.is_(True),
                )
            )
            .order_by(Episode.created_at.asc())
        )
        result = await self._session.execute(stmt)
        episodes = list(result.scalars().all())
        return episodes if len(episodes) >= min_count else []

    async def deactivate_many(self, episode_ids: list[UUID]) -> None:
        """Mark multiple episodes as inactive (decayed)."""
        if not episode_ids:
            return
        stmt = (
            update(Episode)
            .where(Episode.id.in_(episode_ids))
            .values(is_active=False)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def search_by_embedding(
        self,
        session_id: UUID,
        embedding: list[float],
        *,
        limit: int = 10,
        active_only: bool = True,
    ) -> Sequence[tuple[Episode, float]]:
        """Vector similarity search over episode embeddings."""
        stmt = select(
            Episode,
            Episode.embedding.cosine_distance(embedding).label("distance"),
        ).where(
            and_(
                Episode.session_id == session_id,
                Episode.embedding.isnot(None),
            )
        )
        if active_only:
            stmt = stmt.where(Episode.is_active.is_(True))
        stmt = stmt.order_by("distance").limit(limit)
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def count_by_session(
        self, session_id: UUID, active_only: bool = True,
    ) -> int:
        stmt = select(func.count()).select_from(Episode).where(
            Episode.session_id == session_id,
        )
        if active_only:
            stmt = stmt.where(Episode.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalar_one()
