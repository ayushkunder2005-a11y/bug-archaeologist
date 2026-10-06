"""Pydantic schemas for Commit endpoints."""

from datetime import datetime

from pydantic import BaseModel


class CommitResponse(BaseModel):
    """Single commit with analysis data."""
    id: str
    hash: str
    short_hash: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    is_fix_commit: bool
    is_bug_introducing: bool
    bug_intro_score: float
    risk_explanation: str | None = None
    files_changed: int
    insertions: int
    deletions: int
    total_changes: int
    avg_complexity: float
    max_complexity: float

    class Config:
        from_attributes = True


class CommitListResponse(BaseModel):
    """Paginated commit list."""
    commits: list[CommitResponse]
    total: int
    page: int
    per_page: int
