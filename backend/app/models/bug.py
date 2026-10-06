"""Bug model for MongoDB."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.base import MongoBaseModel


class Bug(MongoBaseModel):
    def __init__(
        self,
        repository_id: str,
        title: str,
        introducing_commit_hash: str,
        fix_commit_hash: str,
        introduction_date: datetime,
        fix_date: datetime,
        id: str | None = None,
        severity: str = "medium",
        time_to_fix_days: float = 0.0,
        affected_files: list | dict | None = None,
        affected_functions: list | dict | None = None,
        related_commit_hashes: list | dict | None = None,
        complexity_before: float = 0.0,
        complexity_after: float = 0.0,
        explanation: str | None = None,
        introducing_author: str | None = None,
        fix_author: str | None = None,
        created_at: datetime | None = None,
        **extra: Any,
    ):
        data = {
            "id": id or str(uuid.uuid4()),
            "repository_id": repository_id,
            "title": title,
            "severity": severity,
            "introducing_commit_hash": introducing_commit_hash,
            "fix_commit_hash": fix_commit_hash,
            "introduction_date": introduction_date,
            "fix_date": fix_date,
            "time_to_fix_days": time_to_fix_days,
            "affected_files": affected_files,
            "affected_functions": affected_functions,
            "related_commit_hashes": related_commit_hashes,
            "complexity_before": complexity_before,
            "complexity_after": complexity_after,
            "explanation": explanation,
            "introducing_author": introducing_author,
            "fix_author": fix_author,
            "created_at": created_at or datetime.now(timezone.utc),
            **extra,
        }
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"<Bug '{self.title}' severity={self.severity}>"
