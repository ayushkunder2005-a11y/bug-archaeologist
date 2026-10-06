"""Search service — multi-field search across commits, bugs, files in MongoDB."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app.models.bug import Bug
from app.models.commit import Commit

logger = logging.getLogger(__name__)


class SearchService:
    """Provides search functionality across analysis results in MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def search(
        self,
        repository_id: str | None = None,
        query: str | None = None,
        commit_hash: str | None = None,
        file_path: str | None = None,
        function_name: str | None = None,
        developer: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        """Search commits and bugs with multiple filters."""
        commits = await self._search_commits(
            repository_id, query, commit_hash, developer, date_from, date_to
        )
        bugs = await self._search_bugs(
            repository_id, query, file_path, function_name
        )

        return {
            "commits": commits,
            "bugs": bugs,
            "total_commits": len(commits),
            "total_bugs": len(bugs),
        }

    async def _search_commits(
        self,
        repository_id: str | None,
        query: str | None,
        commit_hash: str | None,
        developer: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> list[Commit]:
        """Search commits collection in MongoDB."""
        filter_doc: dict = {}

        if repository_id:
            filter_doc["repository_id"] = repository_id

        if commit_hash:
            filter_doc["$or"] = [
                {"hash": {"$regex": f"^{re.escape(commit_hash)}", "$options": "i"}},
                {"short_hash": {"$regex": f"^{re.escape(commit_hash)}", "$options": "i"}},
            ]

        if developer:
            dev_regex = {"$regex": re.escape(developer), "$options": "i"}
            dev_condition = [
                {"author_name": dev_regex},
                {"author_email": dev_regex},
            ]
            if "$or" in filter_doc:
                filter_doc["$and"] = [{"$or": filter_doc.pop("$or")}, {"$or": dev_condition}]
            else:
                filter_doc["$or"] = dev_condition

        if query:
            filter_doc["message"] = {"$regex": re.escape(query), "$options": "i"}

        if date_from or date_to:
            date_filter = {}
            if date_from:
                try:
                    date_filter["$gte"] = datetime.fromisoformat(date_from)
                except ValueError:
                    pass
            if date_to:
                try:
                    date_filter["$lte"] = datetime.fromisoformat(date_to)
                except ValueError:
                    pass
            if date_filter:
                filter_doc["authored_date"] = date_filter

        cursor = self.db.commits.find(filter_doc).sort("authored_date", DESCENDING).limit(100)
        docs = await cursor.to_list(length=100)
        return [Commit.from_mongo(d) for d in docs]

    async def _search_bugs(
        self,
        repository_id: str | None,
        query: str | None,
        file_path: str | None,
        function_name: str | None,
    ) -> list[Bug]:
        """Search bugs collection in MongoDB."""
        filter_doc: dict = {}

        if repository_id:
            filter_doc["repository_id"] = repository_id

        if query:
            q_regex = {"$regex": re.escape(query), "$options": "i"}
            filter_doc["$or"] = [
                {"title": q_regex},
                {"explanation": q_regex},
            ]

        if file_path:
            filter_doc["affected_files"] = {"$regex": re.escape(file_path), "$options": "i"}

        if function_name:
            filter_doc["affected_functions"] = {"$regex": re.escape(function_name), "$options": "i"}

        cursor = self.db.bugs.find(filter_doc).sort("introduction_date", DESCENDING).limit(100)
        docs = await cursor.to_list(length=100)
        return [Bug.from_mongo(d) for d in docs]
