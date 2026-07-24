"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure vector and pg_trgm extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Enum types
    entity_type_enum = postgresql.ENUM(
        'person', 'organization', 'location', 'project', 'task',
        'preference', 'goal', 'event', 'document', 'technology',
        'conversation', 'concept', name='entity_type_enum'
    )
    entity_type_enum.create(op.get_bind(), checkfirst=True)

    relation_type_enum = postgresql.ENUM(
        'belongs_to', 'works_on', 'prefers', 'located_in', 'related_to',
        'uses', 'owns', 'depends_on', 'mentions', 'participated_in',
        name='relation_type_enum'
    )
    relation_type_enum.create(op.get_bind(), checkfirst=True)

    fact_status_enum = postgresql.ENUM(
        'active', 'superseded', 'retracted', name='fact_status_enum'
    )
    fact_status_enum.create(op.get_bind(), checkfirst=True)

    # 1. sessions
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('turn_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. entities
    op.create_table(
        'entities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_type', entity_type_enum, nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('importance', sa.Float(), server_default='0.5', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('session_id', 'name', 'entity_type', name='uq_entity_session_name_type')
    )
    op.create_index('ix_entities_session_importance', 'entities', ['session_id', 'importance'])
    op.create_index('ix_entities_session_type', 'entities', ['session_id', 'entity_type'])

    # 3. entity_aliases
    op.create_table(
        'entity_aliases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias', sa.String(500), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('entity_id', 'alias', name='uq_alias_entity')
    )

    # 4. relationships
    op.create_table(
        'relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation_type', relation_type_enum, nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('relationships.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 5. facts
    op.create_table(
        'facts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('status', fact_status_enum, server_default='active', nullable=False),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('importance', sa.Float(), server_default='0.5', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('access_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facts.id'), nullable=True),
        sa.Column('source_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 6. episodes
    op.create_table(
        'episodes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('level', sa.Integer(), server_default='0', nullable=False),
        sa.Column('parent_episode_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('embedding', Vector(384), nullable=True),
        sa.Column('importance', sa.Float(), server_default='0.5', nullable=False),
        sa.Column('confidence', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 7. context_bundles
    op.create_table(
        'context_bundles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('bundle_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('retrieval_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 8. contradiction_logs
    op.create_table(
        'contradiction_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entities.id', ondelete='SET NULL'), nullable=True),
        sa.Column('old_fact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('new_fact_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('facts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('old_statement', sa.Text(), nullable=False),
        sa.Column('new_statement', sa.Text(), nullable=False),
        sa.Column('resolution', sa.String(50), server_default='superseded', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )

    # 9. metrics
    op.create_table(
        'metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('turn_number', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('metrics')
    op.drop_table('contradiction_logs')
    op.drop_table('context_bundles')
    op.drop_table('episodes')
    op.drop_table('facts')
    op.drop_table('relationships')
    op.drop_table('entity_aliases')
    op.drop_table('entities')
    op.drop_table('sessions')
