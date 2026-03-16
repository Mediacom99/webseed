"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

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

    # Test page
    @app.get("/", response_class=HTMLResponse)
    async def test_page() -> str:  # pyright: ignore[reportUnusedFunction]
        return _TEST_PAGE_HTML

    return app


_TEST_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>webseed — API Test</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d1117;color:#c9d1d9;padding:20px}
h1{font-size:1.4rem;margin-bottom:16px;color:#58a6ff}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;max-width:1200px;margin:0 auto}
.card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:16px}
.card h2{font-size:1rem;color:#58a6ff;margin-bottom:12px}
label{display:block;font-size:0.85rem;color:#8b949e;margin-bottom:4px}
input,select,textarea{width:100%;padding:8px;margin-bottom:10px;background:#0d1117;border:1px solid #30363d;border-radius:4px;color:#c9d1d9;font-family:inherit}
textarea{height:80px;resize:vertical}
button{padding:8px 16px;background:#238636;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:0.85rem;margin-right:6px;margin-bottom:6px}
button:hover{background:#2ea043}
button.danger{background:#da3633}
button.danger:hover{background:#f85149}
.status{display:inline-block;padding:3px 8px;border-radius:12px;font-size:0.75rem;margin-bottom:10px}
.status.connected{background:#238636;color:#fff}
.status.disconnected{background:#da3633;color:#fff}
#events{height:400px;overflow-y:auto;font-family:'Courier New',monospace;font-size:0.8rem;padding:12px;background:#0d1117;border:1px solid #30363d;border-radius:4px}
.event{padding:6px 0;border-bottom:1px solid #21262d}
.event .type{color:#f0883e;font-weight:bold}
.event .step{color:#a5d6ff}
.event .msg{color:#c9d1d9}
.event .time{color:#484f58;font-size:0.75rem}
.job-id{font-family:monospace;color:#f0883e;font-size:0.85rem;padding:4px 8px;background:#21262d;border-radius:4px;margin-top:6px}
@media(max-width:768px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<h1>webseed API Test Console</h1>
<div class="grid">
<div class="card">
<h2>Connection</h2>
<span id="ws-status" class="status disconnected">disconnected</span>
<br>
<label>API Key</label>
<input type="password" id="api-key" placeholder="Enter API key">
<button onclick="connectWS()">Connect WebSocket</button>
<button class="danger" onclick="disconnectWS()">Disconnect</button>

<h2 style="margin-top:16px">Quick Actions</h2>
<label>Endpoint</label>
<select id="endpoint">
<option value="/pipeline/search">POST /pipeline/search</option>
<option value="/pipeline/enrich">POST /pipeline/enrich</option>
<option value="/pipeline/generate">POST /pipeline/generate</option>
<option value="/pipeline/test">POST /pipeline/test</option>
<option value="/pipeline/deploy">POST /pipeline/deploy</option>
<option value="/pipeline/email">POST /pipeline/email</option>
<option value="/pipeline/run">POST /pipeline/run</option>
<option value="/businesses">GET /businesses</option>
<option value="/businesses/stats">GET /businesses/stats</option>
<option value="/settings">GET /settings</option>
</select>
<label>Request Body (JSON, for POST)</label>
<textarea id="req-body">{"place_ids": []}</textarea>
<button onclick="sendRequest()">Send Request</button>
<div id="response" style="margin-top:10px;font-family:monospace;font-size:0.8rem;white-space:pre-wrap;max-height:200px;overflow-y:auto;color:#7ee787"></div>
</div>
<div class="card">
<h2>Event Log</h2>
<button onclick="clearEvents()">Clear</button>
<div id="events"></div>
</div>
</div>

<script>
let ws = null;
const eventsEl = document.getElementById('events');
const statusEl = document.getElementById('ws-status');

function connectWS() {
  const key = document.getElementById('api-key').value;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const url = proto + '//' + location.host + '/ws' + (key ? '?api_key=' + encodeURIComponent(key) : '');
  if (ws) ws.close();
  ws = new WebSocket(url);
  ws.onopen = function() { statusEl.textContent = 'connected'; statusEl.className = 'status connected'; addEvent({event_type:'system', message:'WebSocket connected'}); };
  ws.onclose = function() { statusEl.textContent = 'disconnected'; statusEl.className = 'status disconnected'; addEvent({event_type:'system', message:'WebSocket disconnected'}); };
  ws.onerror = function() { addEvent({event_type:'error', message:'WebSocket error'}); };
  ws.onmessage = function(e) { try { addEvent(JSON.parse(e.data)); } catch(err) { addEvent({event_type:'raw', message:e.data}); } };
}

function disconnectWS() { if (ws) ws.close(); }

function addEvent(evt) {
  const div = document.createElement('div');
  div.className = 'event';
  const time = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();

  const timeSpan = document.createElement('span');
  timeSpan.className = 'time';
  timeSpan.textContent = time + ' ';
  div.appendChild(timeSpan);

  const typeSpan = document.createElement('span');
  typeSpan.className = 'type';
  typeSpan.textContent = '[' + (evt.event_type || '?') + '] ';
  div.appendChild(typeSpan);

  if (evt.step) {
    const stepSpan = document.createElement('span');
    stepSpan.className = 'step';
    stepSpan.textContent = evt.step + ' ';
    div.appendChild(stepSpan);
  }

  const msgSpan = document.createElement('span');
  msgSpan.className = 'msg';
  msgSpan.textContent = evt.message || JSON.stringify(evt.data || '');
  div.appendChild(msgSpan);

  if (evt.place_id) {
    const pidSpan = document.createElement('span');
    pidSpan.style.color = '#484f58';
    pidSpan.textContent = ' (' + evt.place_id.substring(0, 12) + '...)';
    div.appendChild(pidSpan);
  }

  eventsEl.appendChild(div);
  eventsEl.scrollTop = eventsEl.scrollHeight;
}

function clearEvents() { eventsEl.textContent = ''; }

async function sendRequest() {
  const endpoint = document.getElementById('endpoint').value;
  const key = document.getElementById('api-key').value;
  const body = document.getElementById('req-body').value;
  const method = endpoint.startsWith('/pipeline/') && endpoint !== '/pipeline' ? 'POST' : 'GET';
  const respEl = document.getElementById('response');
  try {
    const opts = { method: method, headers: { 'X-API-Key': key, 'Content-Type': 'application/json' } };
    if (method === 'POST') opts.body = body;
    const res = await fetch(endpoint, opts);
    const data = await res.json();
    respEl.textContent = JSON.stringify(data, null, 2);
  } catch(e) { respEl.textContent = 'Error: ' + e.message; }
}
</script>
</body>
</html>"""
