"""Utility helpers for Git operations."""

from __future__ import annotations

import logging
import os
import re
import shutil
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


def sanitize_repo_name(url_or_path: str) -> str:
    """Extract a clean repository name from a URL or path."""
    # GitHub URL: https://github.com/owner/repo.git
    match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", url_or_path)
    if match:
        return match.group(1).replace("/", "_")

    # Local path
    name = Path(url_or_path).name
    return re.sub(r"[^\w\-.]", "_", name) or "repository"


def get_clone_path(repo_name: str) -> str:
    """Return the full path where a repo should be cloned."""
    return os.path.join(settings.REPO_CLONE_DIR, repo_name)


def _handle_remove_readonly(func, path, exc_info):
    """Error handler for shutil.rmtree to handle read-only files on Windows."""
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def cleanup_clone(path: str) -> None:
    """Remove a cloned repository directory cleanly on Windows/Linux."""
    try:
        if os.path.exists(path):
            shutil.rmtree(path, onerror=_handle_remove_readonly)
            logger.info("Cleaned up clone at %s", path)
    except Exception as exc:
        logger.warning("Failed to clean up %s: %s", path, exc)


def detect_primary_language(extension_stats: dict[str, int]) -> str:
    """Determine the primary language from file extension statistics."""
    lang_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".jsx": "JavaScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
    }

    best_lang = "Unknown"
    best_count = 0

    for ext, count in extension_stats.items():
        lang = lang_map.get(ext)
        if lang and count > best_count:
            best_lang = lang
            best_count = count

    return best_lang
