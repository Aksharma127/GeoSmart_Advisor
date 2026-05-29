from __future__ import annotations

from typing import Any

import httpx
import orjson

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def _build_overpass_query(lat: float, lon: float) -> str:
    return f"""
[out:json][timeout:30];
(
  way(around:200,{lat},{lon})[landuse~"^(commercial|retail|mixed|residential|industrial)$"];
  node(around:200,{lat},{lon})[landuse~"^(commercial|retail|mixed|residential|industrial)$"];
);
out body;
>;
out skel qt;
""".strip()


def _zoning_score_from_tags(landuse_tags: list[str], address_context: dict[str, Any]) -> float:
    normalized_tags = {tag.lower() for tag in landuse_tags}
    address_text = " ".join(str(value).lower() for value in address_context.values())

    if normalized_tags & {"commercial", "retail"}:
        return 1.0
    if "mixed" in normalized_tags or "mixed_use" in address_text:
        return 0.75
    if "residential" in normalized_tags and ("commercial" in address_text or "retail" in address_text):
        return 0.5
    if "industrial" in normalized_tags:
        return 0.2
    return 0.4


async def fetch_zoning_data(lat: float, lon: float) -> dict[str, Any]:
    landuse_tags: list[str] = []
    address_context: dict[str, Any] = {}

    overpass_query = _build_overpass_query(lat, lon)
    async with httpx.AsyncClient(timeout=35) as client:
        try:
            response = await client.post(OVERPASS_URL, content=overpass_query.encode("utf-8"))
            response.raise_for_status()
            payload = orjson.loads(response.content)
            for element in payload.get("elements", []):
                tags = element.get("tags", {}) or {}
                landuse = tags.get("landuse")
                if landuse:
                    landuse_tags.append(str(landuse))
        except Exception:
            landuse_tags = []

        try:
            reverse_response = await client.get(
                NOMINATIM_REVERSE_URL,
                params={"lat": lat, "lon": lon, "format": "jsonv2"},
                headers={"User-Agent": "GeoSmart-Advisor/1.0"},
            )
            reverse_response.raise_for_status()
            address_context = orjson.loads(reverse_response.content)
        except Exception:
            address_context = {}

    zoning_score = _zoning_score_from_tags(landuse_tags, address_context)
    return {
        "source": "zoning",
        "landuse_tags": sorted(set(landuse_tags)),
        "address_context": address_context,
        "zoning_score": zoning_score,
    }
