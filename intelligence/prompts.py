from __future__ import annotations

from textwrap import dedent

SYSTEM_PROMPT = dedent(
    """
    You are a geospatial business intelligence analyst specializing in
    location viability assessment for emerging markets. You analyze
    structured location data and produce concise, actionable reports.
    Focus on local economic realities over national averages.
    Always quantify your assessments. Be direct and specific.
    Respond ONLY in the JSON format specified. No preamble.
    """
).strip()


def build_viability_prompt(features: dict, score: float, location_name: str = "Unknown location") -> str:
    return dedent(
        f"""
        Location name: {location_name}

        Structured location features:
        {features}

        The quantitative viability score is {score}/100.
        Your verbal assessment must be consistent with this score.

        Return JSON with exactly these fields:
        {{
          "headline": "one sentence verdict on this location",
          "viability_rating": "Excellent|Good|Moderate|Poor|Avoid",
          "top_strengths": ["str", "str", "str"],
          "top_risks": ["str", "str"],
          "competitor_analysis": "2 sentences on competitive landscape",
          "demographic_fit": "2 sentences on population-business match",
          "recommendation": "specific, actionable next step for the owner",
          "confidence": 0.0-1.0
        }}

        The quantitative viability score is {score}/100.
        Your verbal assessment must be consistent with this score.
        """
    ).strip()
