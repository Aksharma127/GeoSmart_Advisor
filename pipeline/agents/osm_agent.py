from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
import orjson

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_RATE_LIMIT_LOCK = asyncio.Lock()
_LAST_REQUEST_AT = 0.0


def _build_overpass_query(lat: float, lon: float, radius_m: int) -> str:
    return f"""
[out:json][timeout:35];
(
  node(around:{radius_m},{lat},{lon})[amenity~"^(restaurant|bank|hospital|school|shop)$"];
  way(around:{radius_m},{lat},{lon})[highway];
  node(around:{radius_m},{lat},{lon})[public_transport~"^(platform|stop_position|station)$"];
  way(around:{radius_m},{lat},{lon})[landuse~"^(commercial|residential|industrial)$"];
);
out body;
>;
out skel qt;
""".strip()


async def _respect_rate_limit() -> None:
    global _LAST_REQUEST_AT
    async with _RATE_LIMIT_LOCK:
        elapsed = time.monotonic() - _LAST_REQUEST_AT
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _LAST_REQUEST_AT = time.monotonic()


def _compute_score(road_count: int, transit_count: int, amenity_count: int) -> float:
    weighted = (road_count * 0.4) + (transit_count * 0.4) + (amenity_count * 0.2)
    return max(0.0, min(1.0, weighted / 50.0))


def _parse_overpass_payload(payload: dict[str, Any]) -> dict[str, Any]:
    elements = payload.get("elements", [])
    road_count = 0
    transit_count = 0
    amenity_count = 0
    landuse_tags: list[str] = []

    for element in elements:
        tags = element.get("tags", {}) or {}
        if "highway" in tags:
            road_count += 1
        if tags.get("amenity") in {"restaurant", "bank", "hospital", "school", "shop"}:
            amenity_count += 1
        if tags.get("public_transport") in {"platform", "stop_position", "station"} or tags.get("railway") == "station":
            transit_count += 1
        landuse = tags.get("landuse")
        if landuse:
            landuse_tags.append(str(landuse))

    infra_proximity_score = _compute_score(road_count, transit_count, amenity_count)
    return {
        "road_count": road_count,
        "transit_count": transit_count,
        "amenity_count": amenity_count,
        "landuse_tags": sorted(set(landuse_tags)),
        "infra_proximity_score": infra_proximity_score,
    }


async def fetch_osm_data(lat: float, lon: float, radius_m: int) -> dict[str, Any]:
    query = _build_overpass_query(lat, lon, radius_m)
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            await _respect_rate_limit()
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.post(OVERPASS_URL, content=query.encode("utf-8"))
                response.raise_for_status()
                payload = orjson.loads(response.content)
                parsed = _parse_overpass_payload(payload)
                parsed.update({"source": "overpass", "is_mock": False})
                return parsed
        except Exception as error:
            last_error = error
            if attempt < 2:
                await asyncio.sleep(1.0)

    return {
        "source": "overpass",
        "is_mock": True,
        "error": str(last_error) if last_error else "unknown error",
        "road_count": 0,
        "transit_count": 0,
        "amenity_count": 0,
        "landuse_tags": [],
        "infra_proximity_score": 0.0,
    }
