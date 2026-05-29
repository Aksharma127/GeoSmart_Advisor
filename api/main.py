from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi import _rate_limit_exceeded_handler

from clients import close_clients, init_clients
from rate_limit import limiter
from routes.analyze import router as analyze_router
from routes.health import router as health_router
from routes.zones import router as zones_router

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started_at = time.time()
    app.state.uptime_seconds = lambda: time.time() - app.state.started_at
    await init_clients()
    try:
        yield
    finally:
        await close_clients()


app = FastAPI(title="GeoSmart Advisor API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(analyze_router)
app.include_router(zones_router)
app.include_router(health_router)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    logger.info("{} {} -> {} ({}ms)", request.method, request.url.path, response.status_code, round(elapsed_ms, 2))
    return response


@app.get("/api/v1/demo", response_model=None)
@limiter.limit("30/minute")
async def demo(request: Request) -> dict:
    return {
        "request_id": "demo-connaught-place",
        "top_zones": [
            {
                "lat": 28.6315,
                "lon": 77.2167,
                "score": 88.4,
                "zone_id": "demo-zone-1",
                "viability_rating": "Excellent",
                "headline": "Connaught Place shows strong retail viability with dense footfall and robust commercial fit.",
                "top_strengths": [
                    "Dense commercial activity and transit access support high customer throughput.",
                    "The market gap remains favorable for premium or differentiated retail.",
                    "The central business district profile makes discovery and walk-in conversion easier.",
                ],
                "top_risks": [
                    "Competition is intense across nearly every relevant retail category.",
                    "Rent pressure can compress margins if the concept lacks strong unit economics.",
                ],
                "recommendation": "Validate rent-to-revenue ratios and shortlist micro-locations with the highest pedestrian dwell time.",
                "breakdown": {"raw": 0.78, "score": 88.4},
                "data_sources": ["osm", "foursquare", "zoning", "demographics"],
                "is_mock": True,
            }
        ],
        "heatmap_data": [
            {"lat": 28.6310, "lon": 77.2162, "weight": 0.83},
            {"lat": 28.6315, "lon": 77.2167, "weight": 0.88},
            {"lat": 28.6320, "lon": 77.2172, "weight": 0.81},
        ],
        "analysis_summary": "Connaught Place appears highly viable for walk-in driven retail, but execution quality and rental discipline will decide margins.",
        "processing_time_ms": 1.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
