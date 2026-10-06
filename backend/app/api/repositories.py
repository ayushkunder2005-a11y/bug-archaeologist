"""Repository CRUD endpoints with MongoDB."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_db, MongoDBManager
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
    RepositoryStatusResponse,
)
from app.services.analysis_service import AnalysisService
from app.services.repository_service import RepositoryService

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_analysis_background(repo_id: str, max_commits: int) -> None:
    """Run analysis in a background task with MongoDB."""
    db = MongoDBManager.get_db()
    try:
        repo_svc = RepositoryService(db)
        repo = await repo_svc.get(repo_id)
        if not repo:
            logger.error("Repository %s not found for background analysis", repo_id)
            return

        analysis_svc = AnalysisService(db)
        await analysis_svc.run_analysis(repo, max_commits=max_commits)
    except Exception as exc:
        logger.exception("Background analysis failed for %s: %s", repo_id, exc)
        try:
            err_repo_svc = RepositoryService(db)
            err_repo = await err_repo_svc.get(repo_id)
            if err_repo:
                err_repo.status = "error"
                err_repo.error_message = f"Analysis error: {str(exc)[:400]}"
                await err_repo_svc.save(err_repo)
        except Exception as inner_exc:
            logger.error("Failed to update error status for repo %s: %s", repo_id, inner_exc)


@router.post("", response_model=RepositoryResponse, status_code=201)
async def create_repository(
    body: RepositoryCreate,
    background_tasks: BackgroundTasks,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Submit a repository for analysis."""
    svc = RepositoryService(db)
    repo = await svc.create(url=body.url, local_path=body.local_path)

    # Kick off analysis in background
    background_tasks.add_task(_run_analysis_background, repo.id, body.max_commits)

    return repo


@router.post("/{repo_id}/analyze", response_model=RepositoryStatusResponse)
async def trigger_analysis(
    repo_id: str,
    background_tasks: BackgroundTasks,
    max_commits: int = Query(500, ge=10, le=5000),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Trigger or retry background analysis for a repository."""
    svc = RepositoryService(db)
    repo = await svc.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo.status = "pending"
    repo.error_message = None
    await svc.save(repo)

    background_tasks.add_task(_run_analysis_background, repo.id, max_commits)

    return RepositoryStatusResponse(id=repo.id, status=repo.status, error_message=None)


@router.get("", response_model=RepositoryListResponse)
async def list_repositories(db: AsyncIOMotorDatabase = Depends(get_db)):
    """List all repositories."""
    svc = RepositoryService(db)
    repos = await svc.list_all()
    return RepositoryListResponse(repositories=repos, total=len(repos))


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get a single repository's details."""
    svc = RepositoryService(db)
    repo = await svc.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/status", response_model=RepositoryStatusResponse)
async def get_repository_status(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Check analysis status for a repository."""
    svc = RepositoryService(db)
    repo = await svc.get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryStatusResponse(
        id=repo.id,
        status=repo.status,
        error_message=repo.error_message,
    )


@router.delete("/{repo_id}", status_code=204)
async def delete_repository(repo_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Delete a repository and all its analysis data."""
    svc = RepositoryService(db)
    deleted = await svc.delete(repo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository not found")
