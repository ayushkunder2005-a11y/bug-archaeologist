#!/usr/bin/env python3
"""
Demo data seeder for Bug Archaeologist.

Creates a temporary Git repository with realistic commit history
including intentional bugs and fixes, then runs the full analysis
pipeline to populate the database for demonstration purposes.
"""

import asyncio
import os
import sys
import tempfile
import time

import git  # type: ignore

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.database.mongodb import MongoDBManager  # type: ignore
from app.services.repository_service import RepositoryService  # type: ignore
from app.services.analysis_service import AnalysisService  # type: ignore


def create_demo_repo(base_dir: str) -> str:
    """Create a demo Git repository with realistic history."""
    repo_dir = os.path.join(base_dir, "demo-project")
    os.makedirs(repo_dir, exist_ok=True)
    repo = git.Repo.init(repo_dir)

    # Configure git
    repo.config_writer().set_value("user", "name", "Alice Chen").release()
    repo.config_writer().set_value("user", "email", "alice@example.com").release()

    # ── Phase 1: Initial project structure ───────────────────────

    # auth.py
    _write_file(repo_dir, "src/auth.py", '''"""Authentication module."""

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    if not username or not password:
        raise ValueError("Username and password are required")
    try:
        user = lookup_user(username)
        if user and verify_password(password, user["hash"]):
            return create_session(user)
        return None
    except Exception as e:
        log_error(f"Auth failed: {e}")
        return None

def create_session(user):
    """Create a new session for the user."""
    return {"user_id": user["id"], "token": generate_token(), "valid": True}

def verify_password(password, stored_hash):
    """Verify password against stored hash."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def lookup_user(username):
    """Look up user by username."""
    return None  # Placeholder

def generate_token():
    """Generate a session token."""
    import secrets
    return secrets.token_urlsafe(32)

def log_error(msg):
    """Log error message."""
    print(f"ERROR: {msg}")
''')

    # data_processor.py
    _write_file(repo_dir, "src/data_processor.py", '''"""Data processing pipeline."""

def process_records(records):
    """Process a list of records safely."""
    if not records:
        return []
    results = []
    for record in records:
        try:
            processed = transform(record)
            if validate(processed):
                results.append(processed)
        except ValueError as e:
            log_warning(f"Skipping invalid record: {e}")
    return results

def transform(record):
    """Transform a single record."""
    return {
        "id": record.get("id"),
        "value": record.get("value", 0) * 2,
        "status": "processed"
    }

def validate(record):
    """Validate a processed record."""
    if record.get("id") is None:
        raise ValueError("Missing ID")
    if record.get("value") is None:
        return False
    return True

def log_warning(msg):
    """Log warning message."""
    print(f"WARNING: {msg}")
''')

    # api.py
    _write_file(repo_dir, "src/api.py", '''"""API endpoint handlers."""

def handle_request(request):
    """Handle an incoming API request."""
    try:
        method = request.get("method", "GET")
        path = request.get("path", "/")

        if method == "GET":
            return handle_get(path, request)
        elif method == "POST":
            return handle_post(path, request)
        else:
            return {"status": 405, "error": "Method not allowed"}
    except Exception as e:
        return {"status": 500, "error": str(e)}

def handle_get(path, request):
    """Handle GET requests."""
    if path == "/health":
        return {"status": 200, "data": "ok"}
    elif path == "/users":
        return {"status": 200, "data": []}
    return {"status": 404, "error": "Not found"}

def handle_post(path, request):
    """Handle POST requests."""
    body = request.get("body", {})
    if not body:
        return {"status": 400, "error": "Empty body"}
    return {"status": 201, "data": body}
''')

    # utils.py
    _write_file(repo_dir, "src/utils.py", '''"""Utility functions."""

def format_date(timestamp):
    """Format a timestamp into a readable date string."""
    from datetime import datetime
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, TypeError):
        return "Invalid date"

def calculate_stats(values):
    """Calculate basic statistics for a list of values."""
    if not values:
        return {"count": 0, "mean": 0, "min": 0, "max": 0}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }

def sanitize_input(text):
    """Sanitize user input."""
    if not isinstance(text, str):
        return ""
    return text.strip().replace("<", "&lt;").replace(">", "&gt;")
''')

    repo.index.add(["src/auth.py", "src/data_processor.py", "src/api.py", "src/utils.py"])
    repo.index.commit("Initial project structure with auth, data processing, API, and utilities")

    # ── Phase 2: Bug-introducing commits ─────────────────────────

    # Bug 1: Remove error handling from auth
    repo.config_writer().set_value("user", "name", "Bob Smith").release()
    repo.config_writer().set_value("user", "email", "bob@example.com").release()

    _write_file(repo_dir, "src/auth.py", '''"""Authentication module."""

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    user = lookup_user(username)
    if user and verify_password(password, user["hash"]):
        return create_session(user)
    return None

def create_session(user):
    """Create a new session for the user."""
    return {"user_id": user["id"], "token": generate_token(), "valid": True}

def verify_password(password, stored_hash):
    """Verify password against stored hash."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def lookup_user(username):
    """Look up user by username."""
    return None

def generate_token():
    """Generate a session token."""
    import secrets
    return secrets.token_urlsafe(32)

def log_error(msg):
    """Log error message."""
    print(f"ERROR: {msg}")
''')
    repo.index.add(["src/auth.py"])
    repo.index.commit("Refactor authentication to simplify flow")

    # Bug 2: Introduce complex and error-prone data processing
    repo.config_writer().set_value("user", "name", "Carol Davis").release()
    repo.config_writer().set_value("user", "email", "carol@example.com").release()

    _write_file(repo_dir, "src/data_processor.py", '''"""Data processing pipeline."""

def process_records(records):
    """Process a list of records."""
    results = []
    for record in records:
        if record.get("type") == "A":
            if record.get("value") > 0:
                if record.get("status") == "active":
                    if record.get("priority") > 5:
                        results.append({"id": record["id"], "value": record["value"] * 3, "flag": True})
                    else:
                        results.append({"id": record["id"], "value": record["value"] * 2, "flag": False})
                else:
                    results.append({"id": record["id"], "value": 0, "flag": False})
            else:
                results.append({"id": record["id"], "value": -1, "flag": False})
        elif record.get("type") == "B":
            if record.get("value") > 100:
                results.append({"id": record["id"], "value": record["value"], "flag": True})
            else:
                results.append({"id": record["id"], "value": record["value"] // 2, "flag": False})
        else:
            results.append({"id": record["id"], "value": 0, "flag": False})
    return results

def transform(record):
    """Transform a single record."""
    return {
        "id": record["id"],
        "value": record["value"] * 2,
        "status": "processed"
    }

def validate(record):
    """Validate a processed record."""
    return record["id"] is not None
''')
    repo.index.add(["src/data_processor.py"])
    repo.index.commit("Optimize data processing for different record types")

    # Bug 3: Weak input validation in API
    repo.config_writer().set_value("user", "name", "Bob Smith").release()
    repo.config_writer().set_value("user", "email", "bob@example.com").release()

    _write_file(repo_dir, "src/api.py", '''"""API endpoint handlers."""

def handle_request(request):
    """Handle an incoming API request."""
    method = request["method"]
    path = request["path"]

    if method == "GET":
        return handle_get(path, request)
    elif method == "POST":
        return handle_post(path, request)
    return {"status": 405, "error": "Method not allowed"}

def handle_get(path, request):
    """Handle GET requests."""
    if path == "/health":
        return {"status": 200, "data": "ok"}
    elif path == "/users":
        return {"status": 200, "data": []}
    return {"status": 404, "error": "Not found"}

def handle_post(path, request):
    """Handle POST requests."""
    body = request["body"]
    return {"status": 201, "data": body}
''')
    repo.index.add(["src/api.py"])
    repo.index.commit("Streamline API request handling")

    # ── Phase 3: Feature additions ───────────────────────────────

    repo.config_writer().set_value("user", "name", "Alice Chen").release()
    repo.config_writer().set_value("user", "email", "alice@example.com").release()

    _write_file(repo_dir, "src/cache.py", '''"""Simple caching layer."""

class Cache:
    """In-memory cache with TTL support."""

    def __init__(self, max_size=1000):
        self._store = {}
        self._max_size = max_size

    def get(self, key):
        """Get a value from the cache."""
        entry = self._store.get(key)
        if entry is None:
            return None
        return entry["value"]

    def set(self, key, value, ttl=3600):
        """Set a value in the cache."""
        if len(self._store) >= self._max_size:
            self._evict()
        self._store[key] = {"value": value, "ttl": ttl}

    def _evict(self):
        """Evict oldest entry."""
        if self._store:
            oldest = next(iter(self._store))
            del self._store[oldest]

    def clear(self):
        """Clear the entire cache."""
        self._store.clear()
''')
    repo.index.add(["src/cache.py"])
    repo.index.commit("Add in-memory caching layer")

    _write_file(repo_dir, "src/logger.py", '''"""Logging configuration."""

import logging

def setup_logger(name, level="INFO"):
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    return logger
''')
    repo.index.add(["src/logger.py"])
    repo.index.commit("Add structured logging module")

    # ── Phase 4: Bug fixes ───────────────────────────────────────

    repo.config_writer().set_value("user", "name", "Alice Chen").release()
    repo.config_writer().set_value("user", "email", "alice@example.com").release()

    _write_file(repo_dir, "src/auth.py", '''"""Authentication module."""

def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    if not username or not password:
        raise ValueError("Username and password are required")
    try:
        user = lookup_user(username)
        if user and verify_password(password, user["hash"]):
            return create_session(user)
        return None
    except Exception as e:
        log_error(f"Authentication failed for {username}: {e}")
        return None

def create_session(user):
    """Create a new session for the user."""
    if not user or "id" not in user:
        raise ValueError("Invalid user object")
    return {"user_id": user["id"], "token": generate_token(), "valid": True}

def verify_password(password, stored_hash):
    """Verify password against stored hash."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest() == stored_hash

def lookup_user(username):
    """Look up user by username."""
    return None

def generate_token():
    """Generate a session token."""
    import secrets
    return secrets.token_urlsafe(32)

def log_error(msg):
    """Log error message."""
    print(f"ERROR: {msg}")
''')
    repo.index.add(["src/auth.py"])
    repo.index.commit("Fix: restore error handling and input validation in authentication")

    repo.config_writer().set_value("user", "name", "Carol Davis").release()
    repo.config_writer().set_value("user", "email", "carol@example.com").release()

    _write_file(repo_dir, "src/data_processor.py", '''"""Data processing pipeline."""

def process_records(records):
    """Process a list of records safely."""
    if not records:
        return []
    results = []
    for record in records:
        try:
            processed = transform(record)
            if validate(processed):
                results.append(processed)
        except (ValueError, KeyError, TypeError) as e:
            log_warning(f"Skipping invalid record: {e}")
    return results

def transform(record):
    """Transform a single record."""
    record_type = record.get("type", "default")
    value = record.get("value", 0)
    multiplier = {"A": 3, "B": 1}.get(record_type, 2)
    return {
        "id": record.get("id"),
        "value": value * multiplier,
        "status": "processed",
        "type": record_type,
    }

def validate(record):
    """Validate a processed record."""
    if record.get("id") is None:
        raise ValueError("Missing ID")
    if not isinstance(record.get("value"), (int, float)):
        return False
    return True

def log_warning(msg):
    """Log warning message."""
    print(f"WARNING: {msg}")
''')
    repo.index.add(["src/data_processor.py"])
    repo.index.commit("Fix: simplify data processing and restore error handling")

    repo.config_writer().set_value("user", "name", "Bob Smith").release()
    repo.config_writer().set_value("user", "email", "bob@example.com").release()

    _write_file(repo_dir, "src/api.py", '''"""API endpoint handlers."""

def handle_request(request):
    """Handle an incoming API request."""
    try:
        method = request.get("method", "GET")
        path = request.get("path", "/")

        if method == "GET":
            return handle_get(path, request)
        elif method == "POST":
            return handle_post(path, request)
        else:
            return {"status": 405, "error": "Method not allowed"}
    except KeyError as e:
        return {"status": 400, "error": f"Missing field: {e}"}
    except Exception as e:
        return {"status": 500, "error": str(e)}

def handle_get(path, request):
    """Handle GET requests."""
    if path == "/health":
        return {"status": 200, "data": "ok"}
    elif path == "/users":
        return {"status": 200, "data": []}
    return {"status": 404, "error": "Not found"}

def handle_post(path, request):
    """Handle POST requests."""
    body = request.get("body")
    if not body:
        return {"status": 400, "error": "Empty request body"}
    return {"status": 201, "data": body}
''')
    repo.index.add(["src/api.py"])
    repo.index.commit("Fix: restore error handling in API request handler")

    # ── Phase 5: More feature work ───────────────────────────────

    repo.config_writer().set_value("user", "name", "Alice Chen").release()
    repo.config_writer().set_value("user", "email", "alice@example.com").release()

    _write_file(repo_dir, "src/middleware.py", '''"""Request middleware."""

def rate_limiter(max_requests=100, window_seconds=60):
    """Simple rate limiting decorator."""
    from collections import defaultdict
    import time
    counters = defaultdict(list)

    def decorator(func):
        def wrapper(request, *args, **kwargs):
            ip = request.get("ip", "unknown")
            now = time.time()
            counters[ip] = [t for t in counters[ip] if now - t < window_seconds]
            if len(counters[ip]) >= max_requests:
                return {"status": 429, "error": "Rate limit exceeded"}
            counters[ip].append(now)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator

def cors_headers(response):
    """Add CORS headers to response."""
    response["headers"] = response.get("headers", {})
    response["headers"]["Access-Control-Allow-Origin"] = "*"
    return response
''')
    repo.index.add(["src/middleware.py"])
    repo.index.commit("Add rate limiting middleware and CORS support")

    _write_file(repo_dir, "tests/test_auth.py", '''"""Tests for authentication module."""

def test_authenticate_missing_credentials():
    """Should raise ValueError for missing credentials."""
    from src.auth import authenticate_user
    try:
        authenticate_user("", "password")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_authenticate_invalid_user():
    """Should return None for invalid user."""
    from src.auth import authenticate_user
    result = authenticate_user("nonexistent", "password")
    assert result is None
''')
    repo.index.add(["tests/test_auth.py"])
    repo.index.commit("Add authentication unit tests")

    print(f"[SUCCESS] Created demo repository at {repo_dir}")
    print(f"  Commits: {len(list(repo.iter_commits()))}")
    return repo_dir


def _write_file(repo_dir: str, path: str, content: str) -> None:
    """Write content to a file, creating directories as needed."""
    full_path = os.path.join(repo_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)


async def seed_demo():
    """Create demo repo and run analysis into MongoDB."""
    print("Bug Archaeologist -- Demo Seeder (MongoDB)")
    print("=" * 50)

    await MongoDBManager.init_indexes()
    db = MongoDBManager.get_db()

    # Create demo repo
    demo_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "repos")
    os.makedirs(demo_dir, exist_ok=True)
    repo_path = create_demo_repo(demo_dir)

    # Run analysis
    repo_svc = RepositoryService(db)
    repo = await repo_svc.create(local_path=repo_path)

    print(f"\nRunning analysis on {repo.name}...")
    start = time.time()

    analysis_svc = AnalysisService(db)
    await analysis_svc.run_analysis(repo, max_commits=500)

    elapsed = time.time() - start
    print(f"\nAnalysis complete in {elapsed:.1f}s")
    print(f"   Repository: {repo.name}")
    print(f"   Status:     {repo.status}")
    print(f"   Commits:    {repo.total_commits}")
    print(f"   Bugs found: {repo.total_bugs_detected}")
    print(f"   Health:     {repo.health_score:.0f}/100")
    print(f"   Repo ID:    {repo.id}")
    print(f"\nMongoDB Seeded! Start the backend and visit http://localhost:8000/docs")

    await MongoDBManager.close()


if __name__ == "__main__":
    asyncio.run(seed_demo())
