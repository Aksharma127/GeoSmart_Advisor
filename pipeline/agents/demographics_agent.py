from __future__ import annotations

from typing import Any

import httpx
import orjson

NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
WORLD_BANK_URL = "https://api.worldbank.org/v2/country/{code}/indicator/SP.POP.TOTL"

COUNTRY_AREA_KM2 = {
    "IN": 3287263,
    "US": 9833520,
    "GB": 242495,
    "CA": 9984670,
    "AU": 7692024,
    "BR": 8515767,
    "DE": 357022,
    "FR": 551695,
    "SG": 734,
}


def _extract_country_and_region(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    address = payload.get("address") or {}
    country_code = address.get("country_code")
    country = address.get("country")
    region = address.get("state") or address.get("province") or address.get("county")
    return (
        str(country_code).upper() if country_code else None,
        str(country) if country else None,
        str(region) if region else None,
    )


async def _reverse_geocode(lat: float, lon: float) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            NOMINATIM_REVERSE_URL,
            params={"lat": lat, "lon": lon, "format": "jsonv2"},
            headers={"User-Agent": "GeoSmart-Advisor/1.0"},
        )
        response.raise_for_status()
        return orjson.loads(response.content)


async def _worldbank_population(country_code: str | None) -> float:
    if not country_code:
        return 0.0
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(WORLD_BANK_URL.format(code=country_code))
        response.raise_for_status()
        payload = orjson.loads(response.content)
        series = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
        for entry in series:
            value = entry.get("value")
            if value is not None:
                return float(value)
    return 0.0


async def _premium_basic_ratio(lat: float, lon: float) -> tuple[int, int]:
    overpass_query = f"""
    [out:json][timeout:30];
    (
      node(around:500,{lat},{lon})[amenity~"^(bank|atm)$"];
      node(around:500,{lat},{lon})[shop~"^(mall|jewelry|electronics|fashion)$"];
      node(around:500,{lat},{lon})[shop~"^(convenience|kiosk|supermarket|general)$"];
      node(around:500,{lat},{lon})[amenity~"^(marketplace)$"];
    );
    out body;
    """.strip()

    premium = 0
    basic = 0
    async with httpx.AsyncClient(timeout=35) as client:
        try:
            response = await client.post(
                "https://overpass-api.de/api/interpreter",
                content=overpass_query.encode("utf-8"),
            )
            response.raise_for_status()
            payload = orjson.loads(response.content)
            for element in payload.get("elements", []):
                tags = element.get("tags", {}) or {}
                amenity = str(tags.get("amenity", "")).lower()
                shop = str(tags.get("shop", "")).lower()
                if amenity in {"bank", "atm"} or shop in {"mall", "jewelry", "electronics", "fashion"}:
                    premium += 1
                elif shop in {"convenience", "kiosk", "supermarket", "general"} or amenity in {"marketplace"}:
                    basic += 1
        except Exception:
            return 0, 0
    return premium, basic


def _estimate_density(population: float, country_code: str | None) -> float:
    area_km2 = COUNTRY_AREA_KM2.get((country_code or "").upper(), 1_000_000.0)
    return population / max(area_km2, 1.0)


def _income_proxy_to_currency(income_proxy_score: float) -> float:
    return round(10_000.0 + (income_proxy_score * 90_000.0), 2)


async def fetch_demographics(lat: float, lon: float) -> dict[str, Any]:
    reverse_payload = await _reverse_geocode(lat, lon)
    country_code, country_name, region_name = _extract_country_and_region(reverse_payload)
    population = await _worldbank_population(country_code)
    demographic_density = _estimate_density(population, country_code)

    premium_count, basic_count = await _premium_basic_ratio(lat, lon)
    ratio = premium_count / max(premium_count + basic_count, 1)
    income_proxy_score = max(0.0, min(1.0, ratio))

    return {
        "source": "demographics",
        "country_code": country_code,
        "country_name": country_name,
        "region_name": region_name,
        "population": population,
        "demographic_density": demographic_density,
        "income_proxy_score": income_proxy_score,
        "median_income": _income_proxy_to_currency(income_proxy_score),
    }
