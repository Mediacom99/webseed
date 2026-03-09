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


def _fetch_all_pages(gmaps, query: str, location: str) -> list[dict]:
    """Fetch all pages of Places results for a single query string."""
    import time
    results = gmaps.places(query=f"{query} {location}")
    places = list(results.get("results", []))

    while "next_page_token" in results:
        time.sleep(2)  # Google requires a short delay before using next_page_token
        results = gmaps.places(
            query=f"{query} {location}",
            page_token=results["next_page_token"],
        )
        places.extend(results.get("results", []))

    return places


# Synonyms to broaden search when initial query doesn't find enough results
QUERY_VARIANTS = {
    "ristorante": ["trattoria", "osteria", "pizzeria", "tavola calda"],
    "parrucchiere": ["barbiere", "salone bellezza", "hair salon"],
    "bar": ["caffè", "caffetteria", "pub"],
    "pizzeria": ["ristorante pizzeria", "pizza al taglio"],
    "dentista": ["studio dentistico", "odontoiatra"],
    "meccanico": ["autofficina", "carrozzeria", "gommista"],
    "idraulico": ["termoidraulica", "impiantista"],
    "elettricista": ["impianti elettrici"],
    "falegname": ["falegnameria", "arredamenti"],
}


def search(
    query: str,
    location: str,
    limit: int,
    api_key: str,
    output_dir: str,
) -> list[BusinessData]:
    """Search Maps for businesses without a website, download their photos."""
    gmaps = googlemaps.Client(key=api_key)

    # Build list of queries: original + synonyms
    queries = [query] + QUERY_VARIANTS.get(query.lower(), [])
    seen_place_ids: set[str] = set()
    businesses: list[BusinessData] = []

    for q in queries:
        if len(businesses) >= limit:
            break

        print(f"  🔎 Searching: {q} {location}")
        places = _fetch_all_pages(gmaps, q, location)

        for place in places:
            if len(businesses) >= limit:
                break

            place_id = place["place_id"]
            if place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

            details = gmaps.place(
                place_id,
                fields=[
                    "name", "formatted_address", "formatted_phone_number",
                    "rating", "user_ratings_total", "website", "photo",
                    "type", "url",
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
                place_id=place_id,
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
            print(f"  Found: {biz.name} — no website ✓ ({len(businesses)}/{limit})")

    return businesses
