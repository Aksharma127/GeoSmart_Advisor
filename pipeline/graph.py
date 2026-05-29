from __future__ import annotations

import asyncio
import os
from typing import Any, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph
from loguru import logger

from agents.demographics_agent import fetch_demographics
from agents.foursquare_agent import fetch_foursquare_data
from agents.osm_agent import fetch_osm_data
from agents.zoning_agent import fetch_zoning_data
from cache import cache_key, get_cached, get_historical, save_observation, set_cached
from schema import LocationFeatures, PipelineInput, PipelineOutput


class PipelineState(TypedDict, total=False):
    input: PipelineInput
    osm: dict[str, Any]
    foursquare: dict[str, Any]
    zoning: dict[str, Any]
    demographics: dict[str, Any]
    output: PipelineOutput | None
    cache_key: str


def _merge_features(state: PipelineState) -> LocationFeatures:
    pipeline_input = state["input"]
    coordinates = pipeline_input.coordinates
    osm = state.get("osm", {})
    foursquare = state.get("foursquare", {})
    zoning = state.get("zoning", {})
    demographics = state.get("demographics", {})

    demographic_density = float(demographics.get("demographic_density", 0.0))
    median_income = float(demographics.get("median_income", 0.0))
    infra_proximity_score = float(osm.get("infra_proximity_score", 0.0))
    competitor_count = int(foursquare.get("competitor_count", 0))
    foot_traffic_proxy = float(foursquare.get("foot_traffic_proxy", 0.0))
    zoning_score = float(zoning.get("zoning_score", 0.0))
    market_gap_score = float(foursquare.get("market_gap_score", 0.0))

    return LocationFeatures(
        lat=coordinates.lat,
        lon=coordinates.lon,
        demographic_density=demographic_density,
        median_income=median_income,
        infra_proximity_score=max(0.0, min(1.0, infra_proximity_score)),
        competitor_count=max(0, competitor_count),
        foot_traffic_proxy=max(0.0, min(1.0, foot_traffic_proxy)),
        zoning_score=max(0.0, min(1.0, zoning_score)),
        market_gap_score=max(0.0, min(1.0, market_gap_score)),
    )


async def _score_features(features: LocationFeatures) -> dict[str, Any]:
    julia_url = os.getenv("JULIA_URL", "http://localhost:8001")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f"{julia_url.rstrip('/')}/score", json=[features.model_dump()])
            response.raise_for_status()
            scored = response.json()[0]
            return {
                "viability_score": float(scored["score"]),
                "score_breakdown": scored.get("breakdown", {}),
                "zone_id": scored.get("zone_id", 0),
                "score_source": "julia",
            }
    except Exception as error:
        logger.warning("Julia scoring API unavailable, falling back to local calculation: {}", error)
        demographic = max(0.0, min(1.0, features.demographic_density / 20_000.0))
        income = max(0.0, min(1.0, features.median_income / 100_000.0))
        infra = max(0.0, min(1.0, features.infra_proximity_score))
        competitor = max(0.0, min(1.0, 1.0 - (features.competitor_count / 15.0)))
        traffic = max(0.0, min(1.0, features.foot_traffic_proxy))
        zoning = max(0.0, min(1.0, features.zoning_score))
        gap = max(0.0, min(1.0, features.market_gap_score))
        raw = (
            0.20 * demographic
            + 0.25 * income
            + 0.15 * infra
            + 0.15 * competitor
            + 0.10 * traffic
            + 0.10 * zoning
            + 0.05 * gap
        )
        score = 100.0 / (1.0 + pow(2.718281828459045, -6.0 * (raw - 0.5)))
        return {"viability_score": score, "score_breakdown": {}, "zone_id": 0, "score_source": "python_fallback"}


async def osm_node(state: PipelineState) -> dict[str, Any]:
    coordinates = state["input"].coordinates
    return {"osm": await fetch_osm_data(coordinates.lat, coordinates.lon, state["input"].radius_m)}


async def foursquare_node(state: PipelineState) -> dict[str, Any]:
    coordinates = state["input"].coordinates
    return {
        "foursquare": await fetch_foursquare_data(
            coordinates.lat,
            coordinates.lon,
            state["input"].radius_m,
            state["input"].business_category,
        )
    }


async def zoning_node(state: PipelineState) -> dict[str, Any]:
    coordinates = state["input"].coordinates
    return {"zoning": await fetch_zoning_data(coordinates.lat, coordinates.lon)}


async def demographics_node(state: PipelineState) -> dict[str, Any]:
    coordinates = state["input"].coordinates
    return {"demographics": await fetch_demographics(coordinates.lat, coordinates.lon)}


async def aggregator_node(state: PipelineState) -> dict[str, Any]:
    features = _merge_features(state)
    score_data = await _score_features(features)
    raw_data = {
        "osm": state.get("osm", {}),
        "foursquare": state.get("foursquare", {}),
        "zoning": state.get("zoning", {}),
        "demographics": state.get("demographics", {}),
        **score_data,
    }
    output = PipelineOutput(
        features=features,
        raw_data=raw_data,
        sources=[
            state.get("osm", {}).get("source", "osm"),
            state.get("foursquare", {}).get("source", "foursquare"),
            state.get("zoning", {}).get("source", "zoning"),
            state.get("demographics", {}).get("source", "demographics"),
        ],
    )

    observation_record = {
        "lat": features.lat,
        "lon": features.lon,
        "radius_m": state["input"].radius_m,
        "zone_id": score_data.get("zone_id"),
        "osm_data": state.get("osm", {}),
        "foursquare_data": state.get("foursquare", {}),
        "zoning_data": state.get("zoning", {}),
        "demographics_data": state.get("demographics", {}),
        "viability_score": score_data.get("viability_score", 0.0),
    }
    await save_observation(observation_record)

    cached_output = output.model_dump()
    await set_cached(state["cache_key"], cached_output)
    return {"output": output}


def build_graph() -> Any:
    graph = StateGraph(PipelineState)
    graph.add_node("osm_node", osm_node)
    graph.add_node("foursquare_node", foursquare_node)
    graph.add_node("zoning_node", zoning_node)
    graph.add_node("demographics_node", demographics_node)
    graph.add_node("aggregator_node", aggregator_node)
    graph.add_edge(START, "osm_node")
    graph.add_edge(START, "foursquare_node")
    graph.add_edge(START, "zoning_node")
    graph.add_edge(START, "demographics_node")
    graph.add_edge("osm_node", "aggregator_node")
    graph.add_edge("foursquare_node", "aggregator_node")
    graph.add_edge("zoning_node", "aggregator_node")
    graph.add_edge("demographics_node", "aggregator_node")
    graph.add_edge("aggregator_node", END)
    return graph.compile()


PIPELINE_GRAPH = build_graph()


async def run_pipeline(lat: float, lon: float, radius_m: int = 500, business_category: str = "retail") -> PipelineOutput:
    pipeline_input = PipelineInput(coordinates={"lat": lat, "lon": lon}, radius_m=radius_m, business_category=business_category)
    key = cache_key(lat, lon, radius_m)
    cached = await get_cached(key)
    if cached is not None:
        return PipelineOutput.model_validate(cached)

    state: PipelineState = {"input": pipeline_input, "cache_key": key}
    results = await asyncio.gather(
        osm_node(state),
        foursquare_node(state),
        zoning_node(state),
        demographics_node(state),
    )
    for partial in results:
        state.update(partial)

    aggregated = await aggregator_node(state)
    return aggregated["output"]


__all__ = [
    "PIPELINE_GRAPH",
    "PipelineState",
    "aggregator_node",
    "build_graph",
    "demographics_node",
    "foursquare_node",
    "osm_node",
    "run_pipeline",
    "zoning_node",
]
