"""Analysis endpoints — dashboard, bugs, commits, files, developers, complexity with MongoDB."""

from __future__ import annotations

import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING

from app.database.mongodb import get_db
from app.models.bug import Bug
from app.models.commit import Commit
from app.models.file_analysis import FileAnalysis
from app.models.function_analysis import FunctionAnalysis
from app.models.repository import Repository
from app.schemas.analysis import (
    BugTimelinePoint,
    ComplexityTrend,
    DashboardResponse,
    DeveloperStat,
    FileAnalysisResponse,
    FunctionAnalysisResponse,
    RiskBucket,
)
from app.schemas.bug import BugDetailResponse, BugListResponse, BugResponse
from app.schemas.commit import CommitListResponse, CommitResponse

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Dashboard ────────────────────────────────────────────────────

@router.get("/{repo_id}/dashboard", response_model=DashboardResponse)
async def get_dashboard(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get complete dashboard data for a repository."""
    repo_doc = await db.repositories.find_one({"id": repo_id})
    if not repo_doc:
        raise HTTPException(status_code=404, detail="Repository not found")
    repo = Repository.from_mongo(repo_doc)
    if repo.status != "complete":
        raise HTTPException(status_code=409, detail=f"Analysis status: {repo.status}")

    # Commits
    commits_cursor = db.commits.find({"repository_id": repo_id}).sort("authored_date", ASCENDING)
    commit_docs = await commits_cursor.to_list(length=10000)
    commits = [Commit.from_mongo(d) for d in commit_docs]

    # Bugs
    bugs_cursor = db.bugs.find({"repository_id": repo_id}).sort("introduction_date", ASCENDING)
    bug_docs = await bugs_cursor.to_list(length=10000)
    bugs = [Bug.from_mongo(d) for d in bug_docs]

    # Files
    files_cursor = db.file_analyses.find({"repository_id": repo_id}).sort("bug_proneness_score", DESCENDING).limit(15)
    file_docs = await files_cursor.to_list(length=15)
    top_files = [FileAnalysis.from_mongo(d) for d in file_docs]

    # Functions
    funcs_cursor = db.function_analyses.find({"repository_id": repo_id}).sort("bug_proneness_score", DESCENDING).limit(15)
    func_docs = await funcs_cursor.to_list(length=15)
    top_functions = [FunctionAnalysis.from_mongo(d) for d in func_docs]

    # Build dashboard aggregates
    bug_timeline = _build_bug_timeline(bugs, commits)
    risk_dist = _build_risk_distribution(commits)
    dev_stats = _build_developer_stats(commits)
    complexity_trends = _build_complexity_trends(commits)

    # Avg complexity across top files
    avg_complexity = 0.0
    if top_files:
        avg_complexity = sum(f.avg_complexity for f in top_files) / len(top_files)

    # Unique developers
    developers = set(c.author_email for c in commits)

    return DashboardResponse(
        repository_name=repo.name,
        total_commits=repo.total_commits,
        total_bugs=repo.total_bugs_detected,
        health_score=repo.health_score,
        total_files=repo.total_files,
        avg_complexity=round(avg_complexity, 2),
        total_developers=len(developers),
        analysis_date=repo.analyzed_at.isoformat() if repo.analyzed_at else None,
        bug_timeline=bug_timeline,
        risk_distribution=risk_dist,
        top_problematic_files=[FileAnalysisResponse.model_validate(f) for f in top_files],
        top_bug_prone_functions=[FunctionAnalysisResponse.model_validate(f) for f in top_functions],
        developer_stats=dev_stats,
        complexity_trends=complexity_trends,
    )


# ── Bugs ─────────────────────────────────────────────────────────

@router.get("/{repo_id}/bugs", response_model=BugListResponse)
async def get_bugs(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """List all detected bugs for a repository."""
    cursor = db.bugs.find({"repository_id": repo_id}).sort("introduction_date", DESCENDING)
    docs = await cursor.to_list(length=1000)
    bugs = [Bug.from_mongo(d) for d in docs]
    return BugListResponse(
        bugs=[BugResponse.model_validate(b) for b in bugs],
        total=len(bugs),
    )


@router.get("/{repo_id}/bugs/{bug_id}", response_model=BugDetailResponse)
async def get_bug_detail(repo_id: str, bug_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get full details for a specific bug."""
    doc = await db.bugs.find_one({"id": bug_id, "repository_id": repo_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Bug not found")
    bug = Bug.from_mongo(doc)
    return BugDetailResponse.model_validate(bug)


# ── Commits ──────────────────────────────────────────────────────

@router.get("/{repo_id}/commits", response_model=CommitListResponse)
async def get_commits(
    repo_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Get paginated commit list with analysis scores."""
    offset = (page - 1) * per_page
    filter_doc = {"repository_id": repo_id}

    total = await db.commits.count_documents(filter_doc)

    cursor = db.commits.find(filter_doc).sort("authored_date", DESCENDING).skip(offset).limit(per_page)
    docs = await cursor.to_list(length=per_page)
    commits = [Commit.from_mongo(d) for d in docs]

    return CommitListResponse(
        commits=[CommitResponse.model_validate(c) for c in commits],
        total=total,
        page=page,
        per_page=per_page,
    )


# ── Files ────────────────────────────────────────────────────────

@router.get("/{repo_id}/files", response_model=list[FileAnalysisResponse])
async def get_files(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get file-level analysis for a repository."""
    cursor = db.file_analyses.find({"repository_id": repo_id}).sort("bug_proneness_score", DESCENDING).limit(50)
    docs = await cursor.to_list(length=50)
    files = [FileAnalysis.from_mongo(d) for d in docs]
    return [FileAnalysisResponse.model_validate(f) for f in files]


# ── Developers ───────────────────────────────────────────────────

@router.get("/{repo_id}/developers", response_model=list[DeveloperStat])
async def get_developers(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get per-developer statistics."""
    cursor = db.commits.find({"repository_id": repo_id})
    docs = await cursor.to_list(length=10000)
    commits = [Commit.from_mongo(d) for d in docs]
    return _build_developer_stats(commits)


# ── Complexity ───────────────────────────────────────────────────

@router.get("/{repo_id}/complexity", response_model=list[ComplexityTrend])
async def get_complexity(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get complexity trend data."""
    cursor = db.commits.find({"repository_id": repo_id}).sort("authored_date", ASCENDING)
    docs = await cursor.to_list(length=10000)
    commits = [Commit.from_mongo(d) for d in docs]
    return _build_complexity_trends(commits)


# ── Helper functions ─────────────────────────────────────────────

def _build_bug_timeline(bugs: list[Bug], commits: list[Commit] | None = None) -> list[BugTimelinePoint]:
    """Build bug introduction/fix timeline (daily or monthly based on date span)."""
    if not bugs:
        if not commits:
            return []
        daily_commits: dict[str, dict] = defaultdict(lambda: {"introductions": 0, "fixes": 0})
        for c in commits:
            day = c.authored_date.strftime("%Y-%m-%d")
            if c.is_fix_commit:
                daily_commits[day]["fixes"] += 1
            if c.is_bug_introducing:
                daily_commits[day]["introductions"] += 1

        points: list[BugTimelinePoint] = []
        for day in sorted(daily_commits.keys()):
            data = daily_commits[day]
            points.append(BugTimelinePoint(
                date=day,
                introductions=data["introductions"],
                fixes=data["fixes"],
                cumulative_open=max(0, data["introductions"] - data["fixes"]),
            ))

        if len(points) == 1:
            points.insert(0, BugTimelinePoint(date="Start", introductions=0, fixes=0, cumulative_open=0))
        return points

    # Determine date format based on span
    dates = [b.introduction_date for b in bugs] + [b.fix_date for b in bugs]
    min_date = min(dates)
    max_date = max(dates)
    span_days = (max_date - min_date).total_seconds() / 86400

    fmt = "%Y-%m-%d" if span_days <= 60 else "%Y-%m"

    timeline_map: dict[str, dict] = defaultdict(lambda: {"introductions": 0, "fixes": 0})

    for bug in bugs:
        intro_key = bug.introduction_date.strftime(fmt)
        fix_key = bug.fix_date.strftime(fmt)
        timeline_map[intro_key]["introductions"] += 1
        timeline_map[fix_key]["fixes"] += 1

    points: list[BugTimelinePoint] = []
    cumulative = 0
    for key in sorted(timeline_map.keys()):
        data = timeline_map[key]
        cumulative += data["introductions"] - data["fixes"]
        points.append(BugTimelinePoint(
            date=key,
            introductions=data["introductions"],
            fixes=data["fixes"],
            cumulative_open=max(0, cumulative),
        ))

    if len(points) == 1:
        points.insert(0, BugTimelinePoint(date="Start", introductions=0, fixes=0, cumulative_open=0))

    return points


def _build_risk_distribution(commits: list[Commit]) -> list[RiskBucket]:
    """Bucket commits by risk score."""
    buckets = {
        "Low (0-25)": 0,
        "Medium (25-50)": 0,
        "High (50-75)": 0,
        "Critical (75-100)": 0,
    }
    colors = {
        "Low (0-25)": "#10b981",
        "Medium (25-50)": "#f59e0b",
        "High (50-75)": "#f97316",
        "Critical (75-100)": "#ef4444",
    }

    for c in commits:
        score = c.bug_intro_score
        if score < 25:
            buckets["Low (0-25)"] += 1
        elif score < 50:
            buckets["Medium (25-50)"] += 1
        elif score < 75:
            buckets["High (50-75)"] += 1
        else:
            buckets["Critical (75-100)"] += 1

    return [
        RiskBucket(label=label, count=count, color=colors[label])
        for label, count in buckets.items()
    ]


def _build_developer_stats(commits: list[Commit]) -> list[DeveloperStat]:
    """Aggregate per-developer statistics."""
    devs: dict[str, dict] = {}

    for c in commits:
        key = c.author_email
        if key not in devs:
            devs[key] = {
                "name": c.author_name,
                "email": c.author_email,
                "total_commits": 0,
                "fix_commits": 0,
                "bug_introducing_commits": 0,
                "total_risk": 0.0,
                "files": set(),
            }
        d = devs[key]
        d["total_commits"] += 1
        if c.is_fix_commit:
            d["fix_commits"] += 1
        if c.is_bug_introducing:
            d["bug_introducing_commits"] += 1
        d["total_risk"] += c.bug_intro_score
        d["files"].add(c.id)

    stats = []
    for d in devs.values():
        stats.append(DeveloperStat(
            name=d["name"],
            email=d["email"],
            total_commits=d["total_commits"],
            fix_commits=d["fix_commits"],
            bug_introducing_commits=d["bug_introducing_commits"],
            avg_risk_score=round(d["total_risk"] / max(d["total_commits"], 1), 1),
            files_touched=len(d["files"]),
        ))

    return sorted(stats, key=lambda s: s.total_commits, reverse=True)


def _build_complexity_trends(commits: list[Commit]) -> list[ComplexityTrend]:
    """Build complexity trend from commits (sampled)."""
    if not commits:
        return []

    # Sample at most 50 points
    step = max(1, len(commits) // 50)
    sampled = commits[::step]

    return [
        ComplexityTrend(
            date=c.authored_date.strftime("%Y-%m-%d"),
            avg_complexity=c.avg_complexity,
            max_complexity=c.max_complexity,
            commit_hash=c.short_hash,
        )
        for c in sampled
    ]
