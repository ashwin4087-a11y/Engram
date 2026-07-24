"""
Core configuration — single source of truth for all settings.
Uses pydantic-settings for env-based configuration with type validation.
"""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/engram_db"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ── Redis ───────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_WORKING_MEMORY_TTL: int = 3600  # 1 hour

    # ── CORS ────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # ── LLM Providers ───────────────────────────────────────
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: Literal["anthropic", "openai", "gemini", "mock"] = "mock"
    DEFAULT_LLM_MODEL: str = "claude-3-haiku-20240307"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 3

    # ── Embeddings ──────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32

    # ── Memory & Context ────────────────────────────────────
    CONTEXT_BUDGET_TOKENS: int = 1500
    CONTEXT_MAX_ENTITIES: int = 20
    CONTEXT_MAX_FACTS: int = 30
    CONTEXT_MAX_EPISODES: int = 10

    # Retrieval weights (must sum to 1.0)
    RETRIEVAL_WEIGHT_SIMILARITY: float = 0.45
    RETRIEVAL_WEIGHT_RECENCY: float = 0.25
    RETRIEVAL_WEIGHT_IMPORTANCE: float = 0.20
    RETRIEVAL_WEIGHT_CONFIDENCE: float = 0.10

    # Memory decay
    DECAY_HALF_LIFE_DAYS: int = 30
    CONSOLIDATION_MIN_EPISODES: int = 3

    # ── Rate Limiting ───────────────────────────────────────
    RATE_LIMIT_OBSERVE: int = 60   # per minute
    RATE_LIMIT_QUERY: int = 120

    @model_validator(mode="after")
    def validate_retrieval_weights(self) -> "Settings":
        total = (
            self.RETRIEVAL_WEIGHT_SIMILARITY
            + self.RETRIEVAL_WEIGHT_RECENCY
            + self.RETRIEVAL_WEIGHT_IMPORTANCE
            + self.RETRIEVAL_WEIGHT_CONFIDENCE
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Retrieval weights must sum to 1.0, got {total}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
