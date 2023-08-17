import os
import sys

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sdk import verify_not_used


class Database:
    """Database class."""

    def __init__(self):
        """Initializes the instance."""
        if os.getenv("DATABASE_URL") is None:
            logger.error("Failed to initialize database: no DATABASE_URL defined in env.")
            sys.exit(1)
        self.initialized = False
        self.engine = AsyncEngine(create_engine(os.getenv("DATABASE_URL")))
        self.initialized = True
        logger.success("Database instance initialized.")

    async def get_session(self) -> AsyncSession:
        if not self.initialized:
            logger.critical("RACE: DB session creation called before initialization")
            verify_not_used("database", "initialization")
        # noinspection PyTypeChecker
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session()
