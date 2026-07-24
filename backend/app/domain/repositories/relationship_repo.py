"""Relationship repository — graph edge queries, supersession."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import and_, func, or_, select

from app.domain.entities.models import Entity, Relationship, RelationType
from app.domain.repositories.base import BaseRepository


class RelationshipRepository(BaseRepository[Relationship]):
    model = Relationship

    async def get_by_session(
        self,
        session_id: UUID,
        *,
        active_only: bool = True,
        limit: int = 200,
    ) -> Sequence[Relationship]:
        """Fetch all relationships in a session."""
        stmt = select(Relationship).where(Relationship.session_id == session_id)
        if active_only:
            stmt = stmt.where(Relationship.is_active.is_(True))
        stmt = stmt.order_by(Relationship.confidence.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_by_entity(
        self,
        entity_id: UUID,
        *,
        active_only: bool = True,
        direction: str = "both",  # "outgoing" | "incoming" | "both"
    ) -> Sequence[Relationship]:
        """Fetch relationships connected to an entity."""
        conditions = []
        if direction in ("outgoing", "both"):
            conditions.append(Relationship.source_entity_id == entity_id)
        if direction in ("incoming", "both"):
            conditions.append(Relationship.target_entity_id == entity_id)

        stmt = select(Relationship).where(or_(*conditions))
        if active_only:
            stmt = stmt.where(Relationship.is_active.is_(True))
        stmt = stmt.order_by(Relationship.confidence.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def find_between(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: RelationType | None = None,
    ) -> Relationship | None:
        """Find an existing relationship between two entities."""
        stmt = select(Relationship).where(
            and_(
                Relationship.source_entity_id == source_id,
                Relationship.target_entity_id == target_id,
                Relationship.is_active.is_(True),
            )
        )
        if relation_type:
            stmt = stmt.where(Relationship.relation_type == relation_type)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def supersede(
        self, old_rel_id: UUID, new_rel_id: UUID,
    ) -> None:
        """Mark a relationship as superseded (contradiction resolution)."""
        from app.utils.time import utcnow
        await self.update_fields(
            old_rel_id,
            is_active=False,
            superseded_by_id=new_rel_id,
            valid_until=utcnow(),
        )

    async def get_neighbors(
        self,
        entity_id: UUID,
        *,
        max_depth: int = 2,
        active_only: bool = True,
    ) -> Sequence[Relationship]:
        """
        Get all relationships within N hops of an entity.
        For depth=1, returns direct connections.
        For depth>1, walks the graph iteratively.
        """
        visited_entities: set[UUID] = {entity_id}
        all_rels: list[Relationship] = []
        frontier: set[UUID] = {entity_id}

        for _ in range(max_depth):
            if not frontier:
                break
            rels = await self._get_rels_for_entities(
                frontier, active_only=active_only,
            )
            new_frontier: set[UUID] = set()
            for rel in rels:
                if rel.id not in {r.id for r in all_rels}:
                    all_rels.append(rel)
                for eid in (rel.source_entity_id, rel.target_entity_id):
                    if eid not in visited_entities:
                        new_frontier.add(eid)
                        visited_entities.add(eid)
            frontier = new_frontier

        return all_rels

    async def _get_rels_for_entities(
        self,
        entity_ids: set[UUID],
        *,
        active_only: bool = True,
    ) -> Sequence[Relationship]:
        """Helper: fetch relationships touching any of the given entity IDs."""
        stmt = select(Relationship).where(
            or_(
                Relationship.source_entity_id.in_(entity_ids),
                Relationship.target_entity_id.in_(entity_ids),
            )
        )
        if active_only:
            stmt = stmt.where(Relationship.is_active.is_(True))
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def count_by_session(self, session_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Relationship)
            .where(
                and_(
                    Relationship.session_id == session_id,
                    Relationship.is_active.is_(True),
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
