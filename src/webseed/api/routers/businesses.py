"""Business CRUD + management endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from webseed import services
from webseed.api.auth import require_api_key
from webseed.api.deps import get_file_storage, get_store
from webseed.models import BusinessRecord, PipelineStatus
from webseed.ports import FileStoragePort, PersistencePort

router = APIRouter(prefix="/businesses", tags=["businesses"])


# ── Request/Response models ──

class StatusUpdate(BaseModel):
    to: str


class HardDeleteRequest(BaseModel):
    place_ids: list[str]
    keep_blacklisted: bool = False


class CloseRequest(BaseModel):
    place_ids: list[str]


def _record_to_dict(rec: BusinessRecord) -> dict[str, Any]:
    """Convert a BusinessRecord to a dict for JSON response."""
    return {
        "id": rec.id,
        "place_id": rec.place_id,
        "name": rec.name,
        "address": rec.address,
        "phone": rec.phone,
        "email": rec.email,
        "rating": rec.rating,
        "reviews": rec.reviews,
        "category": rec.category,
        "maps_url": rec.maps_url,
        "has_photos": rec.has_photos,
        "photo_paths": rec.photo_paths,
        "photo_refs": rec.photo_refs,
        "fallback_unsplash_url": rec.fallback_unsplash_url,
        "lead_score": rec.lead_score,
        "price_level": rec.price_level,
        "business_status": rec.business_status,
        "primary_type": rec.primary_type,
        "types": rec.types,
        "has_opening_hours": rec.has_opening_hours,
        "opening_hours_summary": rec.opening_hours_summary,
        "accepts_credit_cards": rec.accepts_credit_cards,
        "editorial_summary": rec.editorial_summary,
        "review_texts": rec.review_texts,
        "status": rec.status,
        "error_detail": rec.error_detail,
        "vercel_url": rec.vercel_url,
        "site_screenshot_path": rec.site_screenshot_path,
        "email_sent_at": rec.email_sent_at,
        "test_iterations": rec.test_iterations,
        "test_issues": rec.test_issues,
        "run_id": rec.run_id,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }


# ── Endpoints ──

@router.get("")
def list_businesses(
    status: str | None = None,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> list[dict[str, Any]]:
    records = services.list_businesses(store, status=status)
    return [_record_to_dict(r) for r in records]


@router.get("/stats")
def get_stats(
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, int]:
    return services.get_stats(store)


@router.get("/export/csv")
def export_csv(
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> PlainTextResponse:
    csv_content = services.export_csv(store)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=webseed_export.csv"},
    )


@router.get("/{place_id}")
def get_business(
    place_id: str,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, Any]:
    rec = services.get_business(store, place_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Business not found")
    return _record_to_dict(rec)


@router.patch("/{place_id}/status")
def update_status(
    place_id: str,
    body: StatusUpdate,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, str]:
    try:
        target = PipelineStatus(body.to)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.to}")
    if not services.reset_status(store, place_id, target):
        raise HTTPException(status_code=404, detail="Business not found")
    return {"status": "updated", "to": body.to}


@router.delete("/{place_id}")
def delete_business(
    place_id: str,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, str]:
    if not store.delete_business(place_id):
        raise HTTPException(status_code=404, detail="Business not found")
    return {"status": "deleted"}


@router.post("/{place_id}/blacklist")
def blacklist_add(
    place_id: str,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, str]:
    count = services.blacklist_add(store, [place_id])
    if count == 0:
        raise HTTPException(status_code=404, detail="Business not found")
    return {"status": "blacklisted"}


@router.delete("/{place_id}/blacklist")
def blacklist_remove(
    place_id: str,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, str]:
    if not services.blacklist_remove(store, place_id):
        raise HTTPException(status_code=404, detail="Business not found or not blacklisted")
    return {"status": "removed_from_blacklist"}


@router.post("/hard-delete")
def hard_delete(
    body: HardDeleteRequest,
    store: PersistencePort = Depends(get_store),
    file_storage: FileStoragePort = Depends(get_file_storage),
    _key: str = Depends(require_api_key),
) -> dict[str, Any]:
    results = services.hard_delete(store, file_storage, body.place_ids, keep_blacklisted=body.keep_blacklisted)
    return {"results": results}


@router.post("/close")
def close_businesses(
    body: CloseRequest,
    store: PersistencePort = Depends(get_store),
    _key: str = Depends(require_api_key),
) -> dict[str, Any]:
    results = services.close_businesses(store, body.place_ids)
    return {"results": results}
