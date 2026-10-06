"""
Bug-introduction detector — SZZ-inspired algorithm.

Uses fix commits as anchors, then traces back through Git blame
to find the commits that likely introduced the bugs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.analyzers.ast_analyzer import ASTAnalyzer
from app.analyzers.complexity import ComplexityCalculator
from app.analyzers.git_analyzer import CommitInfo, GitAnalyzer
from app.analyzers.scoring import ScoringEngine, ScoreFactors

logger = logging.getLogger(__name__)


@dataclass
class BugCandidate:
    """A potential bug-introduction event."""
    introducing_commit: CommitInfo
    fix_commit: CommitInfo
    affected_files: list[str] = field(default_factory=list)
    affected_functions: list[str] = field(default_factory=list)
    related_commits: list[str] = field(default_factory=list)
    score_factors: ScoreFactors | None = None
    score: float = 0.0
    severity: str = "low"
    complexity_before: float = 0.0
    complexity_after: float = 0.0
    explanation: str = ""


class BugDetector:
    """
    Detects bug-introducing commits using an SZZ-inspired approach:

    1. Identify fix commits (keyword heuristics on commit messages).
    2. For each fix, find which files/functions were modified.
    3. Walk backwards through history to find the commit that last
       modified the same code before the fix.
    4. Use git blame to trace changed lines to their introducing commit.
    5. Score each candidate with the ScoringEngine.
    """

    def __init__(self, git_analyzer: GitAnalyzer):
        self.git = git_analyzer
        self.ast_analyzer = ASTAnalyzer()
        self.complexity = ComplexityCalculator()
        self.scoring = ScoringEngine()

    def detect_bugs(
        self,
        commits: list[CommitInfo],
        max_lookback: int = 50,
    ) -> list[BugCandidate]:
        """
        Main entry point: analyze commits to find bug-introduction candidates.

        Args:
            commits: List of commits (newest first from GitPython).
            max_lookback: How far back to search for introducing commits.

        Returns:
            List of BugCandidate objects with scores.
        """
        # Sort commits by date (oldest first for linear scanning)
        sorted_commits = sorted(commits, key=lambda c: c.authored_date)
        commit_by_hash = {c.hash: c for c in sorted_commits}

        # Build file → commit history index
        file_history = self._build_file_history(sorted_commits)

        # Identify fix commits
        fix_commits = [c for c in sorted_commits if self.git.is_fix_commit(c.message)]
        logger.info("Found %d fix commits out of %d total", len(fix_commits), len(sorted_commits))

        # Cap fix commit tracing to top 60 most recent fix commits for ultra-fast execution (< 1 min for 1000+ commits)
        MAX_FIX_COMMITS = 60
        if len(fix_commits) > MAX_FIX_COMMITS:
            logger.info("Capping fix commit tracing to %d most recent fix commits (out of %d)", MAX_FIX_COMMITS, len(fix_commits))
            fix_commits = fix_commits[-MAX_FIX_COMMITS:]

        # For each fix commit, find introducing commits
        candidates: list[BugCandidate] = []
        for fix_commit in fix_commits:
            try:
                bug = self._trace_fix_to_introduction(
                    fix_commit, sorted_commits, commit_by_hash,
                    file_history, max_lookback,
                )
                if bug:
                    candidates.append(bug)
            except Exception as exc:
                logger.warning(
                    "Error tracing fix commit %s: %s", fix_commit.short_hash, exc
                )

        # Deduplicate: if multiple fixes point to the same introducing commit,
        # keep the one with the highest score
        candidates = self._deduplicate(candidates)

        logger.info("Detected %d bug-introduction candidates", len(candidates))
        return candidates

    def _build_file_history(
        self, commits: list[CommitInfo]
    ) -> dict[str, list[CommitInfo]]:
        """Build an index of file_path → list of commits that touched it."""
        history: dict[str, list[CommitInfo]] = {}
        for commit in commits:
            for f in commit.files_changed:
                history.setdefault(f, []).append(commit)
        return history

    def _trace_fix_to_introduction(
        self,
        fix_commit: CommitInfo,
        sorted_commits: list[CommitInfo],
        commit_by_hash: dict[str, CommitInfo],
        file_history: dict[str, list[CommitInfo]],
        max_lookback: int,
    ) -> BugCandidate | None:
        """Trace a fix commit back to its likely introducing commit."""
        fix_files = fix_commit.files_changed
        if not fix_files:
            return None

        # Strategy 1: Blame-based tracing (for Python files)
        introducing_hash = self._blame_trace(fix_commit, fix_files)

        # Strategy 2: File-history fallback
        if not introducing_hash:
            introducing_hash = self._history_trace(
                fix_commit, fix_files, file_history, max_lookback
            )

        if not introducing_hash or introducing_hash == fix_commit.hash:
            return None

        introducing_commit = commit_by_hash.get(introducing_hash)
        if not introducing_commit:
            return None

        # Calculate affected files (intersection)
        common_files = list(
            set(fix_commit.files_changed) & set(introducing_commit.files_changed)
        )
        if not common_files:
            common_files = fix_commit.files_changed[:5]

        # Extract affected functions
        affected_functions = self._find_affected_functions(
            introducing_commit.hash, fix_commit.hash, common_files
        )

        # Find related commits (others that touched the same files between intro and fix)
        related = self._find_related_commits(
            introducing_commit, fix_commit, common_files, file_history
        )

        # Calculate complexity delta
        complexity_before, complexity_after = self._complexity_comparison(
            introducing_commit.hash, common_files
        )

        # Score the candidate
        score_factors = self._score_candidate(
            introducing_commit, fix_commit, common_files,
            file_history, sorted_commits, complexity_before, complexity_after,
        )

        severity = self.scoring.severity_from_score(score_factors.total)

        # Generate explanation
        explanation = self._generate_explanation(
            introducing_commit, fix_commit, common_files,
            affected_functions, score_factors, complexity_before, complexity_after,
        )

        return BugCandidate(
            introducing_commit=introducing_commit,
            fix_commit=fix_commit,
            affected_files=common_files,
            affected_functions=affected_functions,
            related_commits=[c.hash for c in related],
            score_factors=score_factors,
            score=score_factors.total,
            severity=severity,
            complexity_before=complexity_before,
            complexity_after=complexity_after,
            explanation=explanation,
        )

    # ── Tracing strategies ──────────────────────────────────────

    def _blame_trace(self, fix_commit: CommitInfo, fix_files: list[str]) -> str | None:
        """Use git blame to find the commit that introduced the fixed lines."""
        # Find the parent of the fix commit to get pre-fix blame
        parent_hash = None
        try:
            commit_obj = self.git.repo.commit(fix_commit.hash)
            if commit_obj.parents:
                parent_hash = commit_obj.parents[0].hexsha
        except Exception:
            return None

        if not parent_hash:
            return None

        # Track which commits introduced the most blamed lines
        blame_counts: dict[str, int] = {}

        for file_path in fix_files[:5]:  # Limit to 5 files for performance
            try:
                blame_map = self.git.blame_lines(file_path, parent_hash)
                for _line_num, blamed_hash in blame_map.items():
                    if blamed_hash != fix_commit.hash:
                        blame_counts[blamed_hash] = blame_counts.get(blamed_hash, 0) + 1
            except Exception:
                continue

        if not blame_counts:
            return None

        # Return the commit that introduced the most lines
        return max(blame_counts, key=blame_counts.get)  # type: ignore[arg-type]

    def _history_trace(
        self,
        fix_commit: CommitInfo,
        fix_files: list[str],
        file_history: dict[str, list[CommitInfo]],
        max_lookback: int,
    ) -> str | None:
        """Fallback: find the last commit that touched the same files before the fix."""
        for file_path in fix_files:
            history = file_history.get(file_path, [])
            # Find commits before the fix
            prior = [
                c for c in history
                if c.authored_date < fix_commit.authored_date and c.hash != fix_commit.hash
            ]
            if prior:
                # Return the most recent prior commit
                prior.sort(key=lambda c: c.authored_date, reverse=True)
                return prior[0].hash

        return None

    # ── Helper methods ──────────────────────────────────────────

    def _find_affected_functions(
        self, intro_hash: str, fix_hash: str, files: list[str]
    ) -> list[str]:
        """Find functions modified in both the introducing and fix commits."""
        functions: set[str] = set()
        for file_path in files:
            if not file_path.endswith(".py"):
                continue
            for commit_hash in (intro_hash, fix_hash):
                content = self.git.get_file_content_at_commit(commit_hash, file_path)
                if content:
                    result = self.ast_analyzer.analyze_source(content, file_path)
                    for func in result.functions:
                        functions.add(func.name)
        return list(functions)

    def _find_related_commits(
        self,
        intro: CommitInfo,
        fix: CommitInfo,
        files: list[str],
        file_history: dict[str, list[CommitInfo]],
    ) -> list[CommitInfo]:
        """Find commits between introduction and fix that touched the same files."""
        related: set[str] = set()
        related_commits: list[CommitInfo] = []
        for file_path in files:
            for commit in file_history.get(file_path, []):
                if (
                    intro.authored_date < commit.authored_date < fix.authored_date
                    and commit.hash not in related
                    and commit.hash != intro.hash
                    and commit.hash != fix.hash
                ):
                    related.add(commit.hash)
                    related_commits.append(commit)
        return related_commits[:10]  # Cap at 10

    def _complexity_comparison(
        self, intro_hash: str, files: list[str]
    ) -> tuple[float, float]:
        """Compare complexity before and after the introducing commit."""
        before_total = 0.0
        after_total = 0.0
        count = 0

        for file_path in files:
            if not file_path.endswith(".py"):
                continue

            try:
                commit_obj = self.git.repo.commit(intro_hash)
                if not commit_obj.parents:
                    continue

                parent_hash = commit_obj.parents[0].hexsha
                before_content = self.git.get_file_content_at_commit(parent_hash, file_path)
                after_content = self.git.get_file_content_at_commit(intro_hash, file_path)

                if before_content and after_content:
                    delta = self.complexity.compare_complexity(before_content, after_content)
                    before_total += delta["avg_complexity_before"]
                    after_total += delta["avg_complexity_after"]
                    count += 1
            except Exception:
                continue

        if count == 0:
            return 0.0, 0.0
        return before_total / count, after_total / count

    def _score_candidate(
        self,
        intro: CommitInfo,
        fix: CommitInfo,
        common_files: list[str],
        file_history: dict[str, list[CommitInfo]],
        all_commits: list[CommitInfo],
        complexity_before: float,
        complexity_after: float,
    ) -> ScoreFactors:
        """Calculate the bug-introduction score for a candidate."""
        # Churn count for the affected files
        churn = sum(len(file_history.get(f, [])) for f in common_files)

        # Fix keyword count
        fix_kw_count = sum(
            1 for kw in ("fix", "bug", "patch", "error", "crash", "cve")
            if kw in fix.message.lower()
        )

        # Code smells in the introducing commit
        smell_count = 0
        for file_path in common_files:
            if file_path.endswith(".py"):
                content = self.git.get_file_content_at_commit(intro.hash, file_path)
                if content:
                    result = self.ast_analyzer.analyze_source(content, file_path)
                    smell_count += len(result.code_smells)

        # Author experience with the file
        author_commits = sum(
            1 for c in all_commits
            if c.author_email == intro.author_email
            and any(f in c.files_changed for f in common_files)
        )
        total_file_commits = max(1, churn)

        # Exception handling check
        exception_removed = self._check_exception_removal(intro.hash, common_files)

        # Days to fix
        days_to_fix = (fix.authored_date - intro.authored_date).total_seconds() / 86400

        complexity_delta = complexity_after - complexity_before

        return self.scoring.calculate_score(
            has_subsequent_fix=True,
            complexity_delta=complexity_delta,
            file_churn_count=churn,
            total_commits=len(all_commits),
            fix_keyword_count=fix_kw_count,
            code_smell_count=smell_count,
            author_file_commits=author_commits,
            total_file_commits=total_file_commits,
            exception_handling_removed=exception_removed,
            days_to_fix=days_to_fix,
        )

    def _check_exception_removal(self, commit_hash: str, files: list[str]) -> bool:
        """Check if a commit removed exception handling from Python files."""
        try:
            commit_obj = self.git.repo.commit(commit_hash)
            if not commit_obj.parents:
                return False
            parent_hash = commit_obj.parents[0].hexsha
        except Exception:
            return False

        for file_path in files:
            if not file_path.endswith(".py"):
                continue
            before = self.git.get_file_content_at_commit(parent_hash, file_path)
            after = self.git.get_file_content_at_commit(commit_hash, file_path)
            if before and after:
                if before.count("except") > after.count("except"):
                    return True
                if before.count("try:") > after.count("try:"):
                    return True
        return False

    def _generate_explanation(
        self,
        intro: CommitInfo,
        fix: CommitInfo,
        files: list[str],
        functions: list[str],
        factors: ScoreFactors,
        complexity_before: float,
        complexity_after: float,
    ) -> str:
        """Generate a human-readable explanation of why a commit was flagged."""
        days = (fix.authored_date - intro.authored_date).total_seconds() / 86400
        parts: list[str] = []

        # Opening
        file_desc = ", ".join(files[:3])
        if len(files) > 3:
            file_desc += f" and {len(files) - 3} more"
        parts.append(
            f"Commit {intro.short_hash} modified {file_desc}."
        )

        # Functions
        if functions:
            func_list = ", ".join(functions[:5])
            parts.append(f"Affected functions: {func_list}.")

        # Fix relationship
        parts.append(
            f"The same code was modified {days:.0f} days later in commit "
            f"{fix.short_hash}, which appears to be a bug fix "
            f"(\"{fix.message[:80]}...\")." if len(fix.message) > 80
            else f"The same code was modified {days:.0f} days later in commit "
            f"{fix.short_hash}, which appears to be a bug fix "
            f"(\"{fix.message}\")."
        )

        # Complexity
        if complexity_after > complexity_before:
            delta = complexity_after - complexity_before
            parts.append(
                f"The original change increased average complexity by "
                f"{delta:.1f} (from {complexity_before:.1f} to {complexity_after:.1f})."
            )

        # Exception handling
        if factors.exception_handling > 0:
            parts.append("The commit removed or weakened exception handling.")

        # Score breakdown
        parts.append(
            f"Bug Introduction Probability: {factors.total:.0f}/100 "
            f"(fix proximity: {factors.fix_proximity:.0f}, "
            f"complexity: {factors.complexity_increase:.0f}, "
            f"churn: {factors.churn_rate:.0f})."
        )

        return " ".join(parts)

    def _deduplicate(self, candidates: list[BugCandidate]) -> list[BugCandidate]:
        """If multiple fix commits point to the same intro, keep highest score."""
        seen: dict[str, BugCandidate] = {}
        for c in candidates:
            key = c.introducing_commit.hash
            if key not in seen or c.score > seen[key].score:
                seen[key] = c
        return list(seen.values())
