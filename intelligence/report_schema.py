from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ViabilityReport(BaseModel):
    headline: str
    viability_rating: Literal["Excellent", "Good", "Moderate", "Poor", "Avoid"]
    top_strengths: list[str] = Field(min_length=3, max_length=3)
    top_risks: list[str] = Field(min_length=2, max_length=2)
    competitor_analysis: str
    demographic_fit: str
    recommendation: str
    confidence: float


class ReportRequest(BaseModel):
    features: dict
    score: float
    location_name: str = "Unknown location"


class ReportResponse(BaseModel):
    report: ViabilityReport
    raw_text: str
    generation_time_ms: float
    model: str = "phi3:mini"
