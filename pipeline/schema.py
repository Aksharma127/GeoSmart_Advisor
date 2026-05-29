from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Coordinates(BaseModel):
    lat: float
    lon: float


class LocationFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lat: float
    lon: float
    demographic_density: float
    median_income: float
    infra_proximity_score: float
    competitor_count: int
    foot_traffic_proxy: float
    zoning_score: float
    market_gap_score: float


class PipelineInput(BaseModel):
    coordinates: Coordinates
    radius_m: int = Field(default=500, ge=1)
    business_category: str = "retail"


class PipelineOutput(BaseModel):
    features: LocationFeatures
    raw_data: dict[str, Any]
    sources: list[str]
