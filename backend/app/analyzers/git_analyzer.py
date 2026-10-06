"""Git repository analyzer — extracts commit history, diffs, and metadata."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import git

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Parsed data from a single Git commit."""
    hash: str
    short_hash: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    files_changed: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    total_changes: int = 0
    is_merge: bool = False


@dataclass
class FileDiff:
    """Diff information for a single file in a commit."""
    file_path: str
    change_type: str  # A, D, M, R
    insertions: int = 0
    deletions: int = 0
    diff_text: str = ""


class GitAnalyzer:
    """Analyzes a Git repository's commit history using GitPython."""

    # Patterns that suggest a commit is a bug fix
    FIX_PATTERN = re.compile(
        r"\b(" + "|".join(settings.FIX_KEYWORDS) + r")\b",
        re.IGNORECASE,
    )

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo = git.Repo(str(self.repo_path))
        self._blame_cache: dict[tuple[str, str], dict[int, str]] = {}
        self._content_cache: dict[tuple[str, str], str | None] = {}
        logger.info("Opened repository at %s", self.repo_path)

    def close(self):
        """Close the underlying GitPython repository object."""
        if hasattr(self, "repo") and self.repo:
            try:
                self.repo.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def clone_repo(url: str, target_dir: str) -> "GitAnalyzer":
        """Clone a remote repository and return an analyzer for it."""
        import os
        from app.utils import cleanup_clone
        logger.info("Cloning %s → %s", url, target_dir)
        cleanup_clone(target_dir)
        try:
            git.Repo.clone_from(url, target_dir, depth=None)
        except git.exc.GitCommandError as exc:
            # On Windows, repos containing colons/special chars in filenames fail working tree checkout.
            # If .git directory exists, the commit objects are intact and ready for history analysis.
            if os.path.exists(os.path.join(target_dir, ".git")):
                logger.warning("Working tree checkout warning during clone, proceeding with .git history: %s", exc)
            else:
                raise
        return GitAnalyzer(target_dir)

    # ── Commit extraction ────────────────────────────────────────

    def get_commits(self, max_count: int | None = None) -> list[CommitInfo]:
        """Extract commit history from the default branch."""
        max_count = max_count or settings.MAX_COMMITS
        commits: list[CommitInfo] = []

        for commit in self.repo.iter_commits(max_count=max_count):
            try:
                info = self._parse_commit(commit)
                commits.append(info)
            except Exception as exc:
                logger.warning("Skipping commit %s: %s", commit.hexsha[:8], exc)

        logger.info("Extracted %d commits", len(commits))
        return commits

    def _parse_commit(self, commit: git.Commit) -> CommitInfo:
        """Parse a GitPython commit object into a CommitInfo."""
        files_changed: list[str] = []
        insertions = 0
        deletions = 0

        try:
            stats = commit.stats
            files_changed = list(stats.files.keys())
            insertions = stats.total.get("insertions", 0)
            deletions = stats.total.get("deletions", 0)
        except Exception:
            pass

        authored_date = datetime.fromtimestamp(commit.authored_date, tz=timezone.utc)

        return CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:8],
            message=commit.message.strip(),
            author_name=commit.author.name or "Unknown",
            author_email=commit.author.email or "unknown@unknown",
            authored_date=authored_date,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
            total_changes=insertions + deletions,
            is_merge=len(commit.parents) > 1,
        )

    # ── Fix-commit detection ────────────────────────────────────

    def is_fix_commit(self, message: str) -> bool:
        """Heuristic: does the commit message suggest a bug fix?"""
        return bool(self.FIX_PATTERN.search(message))

    # ── File content at a commit ────────────────────────────────

    def get_file_content_at_commit(self, commit_hash: str, file_path: str) -> str | None:
        """Return the content of a file at a specific commit, or None."""
        key = (commit_hash, file_path)
        if key in self._content_cache:
            return self._content_cache[key]

        content: str | None = None
        try:
            commit = self.repo.commit(commit_hash)
            blob = commit.tree / file_path
            content = blob.data_stream.read().decode("utf-8", errors="replace")
        except (KeyError, git.exc.GitCommandError, TypeError):
            content = None

        self._content_cache[key] = content
        return content

    # ── Files changed between commits ───────────────────────────

    def get_file_diffs(self, commit_hash: str) -> list[FileDiff]:
        """Get per-file diff data for a commit."""
        commit = self.repo.commit(commit_hash)
        diffs: list[FileDiff] = []

        if not commit.parents:
            # Initial commit — diff against empty tree
            for item in commit.tree.traverse():
                if item.type == "blob":
                    diffs.append(FileDiff(file_path=item.path, change_type="A"))
            return diffs

        parent = commit.parents[0]
        for diff_item in parent.diff(commit):
            file_path = diff_item.b_path or diff_item.a_path or ""
            change_type = diff_item.change_type or "M"
            diff_text = ""
            try:
                diff_text = diff_item.diff.decode("utf-8", errors="replace") if diff_item.diff else ""
            except Exception:
                pass

            diffs.append(FileDiff(
                file_path=file_path,
                change_type=change_type,
                diff_text=diff_text,
            ))

        return diffs

    # ── Blame-based line tracking (SZZ-like) ────────────────────

    def blame_lines(self, file_path: str, commit_hash: str) -> dict[int, str]:
        """
        Run git blame on a file at a specific commit.
        Returns {line_number: commit_hash_that_introduced_it}.
        """
        key = (file_path, commit_hash)
        if key in self._blame_cache:
            return self._blame_cache[key]

        result: dict[int, str] = {}
        try:
            commit = self.repo.commit(commit_hash)
            blames = self.repo.blame(commit, file_path)
            line_num = 1
            for blamed_commit, lines in blames:
                for _ in lines:
                    result[line_num] = blamed_commit.hexsha
                    line_num += 1
        except Exception as exc:
            logger.debug("Blame failed for %s@%s: %s", file_path, commit_hash[:8], exc)

        self._blame_cache[key] = result
        return result

    # ── Utilities ───────────────────────────────────────────────

    def get_python_files(self) -> list[str]:
        """List all .py files in the current working tree."""
        py_files: list[str] = []
        try:
            for item in self.repo.head.commit.tree.traverse():
                if item.type == "blob" and item.path.endswith(".py"):
                    py_files.append(item.path)
        except Exception as exc:
            logger.debug("Failed to traverse HEAD tree for python files: %s", exc)
        return py_files

    def get_all_files(self) -> list[str]:
        """List all files in the current working tree."""
        try:
            return [
                item.path
                for item in self.repo.head.commit.tree.traverse()
                if item.type == "blob"
            ]
        except Exception as exc:
            logger.debug("Failed to traverse HEAD tree for all files: %s", exc)
            return []

    def get_file_extension_stats(self) -> dict[str, int]:
        """Count files by extension."""
        stats: dict[str, int] = {}
        for f in self.get_all_files():
            ext = Path(f).suffix.lower() or "(no extension)"
            stats[ext] = stats.get(ext, 0) + 1
        return stats
