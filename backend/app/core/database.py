"""
Async database manager — SQLAlchemy 2.0 with asyncpg.
Provides session factory and health-check utilities.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

log = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base — all ORM models inherit from this."""
    pass


class DatabaseManager:
    """
    Lifecycle manager for the async database engine and session factory.
    Instantiated once at startup, torn down on shutdown.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def startup(self) -> None:
        """Initialize engine, run pgvector setup, create tables."""
        self._engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
            },
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        async with self._engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

        # Import all models so Base.metadata is populated before create_all
        from app.domain.entities import models  # noqa: F401
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        log.info("database.startup.complete", url=settings.DATABASE_URL.split("@")[-1])

    async def shutdown(self) -> None:
        if self._engine:
            await self._engine.dispose()
            log.info("database.shutdown.complete")

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("DatabaseManager.startup() was never called.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager.startup() was never called.")
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context-managed async session with automatic rollback on error."""
        async with self._session_factory() as session:  # type: ignore[misc]
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


database_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a managed async session."""
    async with database_manager.session() as session:
        yield session
