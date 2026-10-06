"""Async MongoDB connection and database session provider using Motor."""

import logging
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.config import settings

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Manages Motor AsyncIOMotorClient connection pool."""

    client: AsyncIOMotorClient | None = None

    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        if cls.client is None:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
        return cls.client

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        client = cls.get_client()
        return client[settings.MONGODB_DB_NAME]

    @classmethod
    async def close(cls) -> None:
        if cls.client:
            cls.client.close()
            cls.client = None
            logger.info("Closed MongoDB client connection pool")

    @classmethod
    async def init_indexes(cls) -> None:
        """Create necessary indexes for efficient querying."""
        db = cls.get_db()

        # Repositories collection
        await db.repositories.create_index([("created_at", DESCENDING)])

        # Commits collection
        await db.commits.create_indexes([
            IndexModel([("repository_id", ASCENDING), ("authored_date", DESCENDING)]),
            IndexModel([("hash", ASCENDING)]),
            IndexModel([("short_hash", ASCENDING)]),
        ])

        # Bugs collection
        await db.bugs.create_indexes([
            IndexModel([("repository_id", ASCENDING), ("introduction_date", DESCENDING)]),
            IndexModel([("score", DESCENDING)]),
        ])

        # File Analyses collection
        await db.file_analyses.create_indexes([
            IndexModel([("repository_id", ASCENDING), ("bug_proneness_score", DESCENDING)]),
            IndexModel([("file_path", ASCENDING)]),
        ])

        # Function Analyses collection
        await db.function_analyses.create_indexes([
            IndexModel([("repository_id", ASCENDING), ("bug_proneness_score", DESCENDING)]),
        ])

        logger.info("MongoDB indexes initialized successfully")


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """FastAPI dependency yielding the MongoDB database instance."""
    yield MongoDBManager.get_db()
