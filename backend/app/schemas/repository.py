"""Pydantic schemas for Repository endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RepositoryCreate(BaseModel):
    """Request body to submit a repository for analysis."""
    url: str | None = Field(None, description="Public GitHub URL")
    local_path: str | None = Field(None, description="Path to a local Git repository")
    max_commits: int = Field(500, ge=10, le=5000, description="Max commits to analyze")

    @field_validator("url", "local_path")
    @classmethod
    def at_least_one(cls, v, info):
        return v

    def model_post_init(self, __context) -> None:
        if not self.url and not self.local_path:
            raise ValueError("Provide either 'url' or 'local_path'")


class RepositoryResponse(BaseModel):
    """Full repository details."""
    id: str
    name: str
    url: str | None = None
    local_path: str | None = None
    status: str
    error_message: str | None = None
    total_commits: int
    total_files: int
    total_bugs_detected: int
    health_score: float
    primary_language: str | None = None
    analyzed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryListResponse(BaseModel):
    """Paginated list of repositories."""
    repositories: list[RepositoryResponse]
    total: int


class RepositoryStatusResponse(BaseModel):
    """Lightweight status check."""
    id: str
    status: str
    error_message: str | None = None
    progress_message: str | None = None
