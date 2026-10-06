"""API endpoint tests."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint returns 200 with app info."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Bug Archaeologist" in data["app"]


@pytest.mark.asyncio
async def test_root(client):
    """Root endpoint returns app metadata."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_list_repositories_empty(client):
    """List repositories returns empty when no repos exist."""
    response = await client.get("/api/repositories")
    assert response.status_code == 200
    data = response.json()
    assert data["repositories"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_repository_with_local_path(client, temp_git_repo):
    """Create repository with a local path starts analysis."""
    response = await client.post("/api/repositories", json={
        "local_path": temp_git_repo,
        "max_commits": 100,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] in ("pending", "analyzing")
    assert data["id"]


@pytest.mark.asyncio
async def test_create_repository_no_input(client):
    """Create repository with no URL or path fails validation."""
    response = await client.post("/api/repositories", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_repository(client):
    """Getting a non-existent repo returns 404."""
    response = await client.get("/api/repositories/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_search_empty(client):
    """Search with no params returns empty results."""
    response = await client.get("/api/search")
    assert response.status_code == 200
    data = response.json()
    assert data["total_commits"] == 0
    assert data["total_bugs"] == 0
