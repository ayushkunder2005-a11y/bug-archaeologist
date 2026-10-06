"""Pydantic schemas for Bug endpoints."""

from datetime import datetime

from pydantic import BaseModel


class BugResponse(BaseModel):
    """Bug summary for list views."""
    id: str
    title: str
    severity: str
    introducing_commit_hash: str
    fix_commit_hash: str
    introduction_date: datetime
    fix_date: datetime
    time_to_fix_days: float
    affected_files: list[str] | None = None
    affected_functions: list[str] | None = None
    introducing_author: str | None = None
    fix_author: str | None = None
    complexity_before: float
    complexity_after: float

    class Config:
        from_attributes = True


class BugDetailResponse(BugResponse):
    """Full bug detail with explanation and related commits."""
    explanation: str | None = None
    related_commit_hashes: list[str] | None = None


class BugListResponse(BaseModel):
    """List of detected bugs."""
    bugs: list[BugResponse]
    total: int
