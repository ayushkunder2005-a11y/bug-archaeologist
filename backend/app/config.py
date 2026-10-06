"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the Bug Archaeologist backend."""

    # ── Application ──────────────────────────────────────────────
    APP_NAME: str = "Bug Archaeologist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ─────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "bug_archaeologist_db"

    # ── Repository Cloning ───────────────────────────────────────
    REPO_CLONE_DIR: str = str(Path(__file__).resolve().parent.parent / "repos")
    MAX_COMMITS: int = 500

    # ── GitHub (optional) ────────────────────────────────────────
    GITHUB_TOKEN: str | None = None

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # ── Analysis tunables ────────────────────────────────────────
    FIX_KEYWORDS: list[str] = [
        "fix", "bug", "patch", "resolve", "hotfix",
        "issue", "closes", "fixes", "fixed", "repair",
        "defect", "error", "fault", "crash", "cve",
    ]
    BUG_SCORE_THRESHOLD: float = 40.0  # Minimum score to flag a commit

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

# Ensure clone directory exists
os.makedirs(settings.REPO_CLONE_DIR, exist_ok=True)
