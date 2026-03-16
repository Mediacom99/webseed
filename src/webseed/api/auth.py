"""API key authentication dependency."""

from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    """FastAPI dependency that validates the X-API-Key header."""
    expected = os.environ.get("WEBSEED_API_KEY", "")
    if not expected:
        raise HTTPException(status_code=500, detail="WEBSEED_API_KEY not configured on server")
    if not api_key or api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key
