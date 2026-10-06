"""Git analyzer tests."""

import pytest
from app.analyzers.git_analyzer import GitAnalyzer


def test_open_repo(temp_git_repo):
    """GitAnalyzer opens a valid repo."""
    analyzer = GitAnalyzer(temp_git_repo)
    assert analyzer.repo is not None


def test_get_commits(temp_git_repo):
    """Extracts correct number of commits."""
    analyzer = GitAnalyzer(temp_git_repo)
    commits = analyzer.get_commits()
    assert len(commits) == 4


def test_commit_fields(temp_git_repo):
    """Commits have required fields."""
    analyzer = GitAnalyzer(temp_git_repo)
    commits = analyzer.get_commits()
    for c in commits:
        assert c.hash
        assert len(c.hash) == 40
        assert c.short_hash == c.hash[:8]
        assert c.author_name
        assert c.authored_date


def test_fix_commit_detection(temp_git_repo):
    """Detects the fix commit by keyword."""
    analyzer = GitAnalyzer(temp_git_repo)
    commits = analyzer.get_commits()
    fix_commits = [c for c in commits if analyzer.is_fix_commit(c.message)]
    assert len(fix_commits) >= 1
    assert any("Fix" in c.message or "fix" in c.message for c in fix_commits)


def test_not_fix_commit():
    """Non-fix messages should not be flagged."""
    analyzer_cls = GitAnalyzer.__new__(GitAnalyzer)
    # Test the pattern directly
    import re
    from app.config import settings
    pattern = re.compile(
        r"\b(" + "|".join(settings.FIX_KEYWORDS) + r")\b",
        re.IGNORECASE,
    )
    assert not pattern.search("Add new feature for dashboard")
    assert not pattern.search("Refactor code structure")
    assert pattern.search("Fix: null pointer exception")
    assert pattern.search("bug in authentication module")


def test_get_python_files(temp_git_repo):
    """Lists Python files in the repo."""
    analyzer = GitAnalyzer(temp_git_repo)
    py_files = analyzer.get_python_files()
    assert "main.py" in py_files
    assert "utils.py" in py_files


def test_get_file_content(temp_git_repo):
    """Retrieves file content at a commit."""
    analyzer = GitAnalyzer(temp_git_repo)
    commits = analyzer.get_commits()
    content = analyzer.get_file_content_at_commit(commits[0].hash, "main.py")
    assert content is not None
    assert "def process_data" in content


def test_get_file_content_nonexistent(temp_git_repo):
    """Returns None for nonexistent files."""
    analyzer = GitAnalyzer(temp_git_repo)
    commits = analyzer.get_commits()
    content = analyzer.get_file_content_at_commit(commits[0].hash, "nonexistent.py")
    assert content is None
