"""FastAPI application entry point with MongoDB connection lifecycle."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.database.mongodb import MongoDBManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize MongoDB indexes on startup and close connection on shutdown."""
    logger.info("Starting %s v%s (MongoDB Target: %s)", settings.APP_NAME, settings.APP_VERSION, settings.MONGODB_URL)
    await MongoDBManager.init_indexes()
    yield
    await MongoDBManager.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "An intelligent software-engineering analysis platform that analyzes "
        "Git repository history to reconstruct how bugs were introduced, "
        "evolved, and eventually fixed. All results are stored in MongoDB."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "MongoDB",
        "docs": "/docs",
    }
