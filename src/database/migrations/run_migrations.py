"""
Database migrations runner
"""

import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from ...config.settings import get_settings
from ..models import Base

logger = logging.getLogger(__name__)

async def run_migrations():
    """Run database migrations"""
    try:
        settings = get_settings()
        engine = create_async_engine(settings.database_url)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database migrations completed successfully")
        print("✅ Database initialized and tables created")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(run_migrations())
