"""
Security layer — rate limiting, request-ID injection, prompt-injection sanitization.
"""
from __future__ import annotations

import re
import uuid
from typing import Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.redis import redis_manager

log = structlog.get_logger(__name__)

# ── Request ID Middleware ───────────────────────────────────────────────────


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Injects a unique X-Request-ID header into every request/response."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        structlog.contextvars.unbind_contextvars("request_id")
        return response


# ── Rate Limiting Middleware ────────────────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter backed by Redis.
    Falls back to permissive mode if Redis is unavailable.
    """

    # Route prefix → requests per minute
    LIMITS: dict[str, int] = {
        "/api/v1/observe": settings.RATE_LIMIT_OBSERVE,
        "/api/v1/query": settings.RATE_LIMIT_QUERY,
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not redis_manager.is_available:
            return await call_next(request)

        path = request.url.path
        for prefix, limit in self.LIMITS.items():
            if path.startswith(prefix):
                client_ip = request.client.host if request.client else "unknown"
                key = f"engram:rl:{prefix}:{client_ip}"
                current = await redis_manager.incr(key)
                if current == 1:
                    await redis_manager.expire(key, 60)
                if current > limit:
                    log.warning(
                        "security.rate_limit.exceeded",
                        path=path, client_ip=client_ip, limit=limit,
                    )
                    return JSONResponse(
                        status_code=429,
                        content={
                            "error": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit of {limit}/min exceeded.",
                        },
                    )
                break

        return await call_next(request)


# ── Prompt Injection Sanitization ───────────────────────────────────────────

# Common prompt injection patterns
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a|an)\s+", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile(r"<\|system\|>", re.IGNORECASE),
]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent prompt injection attacks.
    Strips known injection patterns and control characters.
    """
    # Remove null bytes and other control characters (keep newlines/tabs)
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Flag and strip known injection patterns
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(sanitized):
            log.warning(
                "security.prompt_injection.detected",
                pattern=pattern.pattern,
                text_preview=text[:100],
            )
            sanitized = pattern.sub("[REDACTED]", sanitized)

    return sanitized.strip()


def is_safe_input(text: str) -> bool:
    """Check whether input contains known prompt injection patterns."""
    return not any(p.search(text) for p in _INJECTION_PATTERNS)
