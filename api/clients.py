from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx
from loguru import logger

PIPELINE_URL = os.getenv("PIPELINE_URL", "http://localhost:8002")
JULIA_URL = os.getenv("JULIA_URL", "http://localhost:8001")
SLM_URL = os.getenv("SLM_URL", "http://localhost:8003")

_PIPELINE_CLIENT: httpx.AsyncClient | None = None
_JULIA_CLIENT: httpx.AsyncClient | None = None
_SLM_CLIENT: httpx.AsyncClient | None = None


async def init_clients() -> None:
    global _PIPELINE_CLIENT, _JULIA_CLIENT, _SLM_CLIENT
    if _PIPELINE_CLIENT is None:
        _PIPELINE_CLIENT = httpx.AsyncClient(base_url=PIPELINE_URL, timeout=30.0)
    if _JULIA_CLIENT is None:
        _JULIA_CLIENT = httpx.AsyncClient(base_url=JULIA_URL, timeout=30.0)
    if _SLM_CLIENT is None:
        _SLM_CLIENT = httpx.AsyncClient(base_url=SLM_URL, timeout=30.0)


async def close_clients() -> None:
    global _PIPELINE_CLIENT, _JULIA_CLIENT, _SLM_CLIENT
    clients = [_PIPELINE_CLIENT, _JULIA_CLIENT, _SLM_CLIENT]
    for client in clients:
        if client is not None:
            await client.aclose()
    _PIPELINE_CLIENT = None
    _JULIA_CLIENT = None
    _SLM_CLIENT = None


def _client_or_raise(client: httpx.AsyncClient | None, name: str) -> httpx.AsyncClient:
    if client is None:
        raise RuntimeError(f"{name} client has not been initialized")
    return client


async def _request_json(client: httpx.AsyncClient, method: str, path: str, *, json_payload: Any = None, params: dict[str, Any] | None = None) -> Any:
    delay = 0.5
    last_error: Exception | None = None
    for attempt in range(3):
        start = time.perf_counter()
        try:
            response = await client.request(method, path, json=json_payload, params=params)
            response.raise_for_status()
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.info("{} {} {}ms", method.upper(), str(client.base_url) + path, round(latency_ms, 2))
            return response.json()
        except Exception as error:
            last_error = error
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.warning("{} {} failed after {}ms: {}", method.upper(), str(client.base_url) + path, round(latency_ms, 2), error)
            if attempt < 2:
                await asyncio.sleep(delay)
                delay *= 2
    raise RuntimeError(f"Request to {path} failed") from last_error


async def call_pipeline(lat: float, lon: float, radius_m: int, top_n: int, business_category: str) -> dict[str, Any]:
    client = _client_or_raise(_PIPELINE_CLIENT, "pipeline")
    payload = {
        "lat": lat,
        "lon": lon,
        "radius_m": radius_m,
        "top_n": top_n,
        "business_category": business_category,
    }
    return await _request_json(client, "POST", "/analyze", json_payload=payload)


async def call_pipeline_batch(locations: list[dict[str, Any]], radius_m: int, top_n: int, business_category: str) -> list[dict[str, Any]]:
    client = _client_or_raise(_PIPELINE_CLIENT, "pipeline")
    payload = {
        "locations": locations,
        "radius_m": radius_m,
        "top_n": top_n,
        "business_category": business_category,
    }
    result = await _request_json(client, "POST", "/batch_analyze", json_payload=payload)
    return list(result)


async def call_pipeline_history(lat: float, lon: float, radius_m: int) -> list[dict[str, Any]]:
    client = _client_or_raise(_PIPELINE_CLIENT, "pipeline")
    result = await _request_json(client, "GET", "/history", params={"lat": lat, "lon": lon, "radius_m": radius_m})
    return list(result)


async def call_pipeline_zone(zone_id: str) -> dict[str, Any]:
    client = _client_or_raise(_PIPELINE_CLIENT, "pipeline")
    return await _request_json(client, "GET", f"/zones/{zone_id}")


async def call_julia_score(features_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client = _client_or_raise(_JULIA_CLIENT, "julia")
    result = await _request_json(client, "POST", "/score", json_payload=features_list)
    return list(result)


async def call_julia_simulate(candidates: list[dict[str, Any]], top_n: int) -> list[dict[str, Any]]:
    client = _client_or_raise(_JULIA_CLIENT, "julia")
    payload = {"candidates": candidates, "top_n": top_n}
    result = await _request_json(client, "POST", "/simulate", json_payload=payload)
    return list(result)


async def call_slm_report(features: dict[str, Any], score: float, location_name: str = "Unknown location") -> dict[str, Any]:
    client = _client_or_raise(_SLM_CLIENT, "slm")
    payload = {"features": features, "score": score, "location_name": location_name}
    return await _request_json(client, "POST", "/report", json_payload=payload)


async def call_slm_batch(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client = _client_or_raise(_SLM_CLIENT, "slm")
    result = await _request_json(client, "POST", "/batch_report", json_payload=requests)
    return list(result)


async def get_service_health(service: str) -> bool:
    client_map = {
        "pipeline": _PIPELINE_CLIENT,
        "julia": _JULIA_CLIENT,
        "slm": _SLM_CLIENT,
    }
    base_client = _client_or_raise(client_map[service], service)
    try:
        await _request_json(base_client, "GET", "/health")
        return True
    except Exception:
        return False
