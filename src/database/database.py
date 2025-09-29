"""
Database configuration for UAE Social Support AI System
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from typing import AsyncGenerator

from ..config.settings import get_settings

logger = logging.getLogger(__name__)

# Database setup
settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()
metadata = MetaData()

class DatabaseManager:
    """Database connection manager"""

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal

    async def initialize(self):
        """Initialize database connection"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """Create database tables"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async for session in db_manager.get_session():
        yield session

async def init_database():
    """Initialize database"""
    await db_manager.initialize()
