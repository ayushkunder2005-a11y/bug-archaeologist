"""FileAnalysis model for MongoDB."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.base import MongoBaseModel


class FileAnalysis(MongoBaseModel):
    def __init__(
        self,
        repository_id: str,
        file_path: str,
        id: str | None = None,
        language: str = "unknown",
        total_lines: int = 0,
        code_lines: int = 0,
        functions_count: int = 0,
        classes_count: int = 0,
        imports_count: int = 0,
        avg_complexity: float = 0.0,
        max_complexity: float = 0.0,
        times_changed: int = 0,
        times_in_fix_commit: int = 0,
        bug_proneness_score: float = 0.0,
        created_at: datetime | None = None,
        **extra: Any,
    ):
        data = {
            "id": id or str(uuid.uuid4()),
            "repository_id": repository_id,
            "file_path": file_path,
            "language": language,
            "total_lines": total_lines,
            "code_lines": code_lines,
            "functions_count": functions_count,
            "classes_count": classes_count,
            "imports_count": imports_count,
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "times_changed": times_changed,
            "times_in_fix_commit": times_in_fix_commit,
            "bug_proneness_score": bug_proneness_score,
            "created_at": created_at or datetime.now(timezone.utc),
            **extra,
        }
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"<FileAnalysis {self.file_path}>"
