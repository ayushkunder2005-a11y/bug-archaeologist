"""Pydantic schemas for dashboard / analysis endpoints."""

from pydantic import BaseModel


class FileAnalysisResponse(BaseModel):
    """File-level analysis summary."""
    file_path: str
    language: str
    total_lines: int
    functions_count: int
    classes_count: int
    avg_complexity: float
    max_complexity: float
    times_changed: int
    times_in_fix_commit: int
    bug_proneness_score: float

    class Config:
        from_attributes = True


class FunctionAnalysisResponse(BaseModel):
    """Function-level analysis summary."""
    name: str
    file_path: str
    line_number: int
    complexity: float
    length_lines: int
    parameter_count: int
    nested_depth: int
    has_docstring: bool
    has_error_handling: bool
    times_changed: int
    times_in_fix_commit: int
    is_bug_prone: bool
    bug_proneness_score: float

    class Config:
        from_attributes = True


class DeveloperStat(BaseModel):
    """Per-developer statistics."""
    name: str
    email: str
    total_commits: int
    fix_commits: int
    bug_introducing_commits: int
    avg_risk_score: float
    files_touched: int


class ComplexityTrend(BaseModel):
    """Complexity data point for trending."""
    date: str
    avg_complexity: float
    max_complexity: float
    commit_hash: str


class RiskBucket(BaseModel):
    """Risk distribution bucket."""
    label: str
    count: int
    color: str


class BugTimelinePoint(BaseModel):
    """Bug timeline data point."""
    date: str
    introductions: int
    fixes: int
    cumulative_open: int


class DashboardResponse(BaseModel):
    """Complete dashboard data for a repository."""
    # Overview
    repository_name: str
    total_commits: int
    total_bugs: int
    health_score: float
    total_files: int
    avg_complexity: float
    total_developers: int
    analysis_date: str | None = None

    # Charts
    bug_timeline: list[BugTimelinePoint]
    risk_distribution: list[RiskBucket]
    top_problematic_files: list[FileAnalysisResponse]
    top_bug_prone_functions: list[FunctionAnalysisResponse]
    developer_stats: list[DeveloperStat]
    complexity_trends: list[ComplexityTrend]
