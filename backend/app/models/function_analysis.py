"""FunctionAnalysis model for MongoDB."""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.base import MongoBaseModel


class FunctionAnalysis(MongoBaseModel):
    def __init__(
        self,
        repository_id: str,
        name: str,
        file_path: str,
        id: str | None = None,
        line_number: int = 0,
        complexity: float = 1.0,
        length_lines: int = 0,
        parameter_count: int = 0,
        nested_depth: int = 0,
        has_docstring: bool = False,
        has_error_handling: bool = False,
        times_changed: int = 0,
        times_in_fix_commit: int = 0,
        is_bug_prone: bool = False,
        bug_proneness_score: float = 0.0,
        created_at: datetime | None = None,
        **extra: Any,
    ):
        data = {
            "id": id or str(uuid.uuid4()),
            "repository_id": repository_id,
            "name": name,
            "file_path": file_path,
            "line_number": line_number,
            "complexity": complexity,
            "length_lines": length_lines,
            "parameter_count": parameter_count,
            "nested_depth": nested_depth,
            "has_docstring": has_docstring,
            "has_error_handling": has_error_handling,
            "times_changed": times_changed,
            "times_in_fix_commit": times_in_fix_commit,
            "is_bug_prone": is_bug_prone,
            "bug_proneness_score": bug_proneness_score,
            "created_at": created_at or datetime.now(timezone.utc),
            **extra,
        }
        super().__init__(**data)

    def __repr__(self) -> str:
        return f"<FunctionAnalysis {self.name} in {self.file_path}>"
