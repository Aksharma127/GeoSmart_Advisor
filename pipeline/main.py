from __future__ import annotations

import asyncio
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from cache import get_historical, get_zone_by_id
from graph import run_pipeline
from schema import Coordinates, PipelineOutput


class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = Field(default=500, ge=1)
    top_n: int = Field(default=1, ge=1)
    business_category: str = "retail"


class BatchAnalyzeRequest(BaseModel):
    locations: list[Coordinates]
    radius_m: int = Field(default=500, ge=1)
    top_n: int = Field(default=1, ge=1)
    business_category: str = "retail"


class HistoryQuery(BaseModel):
    lat: float
    lon: float
    radius_m: int = Field(default=500, ge=1)


app = FastAPI(title="GeoSmart Advisor Pipeline", version="1.0.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


def _score_from_output(output: PipelineOutput) -> float:
    return float(output.raw_data.get("viability_score", 0.0))


@app.post("/analyze", response_model=PipelineOutput)
async def analyze(request: AnalyzeRequest) -> PipelineOutput:
    try:
        return await run_pipeline(request.lat, request.lon, request.radius_m, request.business_category)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.post("/batch_analyze", response_model=list[PipelineOutput])
async def batch_analyze(request: BatchAnalyzeRequest) -> list[PipelineOutput]:
    try:
        outputs = await asyncio.gather(
            *[run_pipeline(location.lat, location.lon, request.radius_m, request.business_category) for location in request.locations]
        )
        sorted_outputs = sorted(outputs, key=_score_from_output, reverse=True)
        if request.top_n > 0:
            sorted_outputs = sorted_outputs[: request.top_n]
        return list(sorted_outputs)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/history")
async def history(lat: float, lon: float, radius_m: int = 500) -> list[dict]:
    try:
        return await get_historical(lat, lon, radius_m)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/zones/{zone_id}")
async def zone_by_id(zone_id: str) -> dict:
    try:
        zone = await get_zone_by_id(zone_id)
        if zone is None:
            raise HTTPException(status_code=404, detail="zone not found")
        return zone
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=False)
