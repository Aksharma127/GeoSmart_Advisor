from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request

from clients import get_service_health
from rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
@limiter.limit("30/minute")
async def health(request: Request) -> dict:
    statuses = await asyncio.gather(
        get_service_health("julia"),
        get_service_health("pipeline"),
        get_service_health("slm"),
    )
    services = {"julia": statuses[0], "pipeline": statuses[1], "slm": statuses[2]}
    healthy_count = sum(1 for status in statuses if status)
    if healthy_count == 3:
        overall = "healthy"
    elif healthy_count > 0:
        overall = "degraded"
    else:
        overall = "down"
    return {
        "status": overall,
        "services": services,
        "uptime_seconds": max(0.0, request.app.state.uptime_seconds()),
    }
