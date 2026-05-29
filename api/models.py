from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    radius_m: int = Field(default=500, ge=1)
    business_category: str = "retail"
    top_n: int = Field(default=5, ge=1)


class ZoneResult(BaseModel):
    lat: float
    lon: float
    score: float
    zone_id: str
    viability_rating: str
    headline: str
    top_strengths: list[str] = Field(min_length=3, max_length=3)
    top_risks: list[str] = Field(min_length=2, max_length=2)
    recommendation: str
    breakdown: dict[str, Any]
    data_sources: list[str]
    is_mock: bool = False


class AnalyzeResponse(BaseModel):
    request_id: str
    top_zones: list[ZoneResult]
    heatmap_data: list[dict[str, float]]
    analysis_summary: str
    processing_time_ms: float
    timestamp: str
