"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from webseed.api.routers import businesses, pipeline, settings
from webseed.api.ws import manager
from webseed.db.store import PostgresStore
from webseed.storage import LocalFileStorage

log = logging.getLogger(__name__)


def create_app(database_url: str, results_dir: str = "results") -> FastAPI:
    """Create and configure the FastAPI application."""

    store = PostgresStore(database_url)
    file_storage = LocalFileStorage(results_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # Startup: reset stale running statuses
        count = store.reset_stale_running()
        if count > 0:
            log.warning("Reset %d stale running statuses on startup", count)
        yield

    app = FastAPI(
        title="webseed",
        description="Automated pipeline for Italian local business website generation",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Attach to app state for dependency injection
    app.state.store = store
    app.state.file_storage = file_storage

    # Include routers
    app.include_router(pipeline.router)
    app.include_router(businesses.router)
    app.include_router(settings.router)

    # WebSocket endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, api_key: str | None = None) -> None:  # pyright: ignore[reportUnusedFunction]
        expected = os.environ.get("WEBSEED_API_KEY", "")
        if expected and api_key != expected:
            await websocket.accept()
            await websocket.close(code=4001, reason="Invalid API key")
            return
        await manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app
