"""
Database configuration for UAE Social Support AI System
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy import text

from ..config.settings import get_settings
from .models import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager"""

    def __init__(self):
        self.settings = get_settings()
        self.engine = None
        self.session_factory = None
        self.database_url = self.settings.database_url
        self._configure_engine(self.database_url)

    async def initialize(self):
        """Initialize database connection"""
        try:
            await self._test_primary_connection()
            await self._create_tables()
            logger.info("Database initialized successfully (engine=%s)", self.database_url)
        except Exception as e:
            if self._should_fallback(e):
                fallback_url = "sqlite+aiosqlite:///./social_support.db"
                if self.database_url != fallback_url:
                    logger.warning(
                        "Primary database unavailable (%s). Falling back to local SQLite database.",
                        e,
                    )
                    self._configure_engine(fallback_url)
                    await self._create_tables()
                    logger.info("Database fallback to SQLite successful")
                    return
            logger.error("Database initialization failed: %s", e)
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
            await self._create_tables()
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise

    def _configure_engine(self, database_url: str) -> None:
        """Configure async engine and session factory"""
        if self.engine is not None:
            try:
                self.engine.sync_engine.dispose()
            except Exception as dispose_error:  # pragma: no cover - best effort cleanup
                logger.warning("Failed to dispose previous engine: %s", dispose_error)

        self.engine = create_async_engine(
            database_url,
            echo=self.settings.database_echo,
            future=True,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self.database_url = database_url

    async def _test_primary_connection(self) -> None:
        """Verify the current engine is reachable before creating tables."""
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def _create_tables(self) -> None:
        """Create all tables using the current engine"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def _should_fallback(self, error: Exception) -> bool:
        """Determine if the database initialization should fall back to SQLite."""
        message = str(error).lower()
        connection_issue = any(
            keyword in message
            for keyword in [
                "connection refused",
                "could not connect",
                "connection closed",
                "connect call failed",
            ]
        )
        engine_name = make_url(self.database_url).get_backend_name()
        return connection_issue and engine_name != "sqlite"

# Global database manager instance
db_manager = DatabaseManager()

async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async for session in db_manager.get_session():
        yield session

async def init_database():
    """Initialize database"""
    await db_manager.initialize()
