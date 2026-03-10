"""Google Places API (v1) — search businesses without websites, score leads, download photos."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import requests

log = logging.getLogger(__name__)

MAX_PHOTOS = 3
_API_BASE = "https://places.googleapis.com/v1"
_MAX_DETAIL_CALLS = 100  # cost safeguard

CATEGORY_UNSPLASH: dict[str, str] = {
    "restaurant": "italian-restaurant",
    "italian_restaurant": "italian-restaurant",
    "pizza_restaurant": "italian-pizza",
    "food": "italian-food",
    "bar": "coffee-bar",
    "cafe": "cafe-coffee",
    "coffee_shop": "cafe-coffee",
    "bakery": "bakery-bread",
    "hair_salon": "hair-salon",
    "hair_care": "hair-salon",
    "beauty_salon": "beauty-salon",
    "barber_shop": "barber-shop",
    "gym": "gym-fitness",
    "fitness_center": "gym-fitness",
    "store": "shop-retail",
    "clothing_store": "clothing-store",
    "lodging": "hotel-room",
    "hotel": "hotel-room",
    "bed_and_breakfast": "hotel-room",
    "health": "medical-clinic",
    "dentist": "dental-clinic",
    "dental_clinic": "dental-clinic",
    "car_repair": "auto-mechanic",
    "veterinary_care": "veterinary-clinic",
    "florist": "flower-shop",
    "pharmacy": "pharmacy",
    "spa": "spa-wellness",
    "ice_cream_shop": "gelato-italy",
}
DEFAULT_UNSPLASH = "local-business-italy"

# ---------------------------------------------------------------------------
# Query-to-type expansion map (English Google type identifiers)
# ---------------------------------------------------------------------------

QUERY_TYPE_MAP: dict[str, list[str]] = {
    "restaurant": ["restaurant", "italian_restaurant", "pizza_restaurant", "meal_takeaway"],
    "bar": ["bar", "cafe", "coffee_shop"],
    "hair_salon": ["hair_salon", "beauty_salon", "barber_shop"],
    "dentist": ["dentist", "dental_clinic"],
    "car_repair": ["car_repair", "car_wash"],
    "hotel": ["hotel", "bed_and_breakfast", "lodging", "guest_house"],
    "gym": ["gym", "fitness_center"],
    "store": ["store", "clothing_store", "shoe_store", "jewelry_store"],
    "pharmacy": ["pharmacy"],
    "veterinary_care": ["veterinary_care"],
    "florist": ["florist"],
    "bakery": ["bakery"],
    "pizza_restaurant": ["pizza_restaurant", "italian_restaurant"],
    "ice_cream_shop": ["ice_cream_shop"],
    "spa": ["spa", "beauty_salon"],
}

# ---------------------------------------------------------------------------
# Lead scoring constants
# ---------------------------------------------------------------------------

_HIGH_TIER_CATEGORIES: set[str] = {
    "restaurant", "italian_restaurant", "pizza_restaurant",
    "hair_salon", "beauty_salon", "spa", "dentist", "dental_clinic",
    "hotel", "bed_and_breakfast", "lodging", "guest_house",
}
_MID_TIER_CATEGORIES: set[str] = {
    "bar", "cafe", "coffee_shop", "bakery", "gym", "fitness_center",
    "car_repair", "florist", "pet_store", "clothing_store",
    "veterinary_care", "ice_cream_shop",
}


@dataclass
class BusinessData:
    name: str
    place_id: str
    address: str
    phone: Optional[str]
    rating: float
    reviews: int
    category: str
    maps_url: str
    has_photos: bool
    photo_paths: list[str]
    fallback_unsplash_url: str
    # New fields for lead scoring & enrichment (all defaulted for backward compat)
    lead_score: int = 0
    price_level: Optional[str] = None
    business_status: str = "OPERATIONAL"
    primary_type: Optional[str] = None
    types: Optional[list[str]] = None
    has_opening_hours: bool = False
    opening_hours_summary: Optional[str] = None
    accepts_credit_cards: Optional[bool] = None
    editorial_summary: Optional[str] = None
    review_texts: Optional[list[str]] = None


def safe_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("/", "_")[:30]


# ---------------------------------------------------------------------------
# Places API (v1) helpers
# ---------------------------------------------------------------------------

# Stage 1: cheap fields for discovery filtering
_SEARCH_FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.location",
    "places.rating",
    "places.userRatingCount",
    "places.businessStatus",
    "places.primaryType",
    "places.primaryTypeDisplayName",
    "places.websiteUri",
    "places.googleMapsUri",
])

# Stage 2: rich detail fields for scoring + enrichment
_DETAIL_FIELD_MASK = ",".join([
    "id",
    "displayName",
    "formattedAddress",
    "internationalPhoneNumber",
    "nationalPhoneNumber",
    "rating",
    "userRatingCount",
    "businessStatus",
    "priceLevel",
    "primaryType",
    "primaryTypeDisplayName",
    "types",
    "regularOpeningHours",
    "editorialSummary",
    "paymentOptions",
    "photos",
    "reviews",
    "googleMapsUri",
    "websiteUri",
])


def _api_headers(api_key: str, field_mask: str) -> dict[str, str]:
    return {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask,
        "Content-Type": "application/json",
    }


def _request_with_retry(
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None = None,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Make an API request with exponential backoff on 429/5xx."""
    for attempt in range(max_retries):
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=15)
            else:
                resp = requests.post(url, headers=headers, json=json_body, timeout=15)

            if resp.status_code == 429 or resp.status_code >= 500:
                wait = 2 ** attempt
                log.warning("API %s (attempt %d/%d), retrying in %ds", resp.status_code, attempt + 1, max_retries, wait)
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"API request failed after {max_retries} attempts: {e}") from e

    raise RuntimeError(f"API request failed after {max_retries} attempts")


def _search_text(
    api_key: str,
    query: str,
    location_bias: dict[str, Any] | None = None,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Text Search (New). Returns up to page_size results."""
    body: dict[str, Any] = {
        "textQuery": query,
        "languageCode": "it",
        "pageSize": min(page_size, 20),
    }
    if location_bias:
        body["locationBias"] = location_bias

    data = _request_with_retry(
        "POST",
        f"{_API_BASE}/places:searchText",
        _api_headers(api_key, _SEARCH_FIELD_MASK),
        json_body=body,
    )
    return data.get("places", [])


def _search_nearby(
    api_key: str,
    lat: float,
    lng: float,
    radius: float,
    included_types: list[str] | None = None,
    page_size: int = 20,
) -> list[dict[str, Any]]:
    """Nearby Search (New). Returns up to page_size results."""
    body: dict[str, Any] = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": min(radius, 50000.0),
            }
        },
        "languageCode": "it",
        "maxResultCount": min(page_size, 20),
    }
    if included_types:
        body["includedTypes"] = included_types

    data = _request_with_retry(
        "POST",
        f"{_API_BASE}/places:searchNearby",
        _api_headers(api_key, _SEARCH_FIELD_MASK),
        json_body=body,
    )
    return data.get("places", [])


def _get_place_details(api_key: str, place_id: str) -> dict[str, Any]:
    """Place Details (New). Full enrichment for a single place."""
    return _request_with_retry(
        "GET",
        f"{_API_BASE}/places/{place_id}",
        _api_headers(api_key, _DETAIL_FIELD_MASK),
    )


# ---------------------------------------------------------------------------
# Geocoding + Grid tiling
# ---------------------------------------------------------------------------

def _geocode_city(api_key: str, city: str) -> tuple[float, float]:
    """Geocode a city name to lat/lng using the Geocoding API."""
    resp = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": city, "key": api_key},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        raise ValueError(f"Could not geocode: {city}")
    loc = results[0]["geometry"]["location"]
    return float(loc["lat"]), float(loc["lng"])


def _generate_grid(
    center_lat: float, center_lng: float, grid_size: int = 3
) -> list[tuple[float, float, float]]:
    """Generate grid_size x grid_size points around center.
    Returns list of (lat, lng, radius_meters).

    For a typical Italian city:
    - 2x2 grid = 4 cells, ~2.5km radius each (small town)
    - 3x3 grid = 9 cells, ~1.7km radius each (medium city)
    """
    city_span_deg = 0.045  # ~5km total span
    step = city_span_deg / grid_size
    radius = step * 111_000 / 2 * 1.2  # convert to meters with overlap

    points: list[tuple[float, float, float]] = []
    half = (grid_size - 1) / 2
    for row in range(grid_size):
        for col in range(grid_size):
            lat = center_lat + (row - half) * step
            lng = center_lng + (col - half) * step
            points.append((lat, lng, radius))
    return points


# ---------------------------------------------------------------------------
# Photo download (new API format)
# ---------------------------------------------------------------------------

def _download_photos(
    photos: list[dict[str, Any]], api_key: str, img_dir: str
) -> list[str]:
    """Download up to MAX_PHOTOS from new Places API. Returns relative paths."""
    os.makedirs(img_dir, exist_ok=True)
    paths: list[str] = []

    for i, photo in enumerate(photos[:MAX_PHOTOS]):
        photo_name = photo.get("name", "")
        if not photo_name:
            continue
        url = f"{_API_BASE}/{photo_name}/media?maxWidthPx=800&key={api_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                path = os.path.join(img_dir, f"photo{i + 1}.jpg")
                with open(path, "wb") as f:
                    f.write(resp.content)
                paths.append(f"img/photo{i + 1}.jpg")
        except requests.RequestException:
            continue

    return paths


# ---------------------------------------------------------------------------
# Lead scoring
# ---------------------------------------------------------------------------

def _compute_lead_score(details: dict[str, Any]) -> int:
    """Compute 0-100 lead score from enriched place details."""
    score = 0.0

    # Rating: 4.5+ = 20, 4.0-4.5 = 10-20, 3.5-4.0 = 5
    rating = float(details.get("rating", 0))
    if rating >= 4.5:
        score += 20
    elif rating >= 4.0:
        score += 10 + (rating - 4.0) * 20
    elif rating >= 3.5:
        score += 5

    # Review count: log scale
    reviews = int(details.get("userRatingCount", 0))
    if reviews >= 200:
        score += 20
    elif reviews >= 100:
        score += 15
    elif reviews >= 50:
        score += 10
    elif reviews >= 10:
        score += 5

    # Price level
    price_map = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 3,
        "PRICE_LEVEL_MODERATE": 8,
        "PRICE_LEVEL_EXPENSIVE": 12,
        "PRICE_LEVEL_VERY_EXPENSIVE": 15,
    }
    price_level = details.get("priceLevel")
    if price_level:
        score += price_map.get(str(price_level), 0)

    # Opening hours
    if details.get("regularOpeningHours"):
        score += 10

    # Business status
    if details.get("businessStatus") == "OPERATIONAL":
        score += 10

    # Category tier
    primary_type = str(details.get("primaryType", ""))
    if primary_type in _HIGH_TIER_CATEGORIES:
        score += 10
    elif primary_type in _MID_TIER_CATEGORIES:
        score += 5

    # Review recency (any review within last 6 months)
    reviews_list: list[dict[str, Any]] = details.get("reviews", [])
    if reviews_list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        for review in reviews_list[:5]:
            pub_time = str(review.get("publishTime", ""))
            if pub_time:
                try:
                    review_dt = datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                    if review_dt > cutoff:
                        score += 10
                        break
                except ValueError:
                    pass

    # Has photos
    if details.get("photos"):
        score += 5

    return min(int(score), 100)


def _extract_enrichment(details: dict[str, Any]) -> dict[str, Any]:
    """Extract enrichment fields from place details response."""
    # Opening hours summary
    opening_hours = details.get("regularOpeningHours", {})
    hours_descriptions: list[str] = opening_hours.get("weekdayDescriptions", [])
    opening_summary = "; ".join(hours_descriptions) if hours_descriptions else None

    # Payment options
    payment = details.get("paymentOptions", {})
    accepts_cc: bool | None = None
    if payment:
        accepts_cc = bool(payment.get("acceptsCreditCards", False))

    # Editorial summary
    editorial = details.get("editorialSummary", {})
    editorial_text = str(editorial.get("text", "")) if editorial else None

    # Review texts (up to 5, truncated to 200 chars)
    review_texts: list[str] = []
    for review in details.get("reviews", [])[:5]:
        text_obj = review.get("text", {})
        text = str(text_obj.get("text", "")) if text_obj else ""
        if text:
            review_texts.append(text[:200])

    return {
        "price_level": details.get("priceLevel"),
        "business_status": str(details.get("businessStatus", "OPERATIONAL")),
        "primary_type": details.get("primaryType"),
        "types": details.get("types"),
        "has_opening_hours": bool(opening_hours),
        "opening_hours_summary": opening_summary,
        "accepts_credit_cards": accepts_cc,
        "editorial_summary": editorial_text,
        "review_texts": review_texts or None,
    }


# ---------------------------------------------------------------------------
# Main search function (two-stage)
# ---------------------------------------------------------------------------

def search(
    query: str,
    location: str,
    limit: int,
    api_key: str,
    output_dir: str,
    min_score: int = 0,
    grid_size: int = 3,
    raw_types: list[str] | None = None,
    skip_place_ids: set[str] | None = None,
) -> list[BusinessData]:
    """Search for businesses without a website using two-stage approach.

    Stage 1 (cheap): Nearby Search (grid) + Text Search → filter by no-website + operational
    Stage 2 (rich): Place Details for qualifying candidates → score + enrich

    Args:
        query: Business type query (e.g. "restaurant"). Used for type expansion and text search.
        location: City/area name (e.g. "Milano, Italy").
        limit: Max *new* businesses to return.
        api_key: Google API key (works with both Places and Geocoding APIs).
        output_dir: Directory for downloaded photos.
        min_score: Minimum lead score (0-100) to include in results.
        grid_size: Grid dimension (2=4 cells, 3=9 cells).
        raw_types: If provided, use these Google type IDs directly instead of QUERY_TYPE_MAP.
        skip_place_ids: Place IDs already known (DB + blacklist). These are skipped
            during enrichment so ``limit`` counts only genuinely new businesses.
    """
    # ── Geocode ──
    center_lat: float | None = None
    center_lng: float | None = None
    try:
        center_lat, center_lng = _geocode_city(api_key, location)
        print(f"  Geocoded {location} → ({center_lat:.4f}, {center_lng:.4f})")
    except (ValueError, requests.RequestException) as e:
        log.warning("Geocoding failed for '%s': %s. Falling back to text search only.", location, e)
        print(f"  Geocoding failed for '{location}', using text search only")

    # ── Resolve types ──
    if raw_types:
        search_types = raw_types
    else:
        search_types = QUERY_TYPE_MAP.get(query.lower(), [query])

    # ── Stage 1: Discovery ──
    print(f"\n  Stage 1: Discovery (types: {search_types})")
    seen_ids: set[str] = set()
    candidates: list[dict[str, Any]] = []

    # 1a. Grid-based Nearby Search
    if center_lat is not None and center_lng is not None:
        grid = _generate_grid(center_lat, center_lng, grid_size)
        print(f"  Grid: {grid_size}x{grid_size} = {len(grid)} cells")

        for i, (lat, lng, radius) in enumerate(grid):
            try:
                places = _search_nearby(api_key, lat, lng, radius, included_types=search_types)
                new = 0
                for p in places:
                    pid = str(p.get("id", ""))
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        candidates.append(p)
                        new += 1
                log.debug("Grid cell %d/%d: %d results, %d new", i + 1, len(grid), len(places), new)
            except RuntimeError as e:
                log.warning("Nearby search failed for grid cell %d: %s", i + 1, e)

    # 1b. Text Search for broader coverage
    location_bias: dict[str, Any] | None = None
    if center_lat is not None and center_lng is not None:
        location_bias = {
            "circle": {
                "center": {"latitude": center_lat, "longitude": center_lng},
                "radius": 5000.0,
            }
        }

    text_queries = [f"{query} {location}"]
    for t in search_types:
        tq = f"{t.replace('_', ' ')} {location}"
        if tq not in text_queries:
            text_queries.append(tq)

    for tq in text_queries:
        try:
            print(f"  Text search: {tq}")
            places = _search_text(api_key, tq, location_bias=location_bias)
            new = 0
            for p in places:
                pid = str(p.get("id", ""))
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    candidates.append(p)
                    new += 1
            log.debug("Text search '%s': %d results, %d new", tq, len(places), new)
        except RuntimeError as e:
            log.warning("Text search failed for '%s': %s", tq, e)

    # ── Filter Stage 1 candidates ──
    filtered: list[dict[str, Any]] = []
    for p in candidates:
        # Skip businesses with websites
        if p.get("websiteUri"):
            name = p.get("displayName", {}).get("text", "?")
            log.debug("Skip (has website): %s", name)
            continue
        # Skip non-operational businesses
        status = str(p.get("businessStatus", "OPERATIONAL"))
        if status not in ("OPERATIONAL", ""):
            name = p.get("displayName", {}).get("text", "?")
            log.debug("Skip (status %s): %s", status, name)
            continue
        filtered.append(p)

    print(f"\n  Stage 1 complete: {len(candidates)} found, {len(filtered)} without website")

    # ── Pre-rank for cost safeguard ──
    if len(filtered) > _MAX_DETAIL_CALLS:
        print(f"  Cost safeguard: {len(filtered)} candidates > {_MAX_DETAIL_CALLS} cap, pre-ranking...")
        filtered.sort(
            key=lambda p: float(p.get("rating", 0)) * int(p.get("userRatingCount", 0)),
            reverse=True,
        )
        filtered = filtered[:_MAX_DETAIL_CALLS]

    # ── Stage 2: Enrichment ──
    _skip = skip_place_ids or set()
    eligible = [p for p in filtered if str(p.get("id", "")) not in _skip]
    skipped_known = len(filtered) - len(eligible)
    if skipped_known:
        print(f"\n  Skipping {skipped_known} already-known businesses")
    print(f"\n  Stage 2: Enriching {len(eligible)} new candidates (limit: {limit})...")
    businesses: list[BusinessData] = []

    for i, p in enumerate(eligible):
        place_id = str(p.get("id", ""))
        display_name = p.get("displayName", {}).get("text", "Unknown")

        try:
            details = _get_place_details(api_key, place_id)
        except RuntimeError as e:
            log.warning("Detail fetch failed for %s: %s", display_name, e)
            continue

        # Double-check website (detail call may reveal one not in search results)
        if details.get("websiteUri"):
            log.debug("Skip (website found in details): %s", display_name)
            continue

        # Compute lead score
        score = _compute_lead_score(details)
        if score < min_score:
            log.debug("Skip (score %d < %d): %s", score, min_score, display_name)
            continue

        # Extract enrichment
        enrichment = _extract_enrichment(details)

        # Determine category
        primary_type = str(details.get("primaryType", ""))
        all_types: list[str] = details.get("types", [])
        category = primary_type
        if not category:
            category = next(
                (t for t in all_types if t in CATEGORY_UNSPLASH),
                all_types[0] if all_types else "establishment",
            )

        # Download photos
        name = str(details.get("displayName", {}).get("text", "Unknown"))
        safe = safe_name(name)
        img_dir = os.path.join(output_dir, safe, "img")
        photo_paths = _download_photos(details.get("photos", []), api_key, img_dir)

        # Unsplash fallback
        unsplash_query = CATEGORY_UNSPLASH.get(category, DEFAULT_UNSPLASH)
        fallback_url = f"https://source.unsplash.com/1200x600/?{unsplash_query}"

        # Phone: prefer international, fall back to national
        phone = details.get("internationalPhoneNumber") or details.get("nationalPhoneNumber")

        biz = BusinessData(
            name=name,
            place_id=place_id,
            address=str(details.get("formattedAddress", "")),
            phone=phone,
            rating=float(details.get("rating", 0.0)),
            reviews=int(details.get("userRatingCount", 0)),
            category=category,
            maps_url=str(details.get("googleMapsUri", "")),
            has_photos=len(photo_paths) > 0,
            photo_paths=photo_paths,
            fallback_unsplash_url=fallback_url,
            lead_score=score,
            price_level=enrichment["price_level"],
            business_status=enrichment["business_status"],
            primary_type=enrichment["primary_type"],
            types=enrichment["types"],
            has_opening_hours=enrichment["has_opening_hours"],
            opening_hours_summary=enrichment["opening_hours_summary"],
            accepts_credit_cards=enrichment["accepts_credit_cards"],
            editorial_summary=enrichment["editorial_summary"],
            review_texts=enrichment["review_texts"],
        )
        businesses.append(biz)
        print(f"  [{len(businesses)}] {biz.name} — score:{score} rating:{biz.rating} reviews:{biz.reviews}")

    # Sort by lead score descending, take top `limit`
    businesses.sort(key=lambda b: b.lead_score, reverse=True)
    businesses = businesses[:limit]

    return businesses
