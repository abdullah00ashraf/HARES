from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker
from hares.core.config import get_settings

settings = get_settings()

from sqlalchemy.pool import StaticPool

def _build_async_engine() -> AsyncEngine:
    if "sqlite" in settings.DATABASE_URL:
        is_memory = ":memory:" in settings.DATABASE_URL
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            poolclass=StaticPool if is_memory else None,
            connect_args={"check_same_thread": False} if is_memory else {},
        )
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def _build_sync_engine():
    if "sqlite" in settings.DATABASE_URL_SYNC:
        is_memory = ":memory:" in settings.DATABASE_URL_SYNC
        return create_engine(
            settings.DATABASE_URL_SYNC,
            echo=settings.DEBUG,
            poolclass=StaticPool if is_memory else None,
            connect_args={"check_same_thread": False} if is_memory else {},
        )
    return create_engine(
        settings.DATABASE_URL_SYNC,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


# Asynchronous engine & sessionmaker for FastAPI HTTP context
async_engine: AsyncEngine = _build_async_engine()

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Synchronous engine & sessionmaker for Celery worker thread context
sync_engine = _build_sync_engine()

sync_session_factory = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for asynchronous database operations."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def sync_session_scope() -> Generator[Session, None, None]:
    """Context manager for synchronous worker database operations."""
    session = sync_session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
