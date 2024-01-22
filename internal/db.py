import os
import sys

from alembic import command
from alembic.config import Config
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from sdk import verify_not_used

__config_path__ = "./alembic.ini"
__migration_path__ = "./alembic/"

cfg = Config(__config_path__)
cfg.set_main_option("script_location", __migration_path__)


class Database:
    """Database class."""

    def __init__(self):
        """Initializes the instance."""
        if os.getenv("DATABASE_URL") is None:
            logger.error("Failed to initialize database: no DATABASE_URL defined in env.")
            sys.exit(1)
        self.initialized = False

        self.DB_URL = os.getenv("DATABASE_URL")
        self.sync_engine = create_engine(self.DB_URL.replace("asyncpg", "psycopg2"))
        self.engine = AsyncEngine(create_engine(self.DB_URL))
        self.run_migration()

        self.initialized = True
        logger.success("Database instance initialized.")

    @staticmethod
    def _execute_upgrade(connection):
        cfg.attributes["connection"] = connection
        command.upgrade(cfg, "head")

    def run_migration(self):
        logger.info("Running database migrations.")
        if not database_exists(self.sync_engine.url):
            logger.debug("Creating database.")
            create_database(self.sync_engine.url)
        self._execute_upgrade(self.sync_engine)
        logger.success("Database migrations completed successfully.")

    async def get_session(self) -> AsyncSession:
        if not self.initialized:
            logger.critical("RACE: DB session creation called before initialization")
            verify_not_used("database", "initialization")
        # noinspection PyTypeChecker
        async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        return async_session()
