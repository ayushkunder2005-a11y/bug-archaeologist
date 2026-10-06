"""Root API router — mounts all sub-routers."""

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.repositories import router as repo_router
from app.api.analysis import router as analysis_router
from app.api.search import router as search_router

api_router = APIRouter(prefix="/api")

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(repo_router, prefix="/repositories", tags=["Repositories"])
api_router.include_router(analysis_router, prefix="/repositories", tags=["Analysis"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
