from __future__ import annotations

import asyncio
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import orjson
import redis.asyncio as redis

DUCKDB_PATH = Path(__file__).resolve().parent / "data" / "geosmart.duckdb"
_REDIS_URL = os.getenv("UPSTASH_REDIS_URL", "").strip()
_REDIS_CLIENT: redis.Redis | None = None
_DUCKDB_LOCK = threading.Lock()

_GEOHASH_ALPHABET = "0123456789bcdefghjkmnpqrstuvwxyz"


def _is_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return lowered.startswith("your_") or lowered in {"your_key_here", "your_upstash_url", "your_supabase_url", "your_anon_key"}


def _ensure_duckdb() -> None:
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _DUCKDB_LOCK:
        connection = duckdb.connect(str(DUCKDB_PATH))
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_observations (
                id VARCHAR,
                lat DOUBLE,
                lon DOUBLE,
                radius_m INTEGER,
                zone_id VARCHAR,
                timestamp TIMESTAMP,
                osm_data VARCHAR,
                foursquare_data VARCHAR,
                zoning_data VARCHAR,
                demographics_data VARCHAR,
                viability_score DOUBLE
            )
            """
        )
        try:
            connection.execute("ALTER TABLE raw_observations ADD COLUMN zone_id VARCHAR")
        except Exception:
            pass
        connection.close()


def _get_redis_client() -> redis.Redis | None:
    global _REDIS_CLIENT
    if not _REDIS_URL or _is_placeholder(_REDIS_URL):
        return None
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = redis.from_url(_REDIS_URL, encoding="utf-8", decode_responses=True)
    return _REDIS_CLIENT


def _encode_geohash(lat: float, lon: float, precision: int = 5) -> str:
    lat_interval = [-90.0, 90.0]
    lon_interval = [-180.0, 180.0]
    geohash: list[str] = []
    is_lon = True
    bit = 0
    ch = 0

    while len(geohash) < precision:
        if is_lon:
            midpoint = (lon_interval[0] + lon_interval[1]) / 2.0
            if lon >= midpoint:
                ch |= 1 << (4 - bit)
                lon_interval[0] = midpoint
            else:
                lon_interval[1] = midpoint
        else:
            midpoint = (lat_interval[0] + lat_interval[1]) / 2.0
            if lat >= midpoint:
                ch |= 1 << (4 - bit)
                lat_interval[0] = midpoint
            else:
                lat_interval[1] = midpoint

        is_lon = not is_lon
        if bit < 4:
            bit += 1
        else:
            geohash.append(_GEOHASH_ALPHABET[ch])
            bit = 0
            ch = 0

    return "".join(geohash)


def cache_key(lat: float, lon: float, radius: int) -> str:
    return f"geosmart:{_encode_geohash(lat, lon, precision=5)}:{int(radius)}"


async def get_cached(key: str) -> dict[str, Any] | None:
    client = _get_redis_client()
    if client is None:
        return None
    payload = await client.get(key)
    if not payload:
        return None
    return json.loads(payload)


async def set_cached(key: str, data: dict[str, Any], ttl: int = 86400) -> None:
    client = _get_redis_client()
    if client is None:
        return
    await client.set(key, orjson.dumps(data).decode("utf-8"), ex=ttl)


def _save_observation_sync(data: dict[str, Any]) -> None:
    _ensure_duckdb()
    connection = duckdb.connect(str(DUCKDB_PATH))
    connection.execute(
        """
        INSERT INTO raw_observations (
            id, lat, lon, radius_m, zone_id, timestamp,
            osm_data, foursquare_data, zoning_data, demographics_data, viability_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            data.get("id", str(uuid.uuid4())),
            float(data["lat"]),
            float(data["lon"]),
            int(data.get("radius_m", 500)),
            data.get("zone_id"),
            data.get("timestamp", datetime.now(timezone.utc)),
            json.dumps(data.get("osm_data", {})),
            json.dumps(data.get("foursquare_data", {})),
            json.dumps(data.get("zoning_data", {})),
            json.dumps(data.get("demographics_data", {})),
            float(data.get("viability_score", 0.0)),
        ],
    )
    connection.close()


async def save_observation(data: dict[str, Any]) -> None:
    await asyncio.to_thread(_save_observation_sync, data)


def _get_historical_sync(lat: float, lon: float, radius: int) -> list[dict[str, Any]]:
    _ensure_duckdb()
    connection = duckdb.connect(str(DUCKDB_PATH))
    rows = connection.execute(
        """
        SELECT id, lat, lon, radius_m, timestamp, osm_data, foursquare_data, zoning_data,
             demographics_data, viability_score, zone_id
        FROM raw_observations
        WHERE radius_m = ?
          AND ABS(lat - ?) <= 0.02
          AND ABS(lon - ?) <= 0.02
        ORDER BY timestamp DESC
        LIMIT 20
        """,
        [int(radius), float(lat), float(lon)],
    ).fetchall()
    connection.close()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append(
            {
                "id": row[0],
                "lat": row[1],
                "lon": row[2],
                "radius_m": row[3],
                "timestamp": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
                "osm_data": json.loads(row[5]) if row[5] else {},
                "foursquare_data": json.loads(row[6]) if row[6] else {},
                "zoning_data": json.loads(row[7]) if row[7] else {},
                "demographics_data": json.loads(row[8]) if row[8] else {},
                "viability_score": row[9],
                "zone_id": row[10],
            }
        )
    return results


async def get_historical(lat: float, lon: float, radius: int) -> list[dict[str, Any]]:
    return await asyncio.to_thread(_get_historical_sync, lat, lon, radius)


def _get_zone_by_id_sync(zone_id: str) -> dict[str, Any] | None:
    _ensure_duckdb()
    connection = duckdb.connect(str(DUCKDB_PATH))
    row = connection.execute(
        """
        SELECT id, lat, lon, radius_m, timestamp, osm_data, foursquare_data, zoning_data,
               demographics_data, viability_score, zone_id
        FROM raw_observations
        WHERE zone_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        [zone_id],
    ).fetchone()
    connection.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "lat": row[1],
        "lon": row[2],
        "radius_m": row[3],
        "timestamp": row[4].isoformat() if hasattr(row[4], "isoformat") else row[4],
        "osm_data": json.loads(row[5]) if row[5] else {},
        "foursquare_data": json.loads(row[6]) if row[6] else {},
        "zoning_data": json.loads(row[7]) if row[7] else {},
        "demographics_data": json.loads(row[8]) if row[8] else {},
        "viability_score": row[9],
        "zone_id": row[10],
    }


async def get_zone_by_id(zone_id: str) -> dict[str, Any] | None:
    return await asyncio.to_thread(_get_zone_by_id_sync, zone_id)
