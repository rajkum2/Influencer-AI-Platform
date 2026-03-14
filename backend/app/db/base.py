"""
Database base configuration and session management.
"""

from typing import AsyncGenerator, Optional

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create async engine for main application
async_engine = create_async_engine(
    str(settings.database_url),
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.db_echo,
    future=True,
)

# Create sync engine for migrations and admin tasks
sync_engine = create_engine(
    str(settings.sync_database_url),
    pool_pre_ping=True,
    future=True,
)

# Session makers
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)

# Declarative base for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Get a synchronous database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db() -> None:
    """Initialize database - create tables if they don't exist."""
    async with async_engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import (
            audit,
            content,
            crm,
            influencer,
            ranking,
            technology,
            user,
            watchlist,
        )
        
        # Note: In production, use Alembic migrations instead
        if settings.is_development:
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")


async def close_db_connections() -> None:
    """Close all database connections."""
    await async_engine.dispose()
    sync_engine.dispose()
    logger.info("Database connections closed")
