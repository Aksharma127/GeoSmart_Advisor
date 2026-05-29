from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from clients import call_pipeline_history, call_pipeline_zone
from rate_limit import limiter

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get("/history")
@limiter.limit("30/minute")
async def history(request: Request, lat: float, lon: float, radius_m: int = 500) -> list[dict]:
    try:
        return (await call_pipeline_history(lat, lon, radius_m))[:10]
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/{zone_id}")
@limiter.limit("30/minute")
async def zone(request: Request, zone_id: str) -> dict:
    try:
        result = await call_pipeline_zone(zone_id)
        return result
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
