"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from webseed.ports import FileStoragePort, PersistencePort


def get_store(request: Request) -> PersistencePort:
    """Get the PersistencePort from app state."""
    return cast(PersistencePort, request.app.state.store)


def get_file_storage(request: Request) -> FileStoragePort:
    """Get the FileStoragePort from app state."""
    return cast(FileStoragePort, request.app.state.file_storage)
