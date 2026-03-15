"""Pipeline endpoints — all run in background, return job_id immediately."""

from __future__ import annotations

import asyncio
import os
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from webseed import services
from webseed.api.auth import require_api_key
from webseed.api.deps import get_file_storage, get_store
from webseed.api.ws import make_event_callback
from webseed.ports import FileStoragePort, PersistencePort

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


# ── Request models ──

class SearchRequest(BaseModel):
    location: str
    query: str
    types: list[str] = Field(default_factory=lambda: list[str]())
    limit: int = 10
    min_score: int = 0
    grid_size: int = 3


class EnrichRequest(BaseModel):
    place_ids: list[str]
    only_media: bool = False


class GenerateRequest(BaseModel):
    place_ids: list[str]
    model: str | None = None


class TestRequest(BaseModel):
    place_ids: list[str]
    playwright: bool = False
    max_fix_iterations: int | None = None
    model: str | None = None


class DeployRequest(BaseModel):
    place_ids: list[str]


class EmailRequest(BaseModel):
    place_ids: list[str]
    model: str | None = None


class RunRequest(BaseModel):
    place_ids: list[str]
    model: str | None = None
    test_model: str | None = None
    max_fix_iterations: int | None = None
    no_email: bool = False
    playwright: bool = False


class JobResponse(BaseModel):
    job_id: str


# ── Endpoints ──

@router.post("/search", response_model=JobResponse)
def pipeline_search(
    body: SearchRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_search,
        query=body.query, location=body.location, limit=body.limit,
        types=body.types, min_score=body.min_score, grid_size=body.grid_size,
        store=store, api_key=api_key, on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/enrich", response_model=JobResponse)
def pipeline_enrich(
    body: EnrichRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_enrich,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        api_key=api_key, only_media=body.only_media, on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/generate", response_model=JobResponse)
def pipeline_generate(
    body: GenerateRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_generate,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        model=body.model, on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/test", response_model=JobResponse)
def pipeline_test(
    body: TestRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_test,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        playwright=body.playwright, max_fix_iterations=body.max_fix_iterations,
        model=body.model, on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/deploy", response_model=JobResponse)
def pipeline_deploy(
    body: DeployRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_deploy,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/email", response_model=JobResponse)
def pipeline_email(
    body: EmailRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_email,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        model=body.model, on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)


@router.post("/run", response_model=JobResponse)
def pipeline_run(
    body: RunRequest,
    bg: BackgroundTasks,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> JobResponse:
    job_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()
    on_event = make_event_callback(loop, store)

    bg.add_task(
        services.run_pipeline,
        place_ids=body.place_ids, store=store, file_storage=file_storage,
        model=body.model, test_model=body.test_model,
        max_fix_iterations=body.max_fix_iterations,
        no_email=body.no_email, playwright=body.playwright,
        on_event=on_event, job_id=job_id,
    )
    return JobResponse(job_id=job_id)
