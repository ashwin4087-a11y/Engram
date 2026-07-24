"""Session repository."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update

from app.domain.entities.models import Session
from app.domain.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    model = Session

    async def get_active(self, limit: int = 50) -> Sequence[Session]:
        """Fetch active sessions ordered by most recently updated."""
        stmt = (
            select(Session)
            .where(Session.is_active.is_(True))
            .order_by(Session.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def increment_turn(self, session_id: UUID) -> int:
        """Atomically increment the turn counter and return the new value."""
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(turn_count=Session.turn_count + 1)
            .returning(Session.turn_count)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one()

    async def deactivate(self, session_id: UUID) -> None:
        """Mark a session as inactive."""
        await self.update_fields(session_id, is_active=False)
