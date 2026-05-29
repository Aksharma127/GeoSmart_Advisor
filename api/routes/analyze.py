from __future__ import annotations

import asyncio
import math
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from clients import call_julia_simulate, call_pipeline, call_pipeline_batch, call_slm_batch
from models import AnalyzeRequest, AnalyzeResponse, ZoneResult
from rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["analyze"])


def _meters_to_latitude_delta(meters: float) -> float:
    return meters / 111_320.0


def _meters_to_longitude_delta(meters: float, latitude: float) -> float:
    denominator = 111_320.0 * max(math.cos(math.radians(latitude)), 0.01)
    return meters / denominator


def _grid_points(lat: float, lon: float) -> list[dict[str, float]]:
    offsets = [-400.0, -200.0, 0.0, 200.0, 400.0]
    lat_step = _meters_to_latitude_delta(200.0)
    lon_step = _meters_to_longitude_delta(200.0, lat)
    points: list[dict[str, float]] = []
    for row_offset in offsets:
        for col_offset in offsets:
            points.append({"lat": lat + (row_offset / 200.0) * lat_step, "lon": lon + (col_offset / 200.0) * lon_step})
    return points


def _is_mock_payload(raw_data: dict) -> bool:
    for value in raw_data.values():
        if isinstance(value, dict) and value.get("is_mock"):
            return True
    return False


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("30/minute")
async def analyze(request: Request, payload: AnalyzeRequest) -> AnalyzeResponse:
    started = asyncio.get_running_loop().time()
    request_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        central_task = call_pipeline(payload.lat, payload.lon, payload.radius_m, payload.top_n, payload.business_category)
        grid_points = _grid_points(payload.lat, payload.lon)
        grid_task = call_pipeline_batch(grid_points, payload.radius_m, payload.top_n, payload.business_category)
        central_result, grid_outputs = await asyncio.gather(central_task, grid_task)

        features_list = [item["features"] for item in grid_outputs]
        julia_results = await call_julia_simulate(features_list, payload.top_n)

        slm_requests = []
        for result in julia_results:
            matching_feature = next(
                (item["features"] for item in grid_outputs if item["features"]["lat"] == result["lat"] and item["features"]["lon"] == result["lon"]),
                {"lat": result["lat"], "lon": result["lon"]},
            )
            slm_requests.append(
                {
                    "features": matching_feature,
                    "score": result["score"],
                    "location_name": f"Zone {result['zone_id']}",
                }
            )

        slm_reports = await call_slm_batch(slm_requests)

        feature_lookup = {
            (item["features"]["lat"], item["features"]["lon"]): item
            for item in grid_outputs
        }

        top_zones: list[ZoneResult] = []
        for result, report in zip(julia_results, slm_reports):
            feature_entry = feature_lookup.get((result["lat"], result["lon"]), {})
            raw_data = feature_entry.get("raw_data", {})
            top_zones.append(
                ZoneResult(
                    lat=result["lat"],
                    lon=result["lon"],
                    score=float(result["score"]),
                    zone_id=str(result.get("zone_id", "")),
                    viability_rating=report["report"]["viability_rating"],
                    headline=report["report"]["headline"],
                    top_strengths=list(report["report"]["top_strengths"]),
                    top_risks=list(report["report"]["top_risks"]),
                    recommendation=report["report"]["recommendation"],
                    breakdown=dict(result.get("breakdown", {})),
                    data_sources=list(feature_entry.get("sources", [])),
                    is_mock=_is_mock_payload(raw_data) or ("fallback_template" in report.get("raw_text", "")),
                )
            )

        top_zones.sort(key=lambda item: item.score, reverse=True)
        heatmap_data = [
            {
                "lat": item["features"]["lat"],
                "lon": item["features"]["lon"],
                "weight": max(0.0, min(1.0, float(item.get("raw_data", {}).get("viability_score", 0.0)) / 100.0)),
            }
            for item in grid_outputs
        ]
        analysis_summary = slm_reports[0]["report"]["headline"] if slm_reports else central_result["raw_data"].get("summary", "Analysis completed.")

        elapsed_ms = (asyncio.get_running_loop().time() - started) * 1000.0
        return AnalyzeResponse(
            request_id=request_id,
            top_zones=top_zones,
            heatmap_data=heatmap_data,
            analysis_summary=analysis_summary,
            processing_time_ms=elapsed_ms,
            timestamp=timestamp,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
