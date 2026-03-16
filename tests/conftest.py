"""Shared fixtures for webseed integration tests."""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from typing import Any

import pytest
from starlette.testclient import TestClient

from webseed.api.app import create_app
from webseed.db.store import PostgresStore
from webseed.models import BusinessData
from webseed.storage import LocalFileStorage

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://webseed:webseed@localhost:5432/webseed")
API_KEY = os.environ.get("WEBSEED_API_KEY", "test-key-123")

# Track test place_ids for cleanup
_test_place_ids: list[str] = []


def _unique_place_id() -> str:
    pid = f"TEST_PLACE_{uuid.uuid4().hex[:12]}"
    _test_place_ids.append(pid)
    return pid


def make_biz(**overrides: Any) -> BusinessData:
    """Factory for BusinessData with unique TEST_PLACE_xxx place_ids."""
    place_id = overrides.pop("place_id", _unique_place_id())
    defaults: dict[str, Any] = {
        "name": f"Test Biz {place_id[-6:]}",
        "place_id": place_id,
        "address": "Via Roma 1, Milano",
        "phone": "+39 02 1234567",
        "rating": 4.5,
        "reviews": 42,
        "category": "restaurant",
        "maps_url": f"https://maps.google.com/?cid={place_id}",
        "has_photos": False,
        "photo_paths": [],
        "fallback_unsplash_url": "",
        "photo_refs": [],
    }
    defaults.update(overrides)
    return BusinessData(**defaults)


@pytest.fixture
def store() -> Generator[PostgresStore]:
    """PostgresStore connected to real DB. Cleans up TEST_PLACE_* rows after each test."""
    s = PostgresStore(DATABASE_URL)
    _test_place_ids.clear()
    yield s
    # Cleanup: delete all test businesses
    for pid in _test_place_ids:
        s.delete_business(pid)
    # Also sweep any leftover TEST_PLACE_ businesses
    all_ids = s.all_place_ids()
    for pid in all_ids:
        if pid.startswith("TEST_PLACE_"):
            s.delete_business(pid)


@pytest.fixture
def file_storage(tmp_path: Any) -> LocalFileStorage:
    """LocalFileStorage backed by a temporary directory."""
    return LocalFileStorage(str(tmp_path))


@pytest.fixture
def client(tmp_path: Any) -> Generator[TestClient]:
    """FastAPI TestClient with real DB and temp file storage."""
    os.environ["WEBSEED_API_KEY"] = API_KEY
    app = create_app(DATABASE_URL, str(tmp_path / "results"))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Headers with valid API key."""
    return {"X-API-Key": API_KEY}
