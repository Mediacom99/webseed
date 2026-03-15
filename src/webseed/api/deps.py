"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from fastapi import Request

from webseed.ports import FileStoragePort, PersistencePort


def get_store(request: Request) -> PersistencePort:
    """Get the PersistencePort from app state."""
    store: PersistencePort = request.app.state.store  # type: ignore[assignment]
    return store


def get_file_storage(request: Request) -> FileStoragePort:
    """Get the FileStoragePort from app state."""
    storage: FileStoragePort = request.app.state.file_storage  # type: ignore[assignment]
    return storage
