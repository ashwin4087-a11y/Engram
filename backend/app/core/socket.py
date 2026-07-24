"""
Socket.IO server — real-time event streaming to connected clients.
Every memory operation emits typed events so the frontend can
animate the brain graph, update metrics, and show compiler activity.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any

import socketio
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)


class EventType(str, enum.Enum):
    """All WebSocket event types the backend can emit."""

    # Entity lifecycle
    ENTITY_CREATED = "entity.created"
    ENTITY_UPDATED = "entity.updated"
    ENTITY_MERGED = "entity.merged"

    # Fact lifecycle
    FACT_ADDED = "fact.added"
    FACT_MERGED = "fact.merged"
    FACT_SUPERSEDED = "fact.superseded"

    # Relationship lifecycle
    RELATIONSHIP_CREATED = "relationship.created"
    RELATIONSHIP_UPDATED = "relationship.updated"

    # Contradiction
    CONTRADICTION_DETECTED = "contradiction.detected"
    CONTRADICTION_RESOLVED = "contradiction.resolved"

    # Memory operations
    CONTEXT_COMPILED = "context.compiled"
    MEMORY_RETRIEVED = "memory.retrieved"

    # Consolidation
    CONSOLIDATION_STARTED = "consolidation.started"
    CONSOLIDATION_FINISHED = "consolidation.finished"
    EPISODE_DECAYED = "episode.decayed"
    EPISODE_MERGED = "episode.merged"

    # Compiler
    COMPILER_STAGE_STARTED = "compiler.stage.started"
    COMPILER_STAGE_FINISHED = "compiler.stage.finished"
    COMPILER_FINISHED = "compiler.finished"

    # Agent runtime
    PROMPT_GENERATED = "prompt.generated"
    LLM_RESPONSE_RECEIVED = "llm.response.received"

    # Metrics
    METRICS_UPDATED = "metrics.updated"


# ── Socket.IO Server Instance ──────────────────────────────────────────────

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.CORS_ORIGINS,
    logger=False,
    engineio_logger=False,
)


@sio.event
async def connect(sid: str, environ: dict[str, Any]) -> None:
    log.info("socket.client.connected", sid=sid)


@sio.event
async def disconnect(sid: str) -> None:
    log.info("socket.client.disconnected", sid=sid)


@sio.on("join_session")
async def on_join_session(sid: str, data: dict[str, Any]) -> None:
    """Client joins a session room to receive scoped events."""
    session_id = data.get("session_id", "")
    if session_id:
        sio.enter_room(sid, f"session:{session_id}")
        log.info("socket.session.joined", sid=sid, session_id=session_id)


@sio.on("leave_session")
async def on_leave_session(sid: str, data: dict[str, Any]) -> None:
    session_id = data.get("session_id", "")
    if session_id:
        sio.leave_room(sid, f"session:{session_id}")
        log.info("socket.session.left", sid=sid, session_id=session_id)


# ── Event Emitter ───────────────────────────────────────────────────────────

class EventEmitter:
    """
    Type-safe event emitter that broadcasts events to session rooms.
    All memory subsystems use this to push real-time updates.
    """

    def __init__(self, server: socketio.AsyncServer) -> None:
        self._sio = server

    async def emit(
        self,
        event_type: EventType,
        session_id: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Emit a typed event to all clients in a session room."""
        event_data = {
            "type": event_type.value,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        }
        room = f"session:{session_id}"
        await self._sio.emit("engram_event", event_data, room=room)
        log.debug(
            "socket.event.emitted",
            event=event_type.value,
            session_id=session_id,
        )

    async def emit_entity_created(
        self, session_id: str, entity_id: str, name: str, entity_type: str
    ) -> None:
        await self.emit(EventType.ENTITY_CREATED, session_id, {
            "entity_id": entity_id, "name": name, "entity_type": entity_type,
        })

    async def emit_fact_added(
        self, session_id: str, fact_id: str, statement: str, entity_name: str
    ) -> None:
        await self.emit(EventType.FACT_ADDED, session_id, {
            "fact_id": fact_id, "statement": statement, "entity_name": entity_name,
        })

    async def emit_contradiction_detected(
        self, session_id: str, old_fact: str, new_fact: str, entity_name: str
    ) -> None:
        await self.emit(EventType.CONTRADICTION_DETECTED, session_id, {
            "old_fact": old_fact, "new_fact": new_fact, "entity_name": entity_name,
        })

    async def emit_relationship_created(
        self, session_id: str, rel_id: str,
        source: str, target: str, rel_type: str,
    ) -> None:
        await self.emit(EventType.RELATIONSHIP_CREATED, session_id, {
            "relationship_id": rel_id, "source": source,
            "target": target, "relation_type": rel_type,
        })

    async def emit_context_compiled(
        self, session_id: str, token_count: int, memory_count: int
    ) -> None:
        await self.emit(EventType.CONTEXT_COMPILED, session_id, {
            "token_count": token_count, "memory_count": memory_count,
        })

    async def emit_consolidation_started(self, session_id: str, episode_count: int) -> None:
        await self.emit(EventType.CONSOLIDATION_STARTED, session_id, {
            "episode_count": episode_count,
        })

    async def emit_consolidation_finished(
        self, session_id: str, merged_count: int, summary: str
    ) -> None:
        await self.emit(EventType.CONSOLIDATION_FINISHED, session_id, {
            "merged_count": merged_count, "summary": summary,
        })

    async def emit_compiler_stage(
        self, session_id: str, stage_name: str, finished: bool = False,
        result_count: int = 0,
    ) -> None:
        event = EventType.COMPILER_STAGE_FINISHED if finished else EventType.COMPILER_STAGE_STARTED
        await self.emit(event, session_id, {
            "stage": stage_name, "result_count": result_count,
        })


# Singleton emitter used across the application
event_emitter = EventEmitter(sio)
