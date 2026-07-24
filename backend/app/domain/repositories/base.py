"""
Base repository — generic async CRUD operations.

All repositories inherit from this and add domain-specific queries.
Repositories accept AsyncSession via dependency injection — they never
create their own sessions.
"""
from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    Generic async repository providing common CRUD operations.

    Subclasses set `model` to a concrete ORM class and add
    domain-specific query methods.
    """

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """Fetch a single record by primary key."""
        return await self._session.get(self.model, id)

    async def get_many(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        order_by: Any | None = None,
    ) -> Sequence[ModelT]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, obj: ModelT) -> ModelT:
        """Insert a new record."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def create_many(self, objects: list[ModelT]) -> list[ModelT]:
        """Insert multiple records."""
        self._session.add_all(objects)
        await self._session.flush()
        for obj in objects:
            await self._session.refresh(obj)
        return objects

    async def update_fields(
        self, id: UUID, **fields: Any,
    ) -> ModelT | None:
        """Update specific fields on a record."""
        stmt = (
            update(self.model)
            .where(self.model.id == id)  # type: ignore[attr-defined]
            .values(**fields)
            .returning(self.model)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """Count all records."""
        stmt = select(func.count()).select_from(self.model)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists by ID."""
        stmt = select(func.count()).select_from(self.model).where(
            self.model.id == id,  # type: ignore[attr-defined]
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
