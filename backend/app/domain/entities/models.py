"""
SQLAlchemy 2.0 ORM models — the complete Engram domain model.

All tables use UUID primary keys, proper FK constraints, pgvector columns,
composite indexes, and automatic timestamps.  Every model inherits from the
shared `Base` declared in `core.database`.
"""
from __future__ import annotations

import enum
import uuid as _uuid
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base


# ── Enums ───────────────────────────────────────────────────────────────────


class EntityType(str, enum.Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    PROJECT = "project"
    TASK = "task"
    PREFERENCE = "preference"
    GOAL = "goal"
    EVENT = "event"
    DOCUMENT = "document"
    TECHNOLOGY = "technology"
    CONVERSATION = "conversation"
    CONCEPT = "concept"


class RelationType(str, enum.Enum):
    BELONGS_TO = "belongs_to"
    WORKS_ON = "works_on"
    PREFERS = "prefers"
    LOCATED_IN = "located_in"
    RELATED_TO = "related_to"
    USES = "uses"
    OWNS = "owns"
    DEPENDS_ON = "depends_on"
    MENTIONS = "mentions"
    PARTICIPATED_IN = "participated_in"


class FactStatus(str, enum.Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> _uuid.UUID:
    return _uuid.uuid4()


_VEC_DIM = settings.EMBEDDING_DIMENSION  # 384 by default


# ── Session ─────────────────────────────────────────────────────────────────


class Session(Base):
    """Top-level session — scopes all memory to a user/agent conversation."""

    __tablename__ = "sessions"

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    entities: Mapped[list[Entity]] = relationship(back_populates="session", lazy="selectin")
    facts: Mapped[list[Fact]] = relationship(back_populates="session", lazy="selectin")
    episodes: Mapped[list[Episode]] = relationship(back_populates="session", lazy="selectin")


# ── Entity ──────────────────────────────────────────────────────────────────


class Entity(Base):
    """
    A named entity extracted from user input.
    Supports 12 entity types, aliases, importance scoring, and embeddings.
    """

    __tablename__ = "entities"
    __table_args__ = (
        Index("ix_entities_session_importance", "session_id", "importance"),
        Index("ix_entities_session_type", "session_id", "entity_type"),
        UniqueConstraint("session_id", "name", "entity_type", name="uq_entity_session_name_type"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type_enum", create_constraint=True),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    embedding = mapped_column(Vector(_VEC_DIM), nullable=True)

    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    session: Mapped[Session] = relationship(back_populates="entities")
    aliases: Mapped[list[EntityAlias]] = relationship(
        back_populates="entity", cascade="all, delete-orphan",
    )
    facts: Mapped[list[Fact]] = relationship(back_populates="entity")
    outgoing_relationships: Mapped[list[Relationship]] = relationship(
        back_populates="source_entity",
        foreign_keys="Relationship.source_entity_id",
    )
    incoming_relationships: Mapped[list[Relationship]] = relationship(
        back_populates="target_entity",
        foreign_keys="Relationship.target_entity_id",
    )


# ── Entity Alias ────────────────────────────────────────────────────────────


class EntityAlias(Base):
    """Alternative names for an entity (for deduplication and fuzzy matching)."""

    __tablename__ = "entity_aliases"
    __table_args__ = (
        UniqueConstraint("entity_id", "alias", name="uq_alias_entity"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    entity_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    alias: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    entity: Mapped[Entity] = relationship(back_populates="aliases")


# ── Relationship (Graph Edge) ───────────────────────────────────────────────


class Relationship(Base):
    """
    A typed, directed edge between two entities.
    Supports confidence, temporal validity, and supersession for contradiction tracking.
    """

    __tablename__ = "relationships"
    __table_args__ = (
        Index("ix_rel_session", "session_id"),
        Index("ix_rel_source", "source_entity_id"),
        Index("ix_rel_target", "target_entity_id"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_entity_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_entity_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[RelationType] = mapped_column(
        Enum(RelationType, name="relation_type_enum", create_constraint=True),
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    superseded_by_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("relationships.id"), nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    source_entity: Mapped[Entity] = relationship(
        back_populates="outgoing_relationships",
        foreign_keys=[source_entity_id],
    )
    target_entity: Mapped[Entity] = relationship(
        back_populates="incoming_relationships",
        foreign_keys=[target_entity_id],
    )
    superseded_by: Mapped[Relationship | None] = relationship(
        remote_side=[id], foreign_keys=[superseded_by_id],
    )


# ── Fact (Semantic Memory) ──────────────────────────────────────────────────


class Fact(Base):
    """
    An atomic factual statement extracted from user input.
    Stored with pgvector embeddings for similarity search.
    Supports supersession for contradiction resolution.
    """

    __tablename__ = "facts"
    __table_args__ = (
        Index("ix_facts_session_importance", "session_id", "importance"),
        Index("ix_facts_session_status", "session_id", "status"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    entity_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FactStatus] = mapped_column(
        Enum(FactStatus, name="fact_status_enum", create_constraint=True),
        default=FactStatus.ACTIVE,
    )

    embedding = mapped_column(Vector(_VEC_DIM), nullable=True)

    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    superseded_by_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facts.id"), nullable=True,
    )
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    session: Mapped[Session] = relationship(back_populates="facts")
    entity: Mapped[Entity | None] = relationship(back_populates="facts")
    superseded_by: Mapped[Fact | None] = relationship(
        remote_side=[id], foreign_keys=[superseded_by_id],
    )


# ── Episode (Episodic Memory) ──────────────────────────────────────────────


class Episode(Base):
    """
    A compressed event summary — hierarchical episodic memory.
    Level 0 = raw observation summary.
    Level 1+ = consolidated summaries of lower-level episodes.
    """

    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_session_level", "session_id", "level"),
        Index("ix_episodes_session_active", "session_id", "is_active"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=0)
    parent_episode_ids = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)

    embedding = mapped_column(Vector(_VEC_DIM), nullable=True)

    importance: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    turn_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow,
    )

    # Relationships
    session: Mapped[Session] = relationship(back_populates="episodes")


# ── Context Bundle (Working Memory Snapshot) ────────────────────────────────


class ContextBundle(Base):
    """
    Snapshot of an assembled context bundle — enables timeline replay.
    Stores the full JSON bundle plus metadata about its compilation.
    """

    __tablename__ = "context_bundles"
    __table_args__ = (
        Index("ix_cb_session_turn", "session_id", "turn_number"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    bundle_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    retrieval_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── Contradiction Log ───────────────────────────────────────────────────────


class ContradictionLog(Base):
    """
    Audit trail of detected contradictions and their resolution.
    Never delete — this is the history of belief changes.
    """

    __tablename__ = "contradiction_logs"

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    entity_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("entities.id", ondelete="SET NULL"),
        nullable=True,
    )
    old_fact_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facts.id", ondelete="SET NULL"),
        nullable=True,
    )
    new_fact_id: Mapped[_uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facts.id", ondelete="SET NULL"),
        nullable=True,
    )
    old_statement: Mapped[str] = mapped_column(Text, nullable=False)
    new_statement: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[str] = mapped_column(
        String(50), default="superseded",
    )  # superseded | retracted | coexist

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ── Metrics ─────────────────────────────────────────────────────────────────


class Metric(Base):
    """Historical metrics storage — tracks system performance over time."""

    __tablename__ = "metrics"
    __table_args__ = (
        Index("ix_metrics_session_name", "session_id", "name"),
    )

    id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=_new_uuid,
    )
    session_id: Mapped[_uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    turn_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
