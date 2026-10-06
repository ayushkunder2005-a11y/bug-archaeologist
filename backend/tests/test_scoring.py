"""Scoring engine tests."""

import pytest
from app.analyzers.scoring import ScoringEngine, ScoreFactors


@pytest.fixture
def engine():
    return ScoringEngine()


def test_max_score_all_factors(engine):
    """All maximum factors produce a high score."""
    factors = engine.calculate_score(
        has_subsequent_fix=True,
        complexity_delta=5.0,
        file_churn_count=50,
        total_commits=100,
        fix_keyword_count=3,
        code_smell_count=5,
        author_file_commits=1,
        total_file_commits=50,
        exception_handling_removed=True,
        days_to_fix=1.0,
    )
    assert factors.total >= 70


def test_min_score_no_factors(engine):
    """No risk factors produce a low score."""
    factors = engine.calculate_score(
        has_subsequent_fix=False,
        complexity_delta=0.0,
        file_churn_count=0,
        total_commits=100,
        fix_keyword_count=0,
        code_smell_count=0,
        author_file_commits=50,
        total_file_commits=50,
        exception_handling_removed=False,
        days_to_fix=None,
    )
    assert factors.total < 10


def test_fix_proximity_weight(engine):
    """Fix proximity contributes 25 points."""
    with_fix = engine.calculate_score(
        has_subsequent_fix=True,
        complexity_delta=0, file_churn_count=0, total_commits=1,
        fix_keyword_count=0, code_smell_count=0,
        author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=None,
    )
    without_fix = engine.calculate_score(
        has_subsequent_fix=False,
        complexity_delta=0, file_churn_count=0, total_commits=1,
        fix_keyword_count=0, code_smell_count=0,
        author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=None,
    )
    assert with_fix.total - without_fix.total == 25.0


def test_complexity_delta_scaling(engine):
    """Complexity delta scales up to 20 points."""
    low = engine.calculate_score(
        has_subsequent_fix=False, complexity_delta=1.0,
        file_churn_count=0, total_commits=1, fix_keyword_count=0,
        code_smell_count=0, author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=None,
    )
    high = engine.calculate_score(
        has_subsequent_fix=False, complexity_delta=10.0,
        file_churn_count=0, total_commits=1, fix_keyword_count=0,
        code_smell_count=0, author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=None,
    )
    assert high.complexity_increase >= low.complexity_increase
    assert high.complexity_increase <= 20.0


def test_severity_mapping(engine):
    """Score-to-severity mapping is correct."""
    assert ScoringEngine.severity_from_score(80) == "critical"
    assert ScoringEngine.severity_from_score(60) == "high"
    assert ScoringEngine.severity_from_score(40) == "medium"
    assert ScoringEngine.severity_from_score(20) == "low"


def test_score_capped_at_100(engine):
    """Score never exceeds 100."""
    factors = engine.calculate_score(
        has_subsequent_fix=True,
        complexity_delta=100.0,
        file_churn_count=1000,
        total_commits=10,
        fix_keyword_count=10,
        code_smell_count=20,
        author_file_commits=0,
        total_file_commits=100,
        exception_handling_removed=True,
        days_to_fix=0.5,
    )
    assert factors.total <= 100.0


def test_time_to_fix_scoring(engine):
    """Quick fixes score higher."""
    quick = engine.calculate_score(
        has_subsequent_fix=False, complexity_delta=0,
        file_churn_count=0, total_commits=1, fix_keyword_count=0,
        code_smell_count=0, author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=1.0,
    )
    slow = engine.calculate_score(
        has_subsequent_fix=False, complexity_delta=0,
        file_churn_count=0, total_commits=1, fix_keyword_count=0,
        code_smell_count=0, author_file_commits=1, total_file_commits=1,
        exception_handling_removed=False, days_to_fix=60.0,
    )
    assert quick.time_to_fix > slow.time_to_fix
