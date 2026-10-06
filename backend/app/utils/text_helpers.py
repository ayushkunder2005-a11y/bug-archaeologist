"""Human-readable explanation generation for analysis results."""

from __future__ import annotations


def generate_health_explanation(health_score: float, total_bugs: int, total_commits: int) -> str:
    """Generate a text explanation of the repository health score."""
    ratio = total_bugs / max(total_commits, 1)

    if health_score >= 85:
        quality = "excellent"
        detail = "very few bug-introducing patterns were detected"
    elif health_score >= 70:
        quality = "good"
        detail = "some bug-introducing patterns were found but the overall quality is solid"
    elif health_score >= 50:
        quality = "moderate"
        detail = "a noticeable number of commits show bug-introducing patterns"
    elif health_score >= 30:
        quality = "concerning"
        detail = "many commits show patterns associated with bug introduction"
    else:
        quality = "poor"
        detail = "a high proportion of commits exhibit bug-introducing patterns"

    return (
        f"Repository health is {quality} ({health_score:.0f}/100). "
        f"Out of {total_commits} analyzed commits, {total_bugs} showed "
        f"probable bug-introduction patterns ({ratio:.1%} ratio). "
        f"Overall, {detail}."
    )


def severity_description(severity: str) -> str:
    """Return a human-readable description for a severity level."""
    descriptions = {
        "critical": "Critical — very high confidence that this commit introduced a bug",
        "high": "High — strong signals of bug introduction detected",
        "medium": "Medium — moderate probability of bug introduction",
        "low": "Low — weak signals, possibly a false positive",
    }
    return descriptions.get(severity, "Unknown severity")
