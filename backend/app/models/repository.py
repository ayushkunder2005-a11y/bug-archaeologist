"""Repository model for MongoDB."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.base import MongoBaseModel


class Repository(MongoBaseModel):
    def __init__(
        self,
        name: str,
        id: str | None = None,
        url: str | None = None,
        local_path: str | None = None,
        status: str = "pending",
        error_message: str | None = None,
        total_commits: int = 0,
        total_files: int = 0,
        total_bugs_detected: int = 0,
        health_score: float = 0.0,
        primary_language: str | None = None,
        analyzed_at: datetime | None = None,
        created_at: datetime | None = None,
        **extra: Any,
    ):
        data = {
            "id": id or str(uuid.uuid4()),
            "name": name,
            "url": url,
            "local_path": local_path,
            "status": status,
            "error_message": error_message,
            "total_commits": total_commits,
            "total_files": total_files,
            "total_bugs_detected": total_bugs_detected,
            "health_score": health_score,
            "primary_language": primary_language,
            "analyzed_at": analyzed_at,
            "created_at": created_at or datetime.now(timezone.utc),
            **extra,
        }
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"<Repository {self.name} ({self.status})>"
