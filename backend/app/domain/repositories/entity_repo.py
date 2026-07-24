"""Entity repository — CRUD, alias resolution, similarity search."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.models import Entity, EntityAlias, EntityType
from app.domain.repositories.base import BaseRepository
from app.utils.text import normalize_entity_name


class EntityRepository(BaseRepository[Entity]):
    model = Entity

    async def get_by_session(
        self,
        session_id: UUID,
        *,
        active_only: bool = True,
        entity_type: EntityType | None = None,
        limit: int = 100,
    ) -> Sequence[Entity]:
        """Fetch entities for a session, optionally filtered by type."""
        stmt = select(Entity).where(Entity.session_id == session_id)
        if active_only:
            stmt = stmt.where(Entity.is_active.is_(True))
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        stmt = stmt.order_by(Entity.importance.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def find_by_name(
        self, session_id: UUID, name: str, entity_type: EntityType | None = None,
    ) -> Entity | None:
        """
        Find an entity by exact name match (case-insensitive)
        or by alias match within a session.
        """
        normalized = normalize_entity_name(name)
        # Check primary name
        stmt = select(Entity).where(
            and_(
                Entity.session_id == session_id,
                func.lower(Entity.name) == normalized,
            )
        )
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        result = await self._session.execute(stmt)
        entity = result.scalar_one_or_none()
        if entity:
            return entity

        # Check aliases
        stmt = (
            select(Entity)
            .join(EntityAlias, EntityAlias.entity_id == Entity.id)
            .where(
                and_(
                    Entity.session_id == session_id,
                    func.lower(EntityAlias.alias) == normalized,
                )
            )
        )
        if entity_type:
            stmt = stmt.where(Entity.entity_type == entity_type)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_similar_by_name(
        self, session_id: UUID, name: str, threshold: float = 0.3,
    ) -> Sequence[Entity]:
        """
        Fuzzy-match entities by name using pg_trgm similarity.
        Requires the pg_trgm extension.
        """
        stmt = (
            select(Entity)
            .where(
                and_(
                    Entity.session_id == session_id,
                    Entity.is_active.is_(True),
                    func.similarity(func.lower(Entity.name), normalize_entity_name(name))
                    > threshold,
                )
            )
            .order_by(
                func.similarity(func.lower(Entity.name), normalize_entity_name(name)).desc()
            )
            .limit(5)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add_alias(self, entity_id: UUID, alias: str) -> EntityAlias:
        """Add an alias to an entity."""
        alias_obj = EntityAlias(entity_id=entity_id, alias=alias)
        self._session.add(alias_obj)
        await self._session.flush()
        return alias_obj

    async def increment_access(self, entity_id: UUID) -> None:
        """Increment access count and update last_accessed_at."""
        from app.utils.time import utcnow
        await self.update_fields(
            entity_id,
            access_count=Entity.access_count + 1,
            last_accessed_at=utcnow(),
        )

    async def count_by_session(self, session_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Entity)
            .where(
                and_(Entity.session_id == session_id, Entity.is_active.is_(True))
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def search_by_embedding(
        self, session_id: UUID, embedding: list[float], limit: int = 10,
    ) -> Sequence[tuple[Entity, float]]:
        """
        Vector similarity search on entity embeddings.
        Returns (entity, distance) tuples ordered by similarity.
        """
        stmt = (
            select(
                Entity,
                Entity.embedding.cosine_distance(embedding).label("distance"),
            )
            .where(
                and_(
                    Entity.session_id == session_id,
                    Entity.is_active.is_(True),
                    Entity.embedding.isnot(None),
                )
            )
            .order_by("distance")
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
