"""Bug detector tests."""

import pytest
from app.analyzers.git_analyzer import GitAnalyzer
from app.analyzers.bug_detector import BugDetector


def test_detect_bugs(temp_git_repo):
    """Bug detector finds candidates in the test repo."""
    git_analyzer = GitAnalyzer(temp_git_repo)
    commits = git_analyzer.get_commits()
    detector = BugDetector(git_analyzer)
    candidates = detector.detect_bugs(commits)

    # Should find at least one candidate (the removed error handling)
    assert len(candidates) >= 1


def test_bug_has_score(temp_git_repo):
    """Detected bugs have a non-zero score."""
    git_analyzer = GitAnalyzer(temp_git_repo)
    commits = git_analyzer.get_commits()
    detector = BugDetector(git_analyzer)
    candidates = detector.detect_bugs(commits)

    for c in candidates:
        assert c.score > 0
        assert c.severity in ("low", "medium", "high", "critical")


def test_bug_has_explanation(temp_git_repo):
    """Detected bugs have explanations."""
    git_analyzer = GitAnalyzer(temp_git_repo)
    commits = git_analyzer.get_commits()
    detector = BugDetector(git_analyzer)
    candidates = detector.detect_bugs(commits)

    for c in candidates:
        assert c.explanation
        assert len(c.explanation) > 20


def test_bug_has_affected_files(temp_git_repo):
    """Detected bugs list affected files."""
    git_analyzer = GitAnalyzer(temp_git_repo)
    commits = git_analyzer.get_commits()
    detector = BugDetector(git_analyzer)
    candidates = detector.detect_bugs(commits)

    for c in candidates:
        assert len(c.affected_files) > 0


def test_bug_timeline(temp_git_repo):
    """Introduction date is before fix date."""
    git_analyzer = GitAnalyzer(temp_git_repo)
    commits = git_analyzer.get_commits()
    detector = BugDetector(git_analyzer)
    candidates = detector.detect_bugs(commits)

    for c in candidates:
        assert c.introducing_commit.authored_date <= c.fix_commit.authored_date
