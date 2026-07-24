"""
Knowledge Graph Engine — manages entities, relationships, graph queries, and React Flow formatting.
"""
from __future__ import annotations

from uuid import UUID
import structlog

from app.domain.repositories.entity_repo import EntityRepository
from app.domain.repositories.relationship_repo import RelationshipRepository
from app.domain.services.entity_service import EntityService
from app.schemas.graph import GraphEdge, GraphNode, GraphResponse

log = structlog.get_logger(__name__)


class KnowledgeGraphEngine:
    def __init__(
        self,
        entity_repo: EntityRepository,
        relationship_repo: RelationshipRepository,
    ) -> None:
        self.entity_repo = entity_repo
        self.relationship_repo = relationship_repo
        self.entity_service = EntityService(entity_repo, relationship_repo)

    async def merge_duplicate_entities(self, target_id: UUID, duplicate_id: UUID) -> None:
        """Delegate to entity service to merge duplicates."""
        await self.entity_service.merge_entities(target_id, duplicate_id)

    async def get_graph(self, session_id: UUID) -> GraphResponse:
        """Fetch all active entities and relationships, formatted for React Flow visualizer."""
        entities = await self.entity_repo.get_by_session(session_id, active_only=True)
        relationships = await self.relationship_repo.get_by_session(session_id, active_only=True)

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        # Convert entities to nodes
        for e in entities:
            nodes.append(
                GraphNode(
                    id=f"entity-{e.id}",
                    type="entityNode",
                    data={
                        "label": e.name,
                        "entity_type": e.entity_type.value,
                        "importance": e.importance,
                        "confidence": e.confidence,
                        "access_count": e.access_count,
                    },
                    position={"x": 0.0, "y": 0.0},  # Frontend handles auto-layout
                )
            )

        # Convert relationships to edges
        for r in relationships:
            edges.append(
                GraphEdge(
                    id=f"rel-{r.id}",
                    source=f"entity-{r.source_entity_id}",
                    target=f"entity-{r.target_entity_id}",
                    label=r.relation_type.value,
                    animated=True,
                    data={"confidence": r.confidence},
                )
            )

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            entity_count=len(nodes),
            relationship_count=len(edges),
        )
