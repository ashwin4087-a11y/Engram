"""Metrics repository — insert and query time-series metrics."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, select

from app.domain.entities.models import (
    ContradictionLog,
    ContextBundle,
    Metric,
)
from app.domain.repositories.base import BaseRepository


class MetricsRepository(BaseRepository[Metric]):
    model = Metric

    async def record(
        self,
        session_id: UUID,
        name: str,
        value: float,
        unit: str | None = None,
        turn_number: int | None = None,
        metadata: dict | None = None,
    ) -> Metric:
        """Record a single metric data point."""
        metric = Metric(
            session_id=session_id,
            name=name,
            value=value,
            unit=unit,
            turn_number=turn_number,
            metadata_=metadata,
        )
        return await self.create(metric)

    async def get_by_session(
        self,
        session_id: UUID,
        *,
        name: str | None = None,
        limit: int = 100,
    ) -> Sequence[Metric]:
        """Fetch metrics for a session, optionally filtered by name."""
        stmt = select(Metric).where(Metric.session_id == session_id)
        if name:
            stmt = stmt.where(Metric.name == name)
        stmt = stmt.order_by(Metric.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_latest(
        self, session_id: UUID, name: str,
    ) -> Metric | None:
        """Fetch the most recent metric by name."""
        stmt = (
            select(Metric)
            .where(
                and_(Metric.session_id == session_id, Metric.name == name)
            )
            .order_by(Metric.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class ContextBundleRepository(BaseRepository[ContextBundle]):
    model = ContextBundle

    async def get_by_session(
        self, session_id: UUID, limit: int = 50,
    ) -> Sequence[ContextBundle]:
        stmt = (
            select(ContextBundle)
            .where(ContextBundle.session_id == session_id)
            .order_by(ContextBundle.turn_number.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_turn(
        self, session_id: UUID, turn_number: int,
    ) -> ContextBundle | None:
        stmt = select(ContextBundle).where(
            and_(
                ContextBundle.session_id == session_id,
                ContextBundle.turn_number == turn_number,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


class ContradictionLogRepository(BaseRepository[ContradictionLog]):
    model = ContradictionLog

    async def get_by_session(
        self, session_id: UUID, limit: int = 50,
    ) -> Sequence[ContradictionLog]:
        stmt = (
            select(ContradictionLog)
            .where(ContradictionLog.session_id == session_id)
            .order_by(ContradictionLog.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count_by_session(self, session_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(ContradictionLog)
            .where(ContradictionLog.session_id == session_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
