"""
Entity domain service for deduplication and fetching logic.
"""
from __future__ import annotations

from uuid import UUID
from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.relationship_repo import RelationshipRepository

class EntityService:
    def __init__(self, entity_repo: EntityRepository, rel_repo: RelationshipRepository):
        self.entity_repo = entity_repo
        self.rel_repo = rel_repo

    async def merge_entities(self, target_id: UUID, duplicate_id: UUID) -> None:
        """Merge a duplicate entity into a target entity."""
        target = await self.entity_repo.get_by_id(target_id)
        duplicate = await self.entity_repo.get_by_id(duplicate_id)
        if not target or not duplicate:
            return

        # 1. Update relationships
        outgoing = await self.rel_repo.get_by_entity(duplicate_id, direction="outgoing")
        for rel in outgoing:
            await self.rel_repo.update_fields(rel.id, source_entity_id=target_id)
            
        incoming = await self.rel_repo.get_by_entity(duplicate_id, direction="incoming")
        for rel in incoming:
            await self.rel_repo.update_fields(rel.id, target_entity_id=target_id)

        # 2. Add duplicate's name as an alias to the target
        await self.entity_repo.add_alias(target_id, duplicate.name)

        # 3. Deactivate duplicate
        await self.entity_repo.update_fields(duplicate_id, is_active=False)
