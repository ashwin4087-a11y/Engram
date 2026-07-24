"""
Custom exception hierarchy for Engram backend.
Never expose raw stack traces — all errors are caught and mapped here.
"""
from typing import Any


class EngramError(Exception):
    """Base exception for all application errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, detail: Any = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


# ── Domain Errors ───────────────────────────────────────────────────────────

class EntityNotFoundError(EngramError):
    status_code = 404
    error_code = "ENTITY_NOT_FOUND"


class SessionNotFoundError(EngramError):
    status_code = 404
    error_code = "SESSION_NOT_FOUND"


class DuplicateEntityError(EngramError):
    status_code = 409
    error_code = "DUPLICATE_ENTITY"


class ContradictionDetectedError(EngramError):
    """Raised when a new fact contradicts an existing one."""
    status_code = 200  # Not an error — signals caller to handle
    error_code = "CONTRADICTION_DETECTED"


# ── Memory Errors ────────────────────────────────────────────────────────────

class MemoryCompilerError(EngramError):
    status_code = 500
    error_code = "COMPILER_ERROR"


class RetrievalError(EngramError):
    status_code = 500
    error_code = "RETRIEVAL_ERROR"


class ConsolidationError(EngramError):
    status_code = 500
    error_code = "CONSOLIDATION_ERROR"


class ContextBudgetExceededError(EngramError):
    status_code = 500
    error_code = "CONTEXT_BUDGET_EXCEEDED"


# ── LLM Provider Errors ──────────────────────────────────────────────────────

class LLMProviderError(EngramError):
    status_code = 502
    error_code = "LLM_PROVIDER_ERROR"


class LLMTimeoutError(LLMProviderError):
    status_code = 504
    error_code = "LLM_TIMEOUT"


class LLMRateLimitError(LLMProviderError):
    status_code = 429
    error_code = "LLM_RATE_LIMIT"


class LLMProviderNotConfiguredError(LLMProviderError):
    status_code = 501
    error_code = "LLM_NOT_CONFIGURED"


# ── Infrastructure Errors ─────────────────────────────────────────────────────

class EmbeddingError(EngramError):
    status_code = 500
    error_code = "EMBEDDING_ERROR"


class CacheError(EngramError):
    status_code = 500
    error_code = "CACHE_ERROR"


class DatabaseError(EngramError):
    status_code = 500
    error_code = "DATABASE_ERROR"


# ── Validation Errors ─────────────────────────────────────────────────────────

class InvalidInputError(EngramError):
    status_code = 422
    error_code = "INVALID_INPUT"


class RateLimitError(EngramError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
