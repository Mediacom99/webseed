"""WebSocket manager for real-time event streaming."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket

from webseed.models import PipelineEvent
from webseed.ports import EventCallback, PersistencePort

log = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)

    async def broadcast(self, event: PipelineEvent) -> None:
        data = {
            "event_type": event.event_type,
            "job_id": event.job_id,
            "step": event.step,
            "place_id": event.place_id,
            "message": event.message,
            "data": event.data,
            "timestamp": event.timestamp,
        }
        text = json.dumps(data)
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Module-level singleton
manager = WebSocketManager()


def make_event_callback(
    loop: asyncio.AbstractEventLoop,
    store: PersistencePort | None = None,
) -> EventCallback:
    """Create a sync EventCallback that bridges to async WebSocket broadcast.

    Also logs events to the database if a store is provided.
    """

    def callback(event: PipelineEvent) -> None:
        # Broadcast via WebSocket
        try:
            asyncio.run_coroutine_threadsafe(manager.broadcast(event), loop)
        except RuntimeError:
            log.debug("Event loop closed, skipping WebSocket broadcast")

        # Log to database
        if store is not None:
            try:
                store.log_event(
                    job_id=event.job_id,
                    place_id=event.place_id,
                    event_type=event.event_type,
                    step=event.step,
                    message=event.message,
                    data=event.data,
                )
            except Exception as e:
                log.warning("Failed to log event: %s", e)

    return callback
