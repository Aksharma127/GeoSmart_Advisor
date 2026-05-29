from __future__ import annotations

import os
from typing import Any

import httpx
import orjson

FOURSQUARE_URL = "https://api.foursquare.com/v3/places/search"


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith("your_") or lowered == "your_key_here"


def _normalize_category(category: str | None) -> str:
    return (category or os.getenv("FOURSQUARE_CATEGORY", "retail")).strip().lower()


def _place_categories(place: dict[str, Any]) -> list[str]:
    categories = place.get("categories") or []
    names: list[str] = []
    for category in categories:
        if isinstance(category, dict):
            name = category.get("name") or category.get("short_name")
            if name:
                names.append(str(name).lower())
    return names


def _ratings_count(place: dict[str, Any]) -> int:
    stats = place.get("stats") or {}
    if isinstance(stats, dict):
        if stats.get("total_ratings") is not None:
            return int(stats.get("total_ratings") or 0)
        if stats.get("total_reviews") is not None:
            return int(stats.get("total_reviews") or 0)
    return int(place.get("rating_count") or 0)


def _parse_response(results: list[dict[str, Any]], category: str) -> dict[str, Any]:
    total_places = len(results)
    count_in_category = 0
    total_ratings = 0

    for place in results:
        total_ratings += _ratings_count(place)
        category_names = _place_categories(place)
        place_text = " ".join([str(place.get("name", "")).lower(), " ".join(category_names)])
        if category and category in place_text:
            count_in_category += 1

    max_possible = max(total_places * 100, 1)
    foot_traffic_proxy = max(0.0, min(1.0, total_ratings / max_possible))
    saturation = count_in_category / total_places if total_places else 0.0
    market_gap_score = max(0.0, min(1.0, 1.0 - saturation))

    return {
        "source": "foursquare",
        "is_mock": False,
        "results": results,
        "total_places": total_places,
        "count_in_category": count_in_category,
        "competitor_count": count_in_category,
        "foot_traffic_proxy": foot_traffic_proxy,
        "market_gap_score": market_gap_score,
    }


async def fetch_foursquare_data(
    lat: float,
    lon: float,
    radius_m: int,
    category: str | None = None,
) -> dict[str, Any]:
    category_name = _normalize_category(category)
    api_key = os.getenv("FOURSQUARE_API_KEY", "").strip()

    if not api_key or _is_placeholder(api_key):
        return {
            "source": "foursquare",
            "is_mock": True,
            "category": category_name,
            "results": [],
            "total_places": 0,
            "count_in_category": 0,
            "competitor_count": 3,
            "foot_traffic_proxy": 0.45,
            "market_gap_score": 0.65,
            "mock_reason": "FOURSQUARE_API_KEY missing",
        }

    headers = {
        "Accept": "application/json",
        "Authorization": api_key,
    }
    params = {
        "ll": f"{lat},{lon}",
        "radius": int(radius_m),
        "limit": 50,
        "query": category_name,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(FOURSQUARE_URL, headers=headers, params=params)
        response.raise_for_status()
        payload = orjson.loads(response.content)
        results = list(payload.get("results", []))
        parsed = _parse_response(results, category_name)
        parsed["category"] = category_name
        return parsed
