"""
Analysis service — orchestrates the full analysis pipeline with MongoDB persistence.

Steps:
1. Clone or validate the repository
2. Extract commit history
3. Detect fix commits
4. Run SZZ-based bug detection
5. Analyze Python files with AST
6. Score and persist results to MongoDB collections
7. Compute dashboard aggregates
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.analyzers.ast_analyzer import ASTAnalyzer
from app.analyzers.bug_detector import BugDetector
from app.analyzers.git_analyzer import GitAnalyzer
from app.models.bug import Bug
from app.models.commit import Commit
from app.models.file_analysis import FileAnalysis
from app.models.function_analysis import FunctionAnalysis
from app.models.repository import Repository
from app.utils import get_clone_path, detect_primary_language, cleanup_clone

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates the complete analysis pipeline for a repository using MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.ast_analyzer = ASTAnalyzer()

    async def run_analysis(self, repo: Repository, max_commits: int = 500) -> None:
        """Run the full analysis pipeline in worker threads to prevent event loop hanging."""
        try:
            repo.status = "analyzing"
            await self._update_repo_status(repo)

            # Step 1: Ensure repository on disk (cloning or validating)
            repo_path = await asyncio.to_thread(
                self._ensure_repo_sync, repo.url, repo.local_path, repo.name
            )
            repo.local_path = repo_path
            await self._update_repo_status(repo)

            # Clear any stale data for this repository ID before new analysis run
            await self.db.commits.delete_many({"repository_id": repo.id})
            await self.db.bugs.delete_many({"repository_id": repo.id})
            await self.db.file_analyses.delete_many({"repository_id": repo.id})
            await self.db.function_analyses.delete_many({"repository_id": repo.id})

            # Step 2 & 3: Extract commit history in thread
            logger.info("Extracting commits for %s (max=%d)", repo.name, max_commits)
            def _get_commits_job():
                with GitAnalyzer(repo_path) as ga:
                    return ga.get_commits(max_count=max_commits)

            commit_infos = await asyncio.to_thread(_get_commits_job)

            if not commit_infos:
                repo.status = "error"
                repo.error_message = "No commits found in repository"
                await self._update_repo_status(repo)
                return

            # Step 4: Persist commits
            commit_records = await self._persist_commits(repo, commit_infos)

            # Step 5: Detect bugs in thread
            logger.info("Running bug detection for %s", repo.name)
            def _detect_bugs_job():
                with GitAnalyzer(repo_path) as ga:
                    bd = BugDetector(ga)
                    return bd.detect_bugs(commit_infos)

            bug_candidates = await asyncio.to_thread(_detect_bugs_job)

            # Step 6: Persist bugs and update commit flags
            await self._persist_bugs(repo, bug_candidates, commit_records)

            # Step 7: Analyze source files in thread
            logger.info("Analyzing source files for %s", repo.name)
            def _analyze_files_job():
                with GitAnalyzer(repo_path) as ga:
                    return self._extract_file_analysis_data(ga, commit_infos)

            file_analyses_data, function_analyses_data = await asyncio.to_thread(_analyze_files_job)

            # Persist file & function records
            await self._persist_file_and_function_analyses(
                repo.id, file_analyses_data, function_analyses_data
            )

            # Step 8: Compute repository-level metrics in thread
            def _metrics_job():
                with GitAnalyzer(repo_path) as ga:
                    ext_stats = ga.get_file_extension_stats()
                    total_files = len(ga.get_all_files())
                    return ext_stats, total_files

            ext_stats, total_files = await asyncio.to_thread(_metrics_job)

            from app.config import settings

            significant_bugs = [b for b in bug_candidates if b.score >= settings.BUG_SCORE_THRESHOLD]

            repo.total_commits = len(commit_infos)
            repo.total_files = total_files
            repo.total_bugs_detected = len(significant_bugs)
            repo.primary_language = detect_primary_language(ext_stats)

            bug_ratio = len(significant_bugs) / max(len(commit_infos), 1)
            repo.health_score = max(0.0, min(100.0, 100.0 - (bug_ratio * 300)))

            repo.status = "complete"
            repo.analyzed_at = datetime.now(timezone.utc)
            await self._update_repo_status(repo)

            logger.info(
                "Analysis complete for %s: %d commits, %d bugs detected",
                repo.name, len(commit_infos), len(bug_candidates),
            )

        except Exception as exc:
            logger.exception("Analysis failed for %s: %s", repo.name, exc)
            repo.status = "error"
            repo.error_message = str(exc)[:500]
            await self._update_repo_status(repo)
            raise

    async def _update_repo_status(self, repo: Repository) -> None:
        """Update repository document in MongoDB."""
        await self.db.repositories.replace_one({"id": repo.id}, repo.to_dict(), upsert=True)

    @staticmethod
    def _ensure_repo_sync(url: str | None, local_path: str | None, repo_name: str) -> str:
        """Synchronously clone or validate a repository on disk."""
        import git

        if url:
            clone_path = get_clone_path(repo_name)
            is_valid = False
            if os.path.exists(clone_path):
                try:
                    git.Repo(clone_path)
                    is_valid = True
                except Exception:
                    cleanup_clone(clone_path)

            if not is_valid:
                try:
                    GitAnalyzer.clone_repo(url, clone_path)
                except git.exc.GitCommandError as exc:
                    err_str = str(exc).lower()
                    if "could not resolve host" in err_str or "network" in err_str or "could not read from remote" in err_str:
                        raise RuntimeError(
                            "Network / Internet Error: Unable to connect to remote repository. "
                            "Please check your internet connection or use a local repository path instead."
                        )
                    raise RuntimeError(f"Git clone failed: {exc}")
            return clone_path

        elif local_path:
            clean_path = os.path.abspath(local_path.strip().strip('"').strip("'"))
            if not os.path.exists(clean_path):
                raise ValueError(f"Local repository path does not exist: {clean_path}")
            try:
                git.Repo(clean_path)
            except Exception as exc:
                raise ValueError(f"Specified path is not a valid Git repository: {clean_path}")
            return clean_path
        else:
            raise ValueError("Provide url or local_path")

    async def _persist_commits(
        self,
        repo: Repository,
        commit_infos: list,
    ) -> dict[str, Commit]:
        """Save commit records to MongoDB."""
        records: dict[str, Commit] = {}
        docs: list[dict] = []

        fix_pattern = GitAnalyzer.FIX_PATTERN

        for info in commit_infos:
            is_fix = bool(fix_pattern.search(info.message))
            commit = Commit(
                repository_id=repo.id,
                hash=info.hash,
                short_hash=info.short_hash,
                message=info.message[:1000],
                author_name=info.author_name,
                author_email=info.author_email,
                authored_date=info.authored_date,
                is_fix_commit=is_fix,
                files_changed=len(info.files_changed),
                insertions=info.insertions,
                deletions=info.deletions,
                total_changes=info.total_changes,
            )
            records[info.hash] = commit
            docs.append(commit.to_dict())

        if docs:
            await self.db.commits.insert_many(docs)

        return records

    async def _persist_bugs(
        self,
        repo: Repository,
        bug_candidates: list,
        commit_records: dict[str, Commit],
    ) -> None:
        """Save detected bugs to MongoDB and update commit flags."""
        from app.config import settings

        bug_docs: list[dict] = []

        for candidate in bug_candidates:
            if candidate.score < settings.BUG_SCORE_THRESHOLD:
                continue

            bug = Bug(
                repository_id=repo.id,
                title=self._generate_bug_title(candidate),
                severity=candidate.severity,
                introducing_commit_hash=candidate.introducing_commit.hash,
                fix_commit_hash=candidate.fix_commit.hash,
                introduction_date=candidate.introducing_commit.authored_date,
                fix_date=candidate.fix_commit.authored_date,
                time_to_fix_days=(
                    candidate.fix_commit.authored_date - candidate.introducing_commit.authored_date
                ).total_seconds() / 86400,
                affected_files=candidate.affected_files,
                affected_functions=candidate.affected_functions,
                related_commit_hashes=candidate.related_commits,
                complexity_before=candidate.complexity_before,
                complexity_after=candidate.complexity_after,
                explanation=candidate.explanation,
                introducing_author=candidate.introducing_commit.author_name,
                fix_author=candidate.fix_commit.author_name,
            )
            bug_docs.append(bug.to_dict())

            intro_record = commit_records.get(candidate.introducing_commit.hash)
            if intro_record:
                intro_record.is_bug_introducing = True
                intro_record.bug_intro_score = candidate.score
                intro_record.risk_explanation = candidate.explanation
                # Update commit doc in MongoDB
                await self.db.commits.replace_one({"id": intro_record.id}, intro_record.to_dict())

        if bug_docs:
            await self.db.bugs.insert_many(bug_docs)

    def _extract_file_analysis_data(
        self, git_analyzer: GitAnalyzer, commit_infos: list
    ) -> tuple[list[dict], list[dict]]:
        """Extract file and function level AST metrics synchronously."""
        py_files = git_analyzer.get_python_files()

        file_change_counts: dict[str, int] = defaultdict(int)
        file_fix_counts: dict[str, int] = defaultdict(int)

        for commit_info in commit_infos:
            is_fix = git_analyzer.is_fix_commit(commit_info.message)
            for f in commit_info.files_changed:
                file_change_counts[f] += 1
                if is_fix:
                    file_fix_counts[f] += 1

        file_list: list[dict] = []
        function_list: list[dict] = []

        head_commit_hash = git_analyzer.repo.head.commit.hexsha

        for file_path in py_files[:200]:
            full_path = git_analyzer.repo_path / file_path
            content: str | None = None
            if full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    pass
            if not content:
                content = git_analyzer.get_file_content_at_commit(
                    head_commit_hash, file_path
                )
            if not content:
                continue

            analysis = self.ast_analyzer.analyze_source(content, file_path)
            times_changed = file_change_counts.get(file_path, 0)
            times_in_fix = file_fix_counts.get(file_path, 0)

            file_list.append({
                "file_path": file_path,
                "language": "Python",
                "total_lines": analysis.total_lines,
                "code_lines": analysis.code_lines,
                "functions_count": len(analysis.functions),
                "classes_count": len(analysis.classes),
                "imports_count": len(analysis.imports),
                "avg_complexity": analysis.avg_complexity,
                "max_complexity": analysis.max_complexity,
                "times_changed": times_changed,
                "times_in_fix_commit": times_in_fix,
                "bug_proneness_score": min(100.0, (times_in_fix / max(times_changed, 1)) * 100),
            })

            for func in analysis.functions:
                function_list.append({
                    "name": func.name,
                    "file_path": file_path,
                    "line_number": func.line_number,
                    "complexity": func.complexity,
                    "length_lines": func.length_lines,
                    "parameter_count": func.parameter_count,
                    "nested_depth": func.nested_depth,
                    "has_docstring": func.has_docstring,
                    "has_error_handling": func.has_error_handling,
                    "times_changed": times_changed,
                    "times_in_fix_commit": times_in_fix,
                    "is_bug_prone": times_in_fix >= 2 or func.complexity > 10,
                    "bug_proneness_score": min(
                        100.0,
                        (func.complexity * 5 + times_in_fix * 15),
                    ),
                })

        return file_list, function_list

    async def _persist_file_and_function_analyses(
        self,
        repo_id: str,
        file_data: list[dict],
        function_data: list[dict],
    ) -> None:
        """Persist file and function analyses to MongoDB."""
        file_docs = [
            FileAnalysis(repository_id=repo_id, **fdata).to_dict()
            for fdata in file_data
        ]
        if file_docs:
            await self.db.file_analyses.insert_many(file_docs)

        func_docs = [
            FunctionAnalysis(repository_id=repo_id, **funcdata).to_dict()
            for funcdata in function_data
        ]
        if func_docs:
            await self.db.function_analyses.insert_many(func_docs)

    @staticmethod
    def _generate_bug_title(candidate) -> str:
        """Generate a descriptive title for a bug."""
        files = candidate.affected_files
        if files:
            primary_file = files[0].split("/")[-1]
        else:
            primary_file = "unknown file"

        severity = candidate.severity.capitalize()
        return f"{severity} risk in {primary_file} ({candidate.introducing_commit.short_hash})"
