"""TinyDB data store — local JSON-based state management for the pipeline."""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any, cast

from tinydb import TinyDB, Query

if TYPE_CHECKING:
    from webseed.maps import BusinessData


def open_db(db_path: str = "webseed.json") -> TinyDB:
    """Open or create the TinyDB database file."""
    return TinyDB(db_path, indent=2)


def find_by_place_id(db: TinyDB, place_id: str) -> dict[str, Any] | None:
    """Find a business by place_id. Returns the document or None."""
    Biz = Query()
    results = db.search(Biz.place_id == place_id)
    if results:
        return cast(dict[str, Any], results[0])
    return None


def find_by_name(db: TinyDB, query: str) -> list[dict[str, Any]]:
    """Case-insensitive substring search on business name (like SQL ILIKE)."""
    Biz = Query()
    q_lower = query.lower()
    return [cast(dict[str, Any], d) for d in db.search(
        Biz.name.test(lambda name: q_lower in str(name).lower())  # type: ignore[arg-type]
    )]


def resolve_identifier(db: TinyDB, identifier: str) -> list[dict[str, Any]]:
    """Resolve an identifier to businesses — tries exact place_id first, then name search."""
    doc = find_by_place_id(db, identifier)
    if doc:
        return [doc]
    return find_by_name(db, identifier)


def upsert_business(db: TinyDB, biz: BusinessData, run_id: str) -> str:
    """Insert or update a business. If place_id exists, update mutable fields only.
    Returns 'inserted' or 'updated'."""
    Biz = Query()
    existing = db.search(Biz.place_id == biz.place_id)
    now = datetime.now().isoformat()

    if existing:
        # Update mutable fields only — preserve status, URLs, email tracking
        update_fields: dict[str, Any] = {
            "rating": biz.rating,
            "reviews": biz.reviews,
            "address": biz.address,
            "phone": biz.phone or "",
            "category": biz.category,
            "maps_url": biz.maps_url,
            "lead_score": biz.lead_score,
            "price_level": biz.price_level,
            "business_status": biz.business_status,
            "primary_type": biz.primary_type,
            "types": biz.types,
            "has_opening_hours": biz.has_opening_hours,
            "opening_hours_summary": biz.opening_hours_summary,
            "accepts_credit_cards": biz.accepts_credit_cards,
            "editorial_summary": biz.editorial_summary,
            "review_texts": biz.review_texts,
            "has_photos": biz.has_photos,
            "photo_paths": biz.photo_paths,
            "photo_refs": biz.photo_refs,
            "fallback_unsplash_url": biz.fallback_unsplash_url,
            "updated_at": now,
        }
        db.update(cast(dict[str, object], update_fields), Biz.place_id == biz.place_id)  # type: ignore[arg-type]
        return "updated"

    insert_doc: dict[str, Any] = {
        "place_id": biz.place_id,
        "name": biz.name,
        "address": biz.address,
        "phone": biz.phone or "",
        "email": "",
        "rating": biz.rating,
        "reviews": biz.reviews,
        "category": biz.category,
        "maps_url": biz.maps_url,
        "has_photos": biz.has_photos,
        "photo_paths": biz.photo_paths,
        "photo_refs": biz.photo_refs,
        "fallback_unsplash_url": biz.fallback_unsplash_url,
        "lead_score": biz.lead_score,
        "price_level": biz.price_level,
        "business_status": biz.business_status,
        "primary_type": biz.primary_type,
        "types": biz.types,
        "has_opening_hours": biz.has_opening_hours,
        "opening_hours_summary": biz.opening_hours_summary,
        "accepts_credit_cards": biz.accepts_credit_cards,
        "editorial_summary": biz.editorial_summary,
        "review_texts": biz.review_texts,
        "status": "searched",
        "error_detail": "",
        "vercel_url": "",
        "site_screenshot_path": "",
        "email_sent_at": "",
        "run_id": run_id,
        "created_at": now,
        "updated_at": now,
    }
    db.insert(cast(dict[str, object], insert_doc))  # type: ignore[arg-type]
    return "inserted"


def update_status(
    db: TinyDB, place_id: str, status: str, extra: dict[str, Any] | None = None
) -> None:
    """Update the status (and optional extra fields) for a business."""
    Biz = Query()
    updates: dict[str, Any] = {"status": status, "updated_at": datetime.now().isoformat()}
    if extra:
        updates.update(extra)
    db.update(cast(dict[str, object], updates), Biz.place_id == place_id)  # type: ignore[arg-type]


def delete_business(db: TinyDB, place_id: str) -> bool:
    """Remove a business from the DB. Returns True if found and deleted."""
    Biz = Query()
    removed = db.remove(Biz.place_id == place_id)
    return len(removed) > 0


def all_place_ids(db: TinyDB) -> set[str]:
    """Return the set of all place_ids currently in the DB."""
    return {str(cast(dict[str, Any], d)["place_id"]) for d in db.all()}


def get_businesses_at_status(db: TinyDB, status: str) -> list[dict[str, Any]]:
    """Return all businesses with the given status."""
    Biz = Query()
    return [cast(dict[str, Any], d) for d in db.search(Biz.status == status)]


def get_all_businesses(db: TinyDB) -> list[dict[str, Any]]:
    """Return all businesses in the DB."""
    return [cast(dict[str, Any], d) for d in db.all()]


def get_blacklisted_place_ids(db: TinyDB) -> set[str]:
    """Return place_ids with status 'opted_out' from DB."""
    Biz = Query()
    return {str(cast(dict[str, Any], doc)["place_id"]) for doc in db.search(Biz.status == "opted_out")}


def load_blacklist(filepath: str = "blacklist.txt") -> set[str]:
    """Load place_ids from local blacklist file."""
    if not os.path.exists(filepath):
        return set()
    with open(filepath, encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip() and not line.startswith("#")}


def get_full_blacklist(db: TinyDB, filepath: str = "blacklist.txt") -> set[str]:
    """Merge DB opted_out place_ids with local blacklist file."""
    return load_blacklist(filepath) | get_blacklisted_place_ids(db)


def add_to_blacklist(filepath: str, place_ids: list[str]) -> None:
    """Append place_ids to the local blacklist file."""
    existing = load_blacklist(filepath)
    with open(filepath, "a", encoding="utf-8") as f:
        for pid in place_ids:
            if pid not in existing:
                f.write(f"{pid}\n")


def remove_from_blacklist(filepath: str, place_id: str) -> bool:
    """Remove a place_id from the local blacklist file. Returns True if found."""
    if not os.path.exists(filepath):
        return False
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = [l for l in lines if l.strip() != place_id]
    if len(new_lines) == len(lines):
        return False
    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    return True
