"""Google Places API (v1) — search businesses without websites, score leads, download photos on demand."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

import requests
from google.api_core import client_options as client_options_lib
from google.api_core import exceptions as google_exceptions
from google.maps.places_v1 import PlacesClient
from google.maps.places_v1.types import places_service, geometry
from google.maps.places_v1.types import place as place_types
from google.type import latlng_pb2

log = logging.getLogger(__name__)

MAX_PHOTOS = 3
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

# Valid Google Place Type IDs for Nearby Search `included_types`.
# Reference: https://developers.google.com/maps/documentation/places/web-service/place-types
# This list contains types most relevant for local business lead generation.
SUPPORTED_PLACE_TYPES: list[str] = [
    # Food & Drink
    "restaurant", "italian_restaurant", "pizza_restaurant", "meal_takeaway",
    "meal_delivery", "cafe", "coffee_shop", "bakery", "bar", "ice_cream_shop",
    "sandwich_shop", "seafood_restaurant", "steak_house", "sushi_restaurant",
    "vegetarian_restaurant", "breakfast_restaurant", "brunch_restaurant",
    "hamburger_restaurant", "indian_restaurant", "chinese_restaurant",
    "japanese_restaurant", "mexican_restaurant", "thai_restaurant",
    "mediterranean_restaurant", "middle_eastern_restaurant", "ramen_restaurant",
    "fast_food_restaurant",
    # Beauty & Wellness
    "hair_salon", "beauty_salon", "barber_shop", "spa", "nail_salon",
    # Health
    "dentist", "dental_clinic", "doctor", "physiotherapist",
    "veterinary_care",
    # Automotive
    "car_repair", "car_wash", "car_dealer",
    # Accommodation
    "hotel", "bed_and_breakfast", "lodging", "guest_house", "motel", "hostel",
    # Fitness
    "gym", "fitness_center",
    # Retail
    "store", "clothing_store", "shoe_store", "jewelry_store", "pet_store",
    "furniture_store", "electronics_store", "book_store", "gift_shop",
    "florist", "pharmacy", "hardware_store", "bicycle_store",
    "sporting_goods_store", "convenience_store", "liquor_store",
    # Services
    "laundry", "locksmith", "plumber", "electrician", "roofing_contractor",
    "moving_company", "painter", "real_estate_agency", "travel_agency",
    "insurance_agency", "accounting", "lawyer",
]

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
    photo_refs: list[str] = field(default_factory=list)  # Places API photo resource names for deferred download
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
# Places SDK client (lazy singleton)
# ---------------------------------------------------------------------------

_client: PlacesClient | None = None

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


def _get_client(api_key: str) -> PlacesClient:
    global _client
    if _client is None:
        options = client_options_lib.ClientOptions(api_key=api_key)
        _client = PlacesClient(client_options=options)
    return _client


# ---------------------------------------------------------------------------
# Places SDK search helpers
# ---------------------------------------------------------------------------

def _search_text(
    api_key: str,
    query: str,
    location_bias: tuple[float, float, float] | None = None,
    page_size: int = 20,
) -> list[place_types.Place]:
    """Text Search (New). Returns up to page_size results."""
    client = _get_client(api_key)
    request = places_service.SearchTextRequest(
        text_query=query,
        language_code="it",
        max_result_count=min(page_size, 20),
    )
    if location_bias:
        lat, lng, radius = location_bias
        request.location_bias = places_service.SearchTextRequest.LocationBias(
            circle=geometry.Circle(
                center=latlng_pb2.LatLng(latitude=lat, longitude=lng),
                radius=radius,
            )
        )
    response = client.search_text(  # type: ignore[reportUnknownMemberType]
        request=request,
        metadata=[("x-goog-fieldmask", _SEARCH_FIELD_MASK)],
    )
    return list(response.places)


def _search_nearby(
    api_key: str,
    lat: float,
    lng: float,
    radius: float,
    included_types: list[str] | None = None,
    page_size: int = 20,
) -> list[place_types.Place]:
    """Nearby Search (New). Returns up to page_size results."""
    client = _get_client(api_key)
    request = places_service.SearchNearbyRequest(
        location_restriction=places_service.SearchNearbyRequest.LocationRestriction(
            circle=geometry.Circle(
                center=latlng_pb2.LatLng(latitude=lat, longitude=lng),
                radius=min(radius, 50000.0),
            )
        ),
        language_code="it",
        max_result_count=min(page_size, 20),
    )
    if included_types:
        request.included_types = included_types

    response = client.search_nearby(  # type: ignore[reportUnknownMemberType]
        request=request,
        metadata=[("x-goog-fieldmask", _SEARCH_FIELD_MASK)],
    )
    return list(response.places)


def _get_place_details(api_key: str, place_id: str) -> place_types.Place:
    """Place Details (New). Full enrichment for a single place."""
    client = _get_client(api_key)
    return client.get_place(  # type: ignore[reportUnknownMemberType]
        request=places_service.GetPlaceRequest(name=f"places/{place_id}"),
        metadata=[("x-goog-fieldmask", _DETAIL_FIELD_MASK)],
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
# Photo download (via SDK + requests for image bytes)
# ---------------------------------------------------------------------------

def _extract_photo_refs(photos: Any) -> list[str]:
    """Extract photo resource names from Places API response for deferred download."""
    refs: list[str] = []
    for photo in list(photos)[:MAX_PHOTOS]:
        if photo.name:
            refs.append(photo.name)
    return refs


def download_photos(
    photo_refs: list[str], api_key: str, img_dir: str
) -> list[str]:
    """Download photos by resource name. Returns relative paths (e.g. 'img/photo1.jpg')."""
    os.makedirs(img_dir, exist_ok=True)
    client = _get_client(api_key)
    paths: list[str] = []

    for i, photo_name in enumerate(photo_refs):
        try:
            photo_media = client.get_photo_media(  # type: ignore[reportUnknownMemberType]
                request=places_service.GetPhotoMediaRequest(
                    name=f"{photo_name}/media",
                    max_width_px=800,
                )
            )
            resp = requests.get(photo_media.photo_uri, timeout=10)
            if resp.status_code == 200:
                path = os.path.join(img_dir, f"photo{i + 1}.jpg")
                with open(path, "wb") as f:
                    f.write(resp.content)
                paths.append(f"img/photo{i + 1}.jpg")
        except (google_exceptions.GoogleAPIError, requests.RequestException):
            continue

    return paths


# ---------------------------------------------------------------------------
# Lead scoring
# ---------------------------------------------------------------------------

def _compute_pre_score(p: place_types.Place) -> int:
    """Quick 0-60 score from Stage 1 fields for ranking before enrichment.

    Uses only fields available in _SEARCH_FIELD_MASK (zero extra cost).
    """
    score = 0.0

    # Rating (max 20)
    rating = p.rating
    if rating >= 4.5:
        score += 20
    elif rating >= 4.0:
        score += 10 + (rating - 4.0) * 20
    elif rating >= 3.5:
        score += 5

    # Review count (max 20)
    reviews = p.user_rating_count
    if reviews >= 200:
        score += 20
    elif reviews >= 100:
        score += 15
    elif reviews >= 50:
        score += 10
    elif reviews >= 10:
        score += 5

    # Business status (max 10)
    if p.business_status and p.business_status.name == "OPERATIONAL":
        score += 10

    # Category tier (max 10)
    primary_type = p.primary_type or ""
    if primary_type in _HIGH_TIER_CATEGORIES:
        score += 10
    elif primary_type in _MID_TIER_CATEGORIES:
        score += 5

    return int(score)


def _compute_lead_score(details: place_types.Place) -> int:
    """Compute 0-100 lead score from enriched place details."""
    score = 0.0

    # Rating: 4.5+ = 20, 4.0-4.5 = 10-20, 3.5-4.0 = 5
    rating = details.rating
    if rating >= 4.5:
        score += 20
    elif rating >= 4.0:
        score += 10 + (rating - 4.0) * 20
    elif rating >= 3.5:
        score += 5

    # Review count: log scale
    reviews = details.user_rating_count
    if reviews >= 200:
        score += 20
    elif reviews >= 100:
        score += 15
    elif reviews >= 50:
        score += 10
    elif reviews >= 10:
        score += 5

    # Price level (enum: 0 = unspecified, falsy)
    price_map = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 3,
        "PRICE_LEVEL_MODERATE": 8,
        "PRICE_LEVEL_EXPENSIVE": 12,
        "PRICE_LEVEL_VERY_EXPENSIVE": 15,
    }
    if details.price_level:
        score += price_map.get(details.price_level.name, 0)

    # Opening hours
    if details.regular_opening_hours:
        score += 10

    # Business status (enum: 0 = unspecified)
    if details.business_status and details.business_status.name == "OPERATIONAL":
        score += 10

    # Category tier
    primary_type = details.primary_type or ""
    if primary_type in _HIGH_TIER_CATEGORIES:
        score += 10
    elif primary_type in _MID_TIER_CATEGORIES:
        score += 5

    # Review recency (any review within last 6 months)
    if details.reviews:
        cutoff = datetime.now(timezone.utc) - timedelta(days=180)
        for review in list(details.reviews)[:5]:
            if review.publish_time:
                try:
                    # proto-plus wraps Timestamp as DatetimeWithNanoseconds (datetime subclass)
                    if review.publish_time > cutoff:  # type: ignore[operator]
                        score += 10
                        break
                except (ValueError, TypeError):
                    pass

    # Has photos
    if details.photos:
        score += 5

    return min(int(score), 100)


def _extract_enrichment(details: place_types.Place) -> dict[str, Any]:
    """Extract enrichment fields from place details response."""
    # Opening hours summary
    hours = details.regular_opening_hours
    opening_summary: str | None = None
    if hours and hours.weekday_descriptions:
        opening_summary = "; ".join(hours.weekday_descriptions)

    # Payment options
    accepts_cc: bool | None = None
    if details.payment_options:
        accepts_cc = bool(details.payment_options.accepts_credit_cards)

    # Editorial summary
    editorial_text: str | None = None
    if details.editorial_summary and details.editorial_summary.text:
        editorial_text = details.editorial_summary.text

    # Review texts (up to 5, truncated to 200 chars)
    review_texts: list[str] = []
    for review in list(details.reviews)[:5]:
        if review.text and review.text.text:
            review_texts.append(review.text.text[:200])

    return {
        "price_level": details.price_level.name if details.price_level else None,
        "business_status": details.business_status.name if details.business_status else "OPERATIONAL",
        "primary_type": details.primary_type or None,
        "types": list(details.types) if details.types else None,
        "has_opening_hours": bool(hours),
        "opening_hours_summary": opening_summary,
        "accepts_credit_cards": accepts_cc,
        "editorial_summary": editorial_text,
        "review_texts": review_texts or None,
    }


# ---------------------------------------------------------------------------
# Helper: extract display name from Place object
# ---------------------------------------------------------------------------

def _display_name(p: place_types.Place) -> str:
    return p.display_name.text if p.display_name else "?"


# ---------------------------------------------------------------------------
# Business enrichment (Stage 2 — called per-business from `enrich` step)
# ---------------------------------------------------------------------------

def enrich_business(
    place_id: str,
    name: str,
    category: str,
    api_key: str,
    results_dir: str,
    only_media: bool = False,
    existing_photo_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Enrich a single business with Place Details + photo download.

    Args:
        place_id: Google place ID.
        name: Business display name (for directory naming).
        category: Primary category (for Unsplash fallback).
        api_key: Google API key.
        results_dir: Base results directory (e.g. "results/").
        only_media: If True, skip Place Details and only download photos.
        existing_photo_refs: Photo refs already stored in DB (used with only_media).

    Returns:
        Dict of enriched fields to merge into DB. Includes "has_website": True
        if a website was discovered during enrichment (caller should handle).
    """
    result: dict[str, Any] = {}
    photo_refs: list[str] = existing_photo_refs or []

    # ── Place Details (unless only_media with existing refs) ──
    if not only_media or not photo_refs:
        details = _get_place_details(api_key, place_id)

        # Website check
        if details.website_uri:
            return {"has_website": True}

        if not only_media:
            # Full enrichment
            enrichment = _extract_enrichment(details)
            lead_score = _compute_lead_score(details)

            # Phone
            phone = details.international_phone_number or details.national_phone_number or None

            result.update({
                "phone": phone or "",
                "lead_score": lead_score,
                **enrichment,
            })

        # Extract photo refs from details
        photo_refs = _extract_photo_refs(details.photos) if details.photos else []
        result["photo_refs"] = photo_refs

    # ── Photo download ──
    safe = safe_name(name)
    img_dir = os.path.join(results_dir, safe, "img")

    if photo_refs:
        photo_paths = download_photos(photo_refs, api_key, img_dir)
        result["photo_paths"] = photo_paths
        result["has_photos"] = len(photo_paths) > 0
    else:
        result["photo_paths"] = []
        result["has_photos"] = False

    # Unsplash fallback removed — source.unsplash.com is dead (410 Gone since 2024)
    result["fallback_unsplash_url"] = ""

    return result


# ---------------------------------------------------------------------------
# Main search function (Stage 1 only — cheap discovery)
# ---------------------------------------------------------------------------

def search(
    query: str,
    location: str,
    limit: int,
    api_key: str,
    types: list[str],
    min_score: int = 0,
    grid_size: int = 3,
    skip_place_ids: set[str] | None = None,
) -> list[BusinessData]:
    """Discover businesses without a website (Stage 1 only — no Place Details calls).

    Uses Nearby Search (grid) + Text Search to find candidates, filters by
    no-website + operational, ranks by pre-score, and returns the top ``limit``.

    Enrichment (Place Details, photos) happens in a separate ``enrich`` step.

    Args:
        query: Free-text query for Text Search (any language, e.g. "ristorante").
        location: City/area name (e.g. "Milano, Italy").
        limit: Max *new* businesses to return.
        api_key: Google API key (works with both Places and Geocoding APIs).
        types: Google Place Type IDs for Nearby Search (e.g. ["restaurant", "italian_restaurant"]).
        min_score: Minimum pre-score (0-60) to include in results.
        grid_size: Grid dimension (2=4 cells, 3=9 cells).
        skip_place_ids: Place IDs already known (DB + blacklist). Skipped so
            ``limit`` counts only genuinely new businesses.
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

    # ── Stage 1: Discovery ──
    print(f"\n  Stage 1: Discovery (types: {types})")
    seen_ids: set[str] = set()
    candidates: list[place_types.Place] = []

    # 1a. Grid-based Nearby Search
    if center_lat is not None and center_lng is not None:
        grid = _generate_grid(center_lat, center_lng, grid_size)
        print(f"  Grid: {grid_size}x{grid_size} = {len(grid)} cells")

        for i, (lat, lng, radius) in enumerate(grid):
            try:
                places = _search_nearby(api_key, lat, lng, radius, included_types=types)
                new = 0
                for p in places:
                    pid = p.id
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        candidates.append(p)
                        new += 1
                log.debug("Grid cell %d/%d: %d results, %d new", i + 1, len(grid), len(places), new)
            except google_exceptions.GoogleAPIError as e:
                log.warning("Nearby search failed for grid cell %d: %s", i + 1, e)

    # 1b. Text Search for broader coverage
    location_bias: tuple[float, float, float] | None = None
    if center_lat is not None and center_lng is not None:
        location_bias = (center_lat, center_lng, 5000.0)

    text_queries = [f"{query} {location}"]
    for t in types:
        tq = f"{t.replace('_', ' ')} {location}"
        if tq not in text_queries:
            text_queries.append(tq)

    for tq in text_queries:
        try:
            print(f"  Text search: {tq}")
            places = _search_text(api_key, tq, location_bias=location_bias)
            new = 0
            for p in places:
                pid = p.id
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    candidates.append(p)
                    new += 1
            log.debug("Text search '%s': %d results, %d new", tq, len(places), new)
        except google_exceptions.GoogleAPIError as e:
            log.warning("Text search failed for '%s': %s", tq, e)

    # ── Filter Stage 1 candidates ──
    filtered: list[place_types.Place] = []
    for p in candidates:
        # Skip businesses with websites
        if p.website_uri:
            log.debug("Skip (has website): %s", _display_name(p))
            continue
        # Skip non-operational businesses
        status = p.business_status.name if p.business_status else ""
        if status not in ("OPERATIONAL", "BUSINESS_STATUS_UNSPECIFIED", ""):
            log.debug("Skip (status %s): %s", status, _display_name(p))
            continue
        filtered.append(p)

    print(f"\n  Stage 1 complete: {len(candidates)} found, {len(filtered)} without website")

    # ── Skip known place_ids ──
    _skip = skip_place_ids or set()
    eligible = [p for p in filtered if p.id not in _skip]
    skipped_known = len(filtered) - len(eligible)
    if skipped_known:
        print(f"  Skipping {skipped_known} already-known businesses")

    # ── Pre-score and rank ──
    scored: list[tuple[int, place_types.Place]] = [
        (_compute_pre_score(p), p) for p in eligible
    ]
    scored.sort(key=lambda t: t[0], reverse=True)

    # Apply min_score filter and take top `limit`
    businesses: list[BusinessData] = []
    for pre_score, p in scored:
        if pre_score < min_score:
            log.debug("Skip (pre-score %d < %d): %s", pre_score, min_score, _display_name(p))
            continue

        primary_type = p.primary_type or ""
        category = primary_type or "establishment"

        biz = BusinessData(
            name=_display_name(p),
            place_id=p.id,
            address=p.formatted_address or "",
            phone=None,
            rating=p.rating,
            reviews=p.user_rating_count,
            category=category,
            maps_url=p.google_maps_uri or "",
            has_photos=False,
            photo_paths=[],
            photo_refs=[],
            fallback_unsplash_url="",
            lead_score=pre_score,
            business_status=p.business_status.name if p.business_status else "OPERATIONAL",
            primary_type=primary_type or None,
        )
        businesses.append(biz)
        print(f"  [{len(businesses)}] {biz.name} — pre-score:{pre_score} rating:{biz.rating} reviews:{biz.reviews}")

        if len(businesses) >= limit:
            break

    return businesses
