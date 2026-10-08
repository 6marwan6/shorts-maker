"""Async DB engine/session (impl plan §1.3: SQLAlchemy 2.x async API, asyncpg).

Local dev (D0): postgresql+asyncpg://.../shorts_maker_dev via Docker Compose Postgres.
Hosted (D1/D2/P0): Railway PostgreSQL, same driver, connection string from settings.

There is exactly one canonical engine/session factory -- routers and worker code both import
from here rather than each constructing their own engine (impl plan §1.6.1: the API is
stateless; state lives in PostgreSQL/Redis/R2, not in per-module connection pools).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base shared by every table in app.models."""


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: `session: AsyncSession = Depends(get_session)`."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Non-FastAPI callers (worker tasks, scripts, tests): `async with session_scope() as s:`."""
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def dispose_engine() -> None:
    """Call on app/worker shutdown and between tests that swap DATABASE_URL."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
