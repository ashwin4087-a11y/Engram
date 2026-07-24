"""
Async Redis client manager — working memory cache layer.
Handles connection lifecycle, working memory read/write, and TTL management.
"""
from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)


class RedisManager:
    """
    Lifecycle manager for the async Redis client.
    Provides typed methods for working memory operations.
    """

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def startup(self) -> None:
        """Initialize the Redis connection pool."""
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
        try:
            await self._client.ping()
            log.info("redis.startup.complete", url=settings.REDIS_URL.split("@")[-1])
        except Exception as e:
            log.warning("redis.startup.failed", error=str(e))
            self._client = None

    async def shutdown(self) -> None:
        """Close the Redis connection pool."""
        if self._client:
            await self._client.aclose()
            log.info("redis.shutdown.complete")

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("RedisManager.startup() was never called or failed.")
        return self._client

    @property
    def is_available(self) -> bool:
        return self._client is not None

    # ── Working Memory Operations ───────────────────────────────────────────

    def _working_memory_key(self, session_id: str) -> str:
        return f"engram:wm:{session_id}"

    async def set_working_memory(
        self, session_id: str, bundle: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Store the current working memory bundle for a session."""
        if not self.is_available:
            log.warning("redis.unavailable", op="set_working_memory")
            return
        key = self._working_memory_key(session_id)
        ttl = ttl or settings.REDIS_WORKING_MEMORY_TTL
        await self.client.setex(key, ttl, json.dumps(bundle, default=str))
        log.debug("redis.working_memory.set", session_id=session_id)

    async def get_working_memory(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve the cached working memory bundle for a session."""
        if not self.is_available:
            return None
        key = self._working_memory_key(session_id)
        raw = await self.client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def invalidate_working_memory(self, session_id: str) -> None:
        """Invalidate the working memory cache (e.g., after new observations)."""
        if not self.is_available:
            return
        key = self._working_memory_key(session_id)
        await self.client.delete(key)
        log.debug("redis.working_memory.invalidated", session_id=session_id)

    # ── Generic Cache Operations ────────────────────────────────────────────

    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        if self.is_available:
            await self.client.setex(key, ttl, value)

    async def get(self, key: str) -> str | None:
        if not self.is_available:
            return None
        return await self.client.get(key)

    async def delete(self, key: str) -> None:
        if self.is_available:
            await self.client.delete(key)

    async def incr(self, key: str) -> int:
        """Atomic increment for rate limiting counters."""
        if not self.is_available:
            return 0
        return await self.client.incr(key)

    async def expire(self, key: str, ttl: int) -> None:
        if self.is_available:
            await self.client.expire(key, ttl)


redis_manager = RedisManager()
