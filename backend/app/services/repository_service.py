"""Repository service — handles ingestion, cloning, and CRUD with MongoDB."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.models.repository import Repository
from app.utils import sanitize_repo_name, get_clone_path, cleanup_clone

logger = logging.getLogger(__name__)


class RepositoryService:
    """Manages repository lifecycle in MongoDB: create, list, get, delete."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create(self, url: str | None = None, local_path: str | None = None) -> Repository:
        """Register a new repository for analysis."""
        if url:
            name = sanitize_repo_name(url)
        elif local_path:
            name = sanitize_repo_name(local_path)
        else:
            raise ValueError("Provide url or local_path")

        repo = Repository(
            name=name,
            url=url,
            local_path=local_path or get_clone_path(name),
            status="pending",
        )
        doc = repo.to_dict()
        await self.db.repositories.insert_one(doc)
        logger.info("Created repository record: %s (%s)", repo.name, repo.id)
        return repo

    async def get(self, repo_id: str) -> Repository | None:
        """Get a repository by ID."""
        doc = await self.db.repositories.find_one({"id": repo_id})
        return Repository.from_mongo(doc)

    async def list_all(self) -> list[Repository]:
        """List all repositories."""
        cursor = self.db.repositories.find().sort("created_at", DESCENDING)
        docs = await cursor.to_list(length=1000)
        return [Repository.from_mongo(d) for d in docs]

    async def delete(self, repo_id: str) -> bool:
        """Delete a repository and all related analysis data from MongoDB."""
        repo = await self.get(repo_id)
        if not repo:
            return False

        # Clean up cloned repo on disk if any
        if repo.local_path and os.path.exists(repo.local_path):
            clone_dir = get_clone_path(repo.name)
            if repo.local_path == clone_dir:
                cleanup_clone(repo.local_path)

        # Delete all repository data from Mongo collections
        await self.db.repositories.delete_one({"id": repo_id})
        await self.db.commits.delete_many({"repository_id": repo_id})
        await self.db.bugs.delete_many({"repository_id": repo_id})
        await self.db.file_analyses.delete_many({"repository_id": repo_id})
        await self.db.function_analyses.delete_many({"repository_id": repo_id})

        logger.info("Deleted repository and all associated collections: %s", repo.name)
        return True

    async def save(self, repo: Repository) -> None:
        """Save/Update a repository record in MongoDB."""
        await self.db.repositories.replace_one({"id": repo.id}, repo.to_dict(), upsert=True)

    async def update_status(
        self, repo: Repository, status: str, error: str | None = None
    ) -> None:
        """Update repository analysis status."""
        repo.status = status
        repo.error_message = error
        if status == "complete":
            repo.analyzed_at = datetime.now(timezone.utc)
        await self.save(repo)
