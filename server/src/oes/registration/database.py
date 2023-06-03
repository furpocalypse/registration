"""Database module."""
from __future__ import annotations

import functools
from builtins import BaseException
from contextvars import ContextVar
from typing import Optional

import orjson
from attrs import frozen
from oes.registration.entities.base import metadata
from oes.registration.serialization.json import json_default
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

session_context: ContextVar[Optional[AsyncSession]] = ContextVar(
    "session_context", default=None
)


@frozen
class DBConfig:
    engine: AsyncEngine
    session_factory: async_sessionmaker

    @classmethod
    def create(cls, url: str) -> DBConfig:
        """Create a :class:`DBConfig`."""
        engine = create_async_engine(url, json_serializer=_json_dumps)
        session_factory = async_sessionmaker(bind=engine)
        return cls(engine, session_factory)

    async def close(self):
        """Tear down the DB engine."""
        await self.engine.dispose()

    async def create_tables(self):
        """Create all database tables."""

        # Import modules that define entities
        import oes.registration.entities.cart  # noqa
        import oes.registration.entities.checkout  # noqa
        import oes.registration.entities.event_stats  # noqa
        import oes.registration.entities.registration  # noqa

        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def drop_tables(self):
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(metadata.drop_all)


def _json_dumps(v):
    return orjson.dumps(v, default=json_default).decode()


def db_session_factory(services) -> AsyncSession:
    session = session_context.get()

    if not session:
        db_config: DBConfig = services.provider[DBConfig]
        session = db_config.session_factory()
        session_context.set(session)

    return session


async def db_session_middleware(request, handler):
    """Middleware to close the DB session."""
    try:
        return await handler(request)
    finally:
        session = session_context.get()
        if session is not None:
            await session.close()


async def _commit_or_rollback(session: Optional[AsyncSession], success: bool):
    if session:
        if success:
            await session.commit()
        else:
            await session.rollback()


def transaction(fn):
    """Transaction decorator."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        success = True
        try:
            return await fn(*args, **kwargs)
        except BaseException:
            success = False
            raise
        finally:
            session = session_context.get()
            await _commit_or_rollback(session, success)

    return wrapper
