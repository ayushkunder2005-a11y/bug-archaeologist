"""Commit model for MongoDB."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.base import MongoBaseModel


class Commit(MongoBaseModel):
    def __init__(
        self,
        repository_id: str,
        hash: str,
        short_hash: str,
        message: str,
        author_name: str,
        author_email: str,
        authored_date: datetime,
        id: str | None = None,
        is_fix_commit: bool = False,
        is_bug_introducing: bool = False,
        bug_intro_score: float = 0.0,
        risk_explanation: str | None = None,
        files_changed: int = 0,
        insertions: int = 0,
        deletions: int = 0,
        total_changes: int = 0,
        avg_complexity: float = 0.0,
        max_complexity: float = 0.0,
        created_at: datetime | None = None,
        **extra: Any,
    ):
        data = {
            "id": id or str(uuid.uuid4()),
            "repository_id": repository_id,
            "hash": hash,
            "short_hash": short_hash,
            "message": message,
            "author_name": author_name,
            "author_email": author_email,
            "authored_date": authored_date,
            "is_fix_commit": is_fix_commit,
            "is_bug_introducing": is_bug_introducing,
            "bug_intro_score": bug_intro_score,
            "risk_explanation": risk_explanation,
            "files_changed": files_changed,
            "insertions": insertions,
            "deletions": deletions,
            "total_changes": total_changes,
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "created_at": created_at or datetime.now(timezone.utc),
            **extra,
        }
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"<Commit {self.short_hash} by {self.author_name}>"
