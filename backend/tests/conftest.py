"""Pytest fixtures for Bug Archaeologist tests."""

import os
import tempfile
from datetime import datetime, timezone

import git
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database.base import Base
from app.main import app
from app.database.session import get_session


# ── In-memory SQLite for tests ───────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_factory = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Yield a test DB session with tables created."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Yield an httpx AsyncClient wired to the test DB."""
    async def _override_session():
        yield db_session

    app.dependency_overrides[get_session] = _override_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Temporary Git repository fixture ─────────────────────────────

@pytest.fixture
def temp_git_repo():
    """
    Create a temporary Git repo with sample commits for testing.
    Includes intentional 'bug' and 'fix' commits.
    """
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        repo = git.Repo.init(tmpdir)

        # Configure git user
        repo.config_writer().set_value("user", "name", "Test Author").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # Commit 1: Initial file
        main_file = os.path.join(tmpdir, "main.py")
        with open(main_file, "w") as f:
            f.write(
                'def process_data(data):\n'
                '    """Process the input data safely."""\n'
                '    try:\n'
                '        result = data["key"]\n'
                '        return result\n'
                '    except KeyError:\n'
                '        return None\n'
            )
        repo.index.add(["main.py"])
        repo.index.commit("Initial commit: add data processor")

        # Commit 2: Bug-introducing change (removes error handling)
        with open(main_file, "w") as f:
            f.write(
                'def process_data(data):\n'
                '    """Process the input data."""\n'
                '    result = data["key"]\n'
                '    if result > 0:\n'
                '        if result > 100:\n'
                '            if result > 1000:\n'
                '                return "huge"\n'
                '            return "large"\n'
                '        return "small"\n'
                '    return result\n'
            )
        repo.index.add(["main.py"])
        repo.index.commit("Refactor: simplify data processor")

        # Commit 3: Add another file
        util_file = os.path.join(tmpdir, "utils.py")
        with open(util_file, "w") as f:
            f.write(
                'def validate(value):\n'
                '    """Validate input value."""\n'
                '    if value is None:\n'
                '        raise ValueError("Value cannot be None")\n'
                '    return True\n'
            )
        repo.index.add(["utils.py"])
        repo.index.commit("Add validation utility")

        # Commit 4: Fix the bug
        with open(main_file, "w") as f:
            f.write(
                'def process_data(data):\n'
                '    """Process the input data safely."""\n'
                '    try:\n'
                '        result = data["key"]\n'
                '        if result > 0:\n'
                '            return "positive"\n'
                '        return result\n'
                '    except KeyError:\n'
                '        return None\n'
                '    except TypeError:\n'
                '        return None\n'
            )
        repo.index.add(["main.py"])
        repo.index.commit("Fix: restore error handling in data processor")

        repo.close()
        yield tmpdir
