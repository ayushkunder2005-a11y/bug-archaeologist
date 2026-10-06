"""Search endpoint with MongoDB."""

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_db
from app.schemas.bug import BugResponse
from app.schemas.commit import CommitResponse
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.get("", response_model=SearchResponse)
async def search(
    q: str | None = Query(None, description="General search query"),
    commit_hash: str | None = Query(None, description="Search by commit hash"),
    file_path: str | None = Query(None, description="Search by file path"),
    function_name: str | None = Query(None, description="Search by function name"),
    developer: str | None = Query(None, description="Search by developer name/email"),
    date_from: str | None = Query(None, description="Start date (ISO format)"),
    date_to: str | None = Query(None, description="End date (ISO format)"),
    repository_id: str | None = Query(None, description="Filter by repository ID"),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Multi-field search across commits and bugs."""
    svc = SearchService(db)
    result = await svc.search(
        repository_id=repository_id,
        query=q,
        commit_hash=commit_hash,
        file_path=file_path,
        function_name=function_name,
        developer=developer,
        date_from=date_from,
        date_to=date_to,
    )

    return SearchResponse(
        commits=[CommitResponse.model_validate(c) for c in result["commits"]],
        bugs=[BugResponse.model_validate(b) for b in result["bugs"]],
        total_commits=result["total_commits"],
        total_bugs=result["total_bugs"],
    )
