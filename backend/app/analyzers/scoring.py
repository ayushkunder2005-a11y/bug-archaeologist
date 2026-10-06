"""Bug-introduction scoring engine — weighted heuristic scoring."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoreFactors:
    """Individual factors contributing to the bug-introduction score."""
    fix_proximity: float = 0.0          # 0-25  : Fix commit found for same code?
    complexity_increase: float = 0.0    # 0-20  : Did complexity increase?
    churn_rate: float = 0.0             # 0-15  : How often is this file changed?
    fix_keyword_strength: float = 0.0   # 0-15  : How strong is the fix-commit signal?
    code_smell_count: float = 0.0       # 0-10  : Code smells introduced?
    author_experience: float = 0.0      # 0-5   : Author familiarity with this code?
    exception_handling: float = 0.0     # 0-5   : Exception handlers removed?
    time_to_fix: float = 0.0           # 0-5   : Short fix → obvious bug?

    @property
    def total(self) -> float:
        return min(100.0, max(0.0,
            self.fix_proximity
            + self.complexity_increase
            + self.churn_rate
            + self.fix_keyword_strength
            + self.code_smell_count
            + self.author_experience
            + self.exception_handling
            + self.time_to_fix
        ))


class ScoringEngine:
    """
    Calculates Bug Introduction Probability scores (0–100).

    Each factor contributes a weighted amount to the total score.
    The scoring is probabilistic — it estimates *likelihood*, not certainty.
    """

    def calculate_score(
        self,
        has_subsequent_fix: bool,
        complexity_delta: float,
        file_churn_count: int,
        total_commits: int,
        fix_keyword_count: int,
        code_smell_count: int,
        author_file_commits: int,
        total_file_commits: int,
        exception_handling_removed: bool,
        days_to_fix: float | None,
    ) -> ScoreFactors:
        """Compute all scoring factors and return the result."""
        factors = ScoreFactors()

        # ── Factor 1: Fix proximity (0–25) ──────────────────────
        if has_subsequent_fix:
            factors.fix_proximity = 25.0
        else:
            factors.fix_proximity = 0.0

        # ── Factor 2: Complexity increase (0–20) ────────────────
        if complexity_delta > 0:
            # Scale: +1 complexity → 5 pts, +4 → 20 pts (capped)
            factors.complexity_increase = min(20.0, complexity_delta * 5.0)

        # ── Factor 3: Churn rate (0–15) ─────────────────────────
        if total_commits > 0:
            churn_ratio = file_churn_count / total_commits
            factors.churn_rate = min(15.0, churn_ratio * 150.0)

        # ── Factor 4: Fix keyword strength (0–15) ──────────────
        # More fix-related keywords = stronger signal
        factors.fix_keyword_strength = min(15.0, fix_keyword_count * 5.0)

        # ── Factor 5: Code smells (0–10) ────────────────────────
        factors.code_smell_count = min(10.0, code_smell_count * 2.5)

        # ── Factor 6: Author experience (0–5) ──────────────────
        if total_file_commits > 0:
            experience_ratio = author_file_commits / total_file_commits
            # Less experience = higher risk
            factors.author_experience = max(0.0, 5.0 * (1.0 - experience_ratio))

        # ── Factor 7: Exception handling (0–5) ──────────────────
        if exception_handling_removed:
            factors.exception_handling = 5.0

        # ── Factor 8: Time to fix (0–5) ─────────────────────────
        if days_to_fix is not None and days_to_fix > 0:
            # Very quick fix (<3 days) suggests obvious bug
            if days_to_fix < 3:
                factors.time_to_fix = 5.0
            elif days_to_fix < 7:
                factors.time_to_fix = 3.0
            elif days_to_fix < 30:
                factors.time_to_fix = 1.0

        return factors

    @staticmethod
    def severity_from_score(score: float) -> str:
        """Map a 0–100 score to a severity label."""
        if score >= 75:
            return "critical"
        elif score >= 55:
            return "high"
        elif score >= 35:
            return "medium"
        else:
            return "low"
