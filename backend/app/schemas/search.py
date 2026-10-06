"""Pydantic schemas for Search endpoints."""

from pydantic import BaseModel

from app.schemas.commit import CommitResponse
from app.schemas.bug import BugResponse


class SearchRequest(BaseModel):
    """Search query parameters."""
    query: str | None = None
    commit_hash: str | None = None
    file_path: str | None = None
    function_name: str | None = None
    developer: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    repository_id: str | None = None


class SearchResponse(BaseModel):
    """Search results."""
    commits: list[CommitResponse]
    bugs: list[BugResponse]
    total_commits: int
    total_bugs: int
