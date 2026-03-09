"""Google Places API wrapper — search businesses without websites, download photos."""

import os
from dataclasses import dataclass
from typing import Optional

import googlemaps
import requests

MAX_PHOTOS = 3

CATEGORY_UNSPLASH = {
    "restaurant": "italian-restaurant",
    "food": "italian-food",
    "bar": "coffee-bar",
    "cafe": "cafe-coffee",
    "bakery": "bakery-bread",
    "hair_care": "hair-salon",
    "beauty_salon": "beauty-salon",
    "gym": "gym-fitness",
    "store": "shop-retail",
    "lodging": "hotel-room",
    "health": "medical-clinic",
}
DEFAULT_UNSPLASH = "local-business-italy"


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


def _safe_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("/", "_")[:30]


def _download_photos(
    photos: list[dict], api_key: str, img_dir: str
) -> list[str]:
    """Download up to MAX_PHOTOS from Places API. Returns relative paths for HTML."""
    os.makedirs(img_dir, exist_ok=True)
    paths: list[str] = []

    for i, photo in enumerate(photos[:MAX_PHOTOS]):
        ref = photo["photo_reference"]
        url = (
            f"https://maps.googleapis.com/maps/api/place/photo"
            f"?maxwidth=800&photo_reference={ref}&key={api_key}"
        )
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


def search(
    query: str,
    location: str,
    limit: int,
    api_key: str,
    output_dir: str,
) -> list[BusinessData]:
    """Search Maps for businesses without a website, download their photos."""
    gmaps = googlemaps.Client(key=api_key)

    # Places API returns max ~20 per call; fetch extra to compensate for filtering
    results = gmaps.places(query=f"{query} {location}")
    places = results.get("results", [])[:limit * 2]

    businesses: list[BusinessData] = []

    for place in places:
        if len(businesses) >= limit:
            break

        details = gmaps.place(
            place["place_id"],
            fields=[
                "name", "formatted_address", "formatted_phone_number",
                "rating", "user_ratings_total", "website", "photos",
                "types", "url",
            ],
        ).get("result", {})

        # Skip businesses that already have a website
        if details.get("website"):
            print(f"  Skip: {details.get('name', '?')} — has website")
            continue

        # Determine primary category
        types = details.get("types", ["establishment"])
        category = next(
            (t for t in types if t in CATEGORY_UNSPLASH),
            types[0] if types else "establishment",
        )

        # Download photos
        safe = _safe_name(details.get("name", "unknown"))
        img_dir = os.path.join(output_dir, safe, "img")
        photo_paths = _download_photos(
            details.get("photos", []), api_key, img_dir
        )

        # Unsplash fallback URL
        unsplash_query = CATEGORY_UNSPLASH.get(category, DEFAULT_UNSPLASH)
        fallback_url = f"https://source.unsplash.com/1200x600/?{unsplash_query}"

        biz = BusinessData(
            name=details.get("name", ""),
            place_id=place["place_id"],
            address=details.get("formatted_address", ""),
            phone=details.get("formatted_phone_number"),
            rating=details.get("rating", 0.0),
            reviews=details.get("user_ratings_total", 0),
            category=category,
            maps_url=details.get("url", ""),
            has_photos=len(photo_paths) > 0,
            photo_paths=photo_paths,
            fallback_unsplash_url=fallback_url,
        )
        businesses.append(biz)
        print(f"  Found: {biz.name} — no website ✓")

    return businesses
