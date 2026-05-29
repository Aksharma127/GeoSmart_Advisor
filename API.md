# GeoSmart Advisor - API Reference

Complete API documentation for all 5 services.

---

## Gateway API (http://localhost:8000)

Main entry point for the frontend and external clients. All real requests go through this gateway.

### Health Check
```bash
curl -X GET http://localhost:8000/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "pipeline": "ok",
    "julia": "ok",
    "slm": "ok"
  },
  "timestamp": "2026-05-29T12:00:00Z"
}
```

---

### Demo Endpoint (No Setup Required)

Complete walk-through with synthetic data. Use this to test the system without API keys.

```bash
curl -X GET http://localhost:8000/api/v1/demo
```

**Response (200):**
```json
{
  "demo": true,
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "city": "New Delhi",
    "name": "Demo location"
  },
  "analysis": {
    "viability_score": 0.87,
    "foot_traffic_proxy": 450,
    "competition_level": "moderate",
    "demographics": {
      "population_density": 12500,
      "income_level": "middle_to_upper"
    }
  },
  "report": {
    "summary": "This location shows strong viability...",
    "recommendation": "Highly recommended for food service businesses"
  }
}
```

---

### Analyze Single Location

Core analysis: viability scoring + foot traffic + demographics.

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "category": "restaurant",
    "radius_km": 2.0,
    "business_type": "casual_dining"
  }'
```

**Parameters:**
| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `latitude` | float | ✅ | -90 to 90 |
| `longitude` | float | ✅ | -180 to 180 |
| `category` | string | ✅ | "restaurant", "retail", "service", "office", etc. |
| `radius_km` | float | ❌ | Default: 2.0 km |
| `business_type` | string | ❌ | e.g., "casual_dining", "premium", "fast_food" |

**Response (200):**
```json
{
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "New Delhi, India"
  },
  "analysis": {
    "viability_score": 0.87,
    "score_components": {
      "location_centrality": 0.9,
      "foot_traffic_proxy": 0.85,
      "competition_pressure": 0.8,
      "demographics_fit": 0.88
    },
    "foot_traffic_proxy": 450,
    "nearby_competitors": 12,
    "competition_level": "moderate",
    "demographics": {
      "population_density": 12500,
      "median_income": 75000,
      "age_distribution": {
        "18_35": 0.35,
        "35_55": 0.45,
        "55_plus": 0.20
      }
    },
    "amenities_nearby": {
      "transit_access": "high",
      "parking": "moderate",
      "foot_traffic_sources": ["office_district", "residential"]
    }
  },
  "timestamp": "2026-05-29T12:00:00Z"
}
```

---

### Batch Analyze

Analyze multiple locations at once (max 50).

```bash
curl -X POST http://localhost:8000/api/v1/batch_analyze \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "category": "restaurant"
      },
      {
        "latitude": 28.5244,
        "longitude": 77.1855,
        "category": "retail"
      }
    ],
    "radius_km": 2.0
  }'
```

**Response (200):**
```json
{
  "batch_id": "batch_001_20260529",
  "total_locations": 2,
  "results": [
    {
      "location_index": 0,
      "viability_score": 0.87,
      "foot_traffic_proxy": 450
    },
    {
      "location_index": 1,
      "viability_score": 0.72,
      "foot_traffic_proxy": 320
    }
  ],
  "processing_time_ms": 450
}
```

---

### Generate Report

AI-generated business report for a location.

```bash
curl -X POST http://localhost:8000/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "zone_id": "restaurant_delhi_001",
    "report_type": "executive_summary"
  }'
```

**Parameters:**
| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `latitude` | float | ✅ | Location latitude |
| `longitude` | float | ✅ | Location longitude |
| `zone_id` | string | ✅ | Unique identifier for caching |
| `report_type` | string | ❌ | "executive_summary" (default), "detailed", "risk_analysis" |

**Response (200):**
```json
{
  "report_id": "report_001_20260529",
  "zone_id": "restaurant_delhi_001",
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "address": "New Delhi, India"
  },
  "report": {
    "title": "Location Viability Report - Restaurant Zone",
    "executive_summary": "This location in central Delhi shows strong viability for restaurant business with...",
    "key_findings": [
      "High foot traffic from office district",
      "Moderate competition (12 restaurants within 2km)",
      "Affluent demographic with 45% earning 75k+ annually",
      "Excellent transit access (Delhi Metro 0.3km away)"
    ],
    "recommendation": "HIGHLY RECOMMENDED for casual dining or premium restaurant",
    "risk_factors": [
      "Rent in this area is premium (may impact margins)"
    ],
    "generated_by": "Phi-3-mini"
  },
  "timestamp": "2026-05-29T12:00:00Z"
}
```

---

### Get Zone Data

Retrieve cached analysis for a zone.

```bash
curl -X GET "http://localhost:8000/api/v1/zones/restaurant_delhi_001"
```

**Response (200):**
```json
{
  "zone_id": "restaurant_delhi_001",
  "location": {
    "latitude": 28.6139,
    "longitude": 77.2090
  },
  "last_analysis": "2026-05-29T12:00:00Z",
  "cached_data": {
    "viability_score": 0.87,
    "foot_traffic_proxy": 450
  }
}
```

**Response (404):**
```json
{
  "error": "Zone not found",
  "zone_id": "restaurant_delhi_001"
}
```

---

### List Recent Analyses

Get paginated list of recent analyses.

```bash
curl -X GET "http://localhost:8000/api/v1/analyses?limit=10&offset=0"
```

**Response (200):**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "analyses": [
    {
      "id": "analysis_001",
      "zone_id": "restaurant_delhi_001",
      "viability_score": 0.87,
      "timestamp": "2026-05-29T12:00:00Z"
    }
  ]
}
```

---

## Pipeline Service (http://localhost:8002)

**Internal use only** (called by gateway). Handles data ingestion and feature engineering.

### Health Check
```bash
curl -X GET http://localhost:8002/health
```

### Run Analysis Pipeline
```bash
curl -X POST http://localhost:8002/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "category": "restaurant",
    "radius_km": 2.0
  }'
```

**Response (200):**
```json
{
  "features": {
    "osm_features": {
      "nearby_restaurants": 12,
      "transit_distance_km": 0.3
    },
    "foursquare_features": {
      "foot_traffic_proxy": 450,
      "avg_rating": 4.2
    },
    "demographics": {
      "population_density": 12500
    }
  }
}
```

---

## Julia Core (http://localhost:8001)

**Internal use only**. Viability scoring engine.

### Health Check
```bash
curl -X GET http://localhost:8001/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Score Location
```bash
curl -X POST http://localhost:8001/score \
  -H "Content-Type: application/json" \
  -d '[
    {
      "location_centrality": 0.9,
      "foot_traffic_proxy": 450,
      "competition_pressure": 8,
      "population_density": 12500,
      "category": "restaurant"
    }
  ]'
```

**Response (200):**
```json
[
  {
    "viability_score": 0.87,
    "components": {
      "location_centrality": 0.9,
      "foot_traffic": 0.85,
      "competition": 0.8,
      "demographics": 0.88
    }
  }
]
```

### Simulate Candidates
```bash
curl -X POST http://localhost:8001/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [
      {
        "location_centrality": 0.9,
        "foot_traffic_proxy": 450,
        "competition_pressure": 8
      }
    ],
    "top_n": 3
  }'
```

**Response (200):**
```json
{
  "ranked": [
    {
      "rank": 1,
      "viability_score": 0.87
    }
  ]
}
```

---

## SLM Server (http://localhost:8003)

**Internal use only**. Local AI report generation via Ollama.

### Health Check
```bash
curl -X GET http://localhost:8003/health
```

### Generate Report
```bash
curl -X POST http://localhost:8003/report \
  -H "Content-Type: application/json" \
  -d '{
    "context": "restaurant in New Delhi with 0.87 viability...",
    "report_type": "executive_summary"
  }'
```

**Response (200):**
```json
{
  "report": "This location shows strong viability...",
  "model": "phi3:mini",
  "tokens_generated": 250
}
```

---

## Error Responses

All services follow standard HTTP error codes:

### 400 Bad Request
```json
{
  "error": "Invalid parameter",
  "detail": "latitude must be between -90 and 90"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found",
  "detail": "Zone restaurant_delhi_001 not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Failed to connect to Julia core at http://geosmart-core:8001",
  "request_id": "req_001_20260529"
}
```

### 503 Service Unavailable
```json
{
  "error": "Service unavailable",
  "detail": "Pipeline service is down. Fallback to demo data.",
  "fallback": true
}
```

---

## Rate Limiting

With free APIs:
- **Foursquare**: 1000 calls/day (falls back to mock if exceeded)
- **Upstash Redis**: 10k commands/day (demo mode if exceeded)
- **OpenRouteService**: 2000 requests/day

The system gracefully falls back to demo/cached data when limits are hit.

---

## Environment Variables

Control behavior via `.env`:

```bash
# Data Sources
FOURSQUARE_API_KEY=your_key_here              # Leave as "your_key_here" for demo mode
UPSTASH_REDIS_URL=your_upstash_url            # Leave as "your_upstash_url" for demo mode

# Backend Configuration
PIPELINE_URL=http://geosmart-pipeline:8002    # Internal (docker-compose sets this)
JULIA_URL=http://geosmart-core:8001           # Internal (docker-compose sets this)
SLM_URL=http://geosmart-slm:8003              # Internal (docker-compose sets this)
OLLAMA_HOST=http://localhost:11434            # Local GPU on host machine

# Telemetry (optional)
SUPABASE_URL=your_supabase_url                # Existing BAI backend
SUPABASE_ANON_KEY=your_anon_key               # Leave blank for demo mode
```

---

## Testing with Different Tools

### Using curl
```bash
curl -X GET http://localhost:8000/api/v1/demo
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json={
        "latitude": 28.6139,
        "longitude": 77.2090,
        "category": "restaurant"
    }
)
print(response.json())
```

### Using JavaScript
```javascript
const response = await fetch(
  "http://localhost:8000/api/v1/analyze",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      latitude: 28.6139,
      longitude: 77.2090,
      category: "restaurant"
    })
  }
);
const data = await response.json();
```

### Using Postman
1. Import this collection: [Link to postman-collection.json]
2. Set environment variable: `base_url = http://localhost:8000`
3. Run requests from "Demo" folder first
4. Then try "Analyze" and "Report" folders

---

## Pagination

List endpoints support pagination:

```bash
# Get 10 items, skip first 20
curl "http://localhost:8000/api/v1/analyses?limit=10&offset=20"
```

---

## Caching

Results are cached in Upstash Redis (or memory if Redis unavailable):

```bash
# Same request = cached response (< 10ms)
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "category": "restaurant"
  }'

# Cache TTL: 24 hours
# Clear cache by restarting services
```

---

## Demo Mode Behavior

When `.env` contains placeholder values (e.g., `FOURSQUARE_API_KEY=your_key_here`):

1. **Foursquare** → Returns mock foot traffic data
2. **Redis** → Uses in-memory cache (no persistence)
3. **Ollama** → Returns template report if unavailable
4. **Demographics** → Uses cached public datasets

**Demo mode doesn't degrade functionality** - it just uses free fallback data.

---

## Support & Debugging

Check service health:
```bash
curl http://localhost:8000/health
curl http://localhost:8002/health
curl http://localhost:8001/health
curl http://localhost:8003/health
```

View service logs:
```bash
docker-compose logs -f geosmart-api
docker-compose logs -f geosmart-pipeline
docker-compose logs -f geosmart-core
```

For detailed debugging, set environment variable:
```bash
DEBUG=true docker-compose up
```
