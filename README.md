# GeoSmart Advisor

GeoSmart Advisor is a local-first geospatial business intelligence monorepo. It combines a Julia viability core, a Python LangGraph ingestion pipeline, a local SLM report generator, a FastAPI gateway, and a React/Vite dashboard.

## Free Stack Map

Good constraint - forces smarter choices too. Here's every layer mapped to free alternatives, with capability kept intact.

Google Maps is not used anywhere in this stack. It is not free at scale, so the pipeline is built around free replacements from the start.

### Layer 1 - Interface

| Need | Free Solution |
|---|---|
| React + TypeScript | Free everywhere |
| deck.gl maps | Open source, MIT license |
| Tailwind CSS | Free |
| Frontend hosting | Vercel free tier (CI/CD + custom domain) |
| BAI telemetry backend | Supabase free tier |

### Layer 2 - SLM

| Need | Free Solution |
|---|---|
| Model weights | Phi-3-mini or Gemma-2B |
| Inference runtime | Ollama or llama.cpp |
| Fine-tuning compute | Google Colab free tier |
| Fine-tuning framework | Unsloth |

### Layer 3 - Data Pipeline

| Need | Free Replacement |
|---|---|
| Infrastructure / roads / POIs | Overpass API (OSM) - completely free, no key |
| Geocoding | Nominatim (OSM) - free |
| Foot traffic proxy | Foursquare free tier + review count density heuristics |
| Isochrones / walk radius | OpenRouteService free tier |
| Demographics | data.gov.in or Census Bureau API |
| Redis cache | Upstash Redis free tier |
| Structured storage | DuckDB - embedded, zero cost |
| Pipeline orchestration | LangGraph - open source |
| Async HTTP | httpx + asyncio - free |

### Layer 4 - Julia Core

| Need | Free Solution |
|---|---|
| Viability engine | Julia |
| Geospatial statistics | GeoStats.jl |
| Distance calculations | Distances.jl |
| HTTP service | HTTP.jl |

### Free Hosting Recommendation

| Service | Free Option |
|---|---|
| Frontend | Vercel free tier |
| Backend | Fly.io, Render, or Railway free tier |
| Cache | Upstash Redis free tier |
| Existing BAI | Supabase free tier |
| SLM during dev | Ollama local / Fly.io later |

Recommended combo: Vercel for the frontend, Fly.io for FastAPI + Julia, Upstash Redis, Supabase for the existing BAI telemetry, and Ollama locally during development. Total monthly cost: $0.

## One-Command Setup

```bash
git clone <repo-url>
cd geosmart-advisor
cp .env.example .env
ollama pull phi3:mini
docker-compose up --build
```

If you do not have API keys yet, the system still runs in demo mode: the Foursquare agent falls back to mock data and the SLM server falls back to a template report.

## Architecture

```text
Layer 1: Presentation
	React + Vite + deck.gl dashboard on port 3000

Layer 2: Gateway
	FastAPI API on port 8000 orchestrates scoring, reporting, and health checks

Layer 3: Intelligence
	Julia core on port 8001, pipeline on port 8002, SLM server on port 8003

Layer 4: Data + External Services
	OSM, Foursquare, Upstash Redis, DuckDB, Supabase BAI, Ollama on host machine
```

## API Reference

### Julia core `:8001`

```bash
curl http://localhost:8001/health
```

```bash
curl -X POST http://localhost:8001/score \
	-H 'Content-Type: application/json' \
	-d '[{"lat":28.61,"lon":77.21,"demographic_density":12000,"median_income":48000,"infra_proximity_score":0.8,"competitor_count":4,"foot_traffic_proxy":0.7,"zoning_score":0.8,"market_gap_score":0.6}]'
```

```bash
curl -X POST http://localhost:8001/simulate \
	-H 'Content-Type: application/json' \
	-d '{"candidates":[{"lat":28.61,"lon":77.21,"demographic_density":12000,"median_income":48000,"infra_proximity_score":0.8,"competitor_count":4,"foot_traffic_proxy":0.7,"zoning_score":0.8,"market_gap_score":0.6}],"top_n":3}'
```

### Pipeline `:8002`

```bash
curl -X POST http://localhost:8002/analyze \
	-H 'Content-Type: application/json' \
	-d '{"lat":28.61,"lon":77.21,"radius_m":500,"top_n":3,"business_category":"retail"}'
```

```bash
curl -X POST http://localhost:8002/batch_analyze \
	-H 'Content-Type: application/json' \
	-d '{"locations":[{"lat":28.61,"lon":77.21},{"lat":28.62,"lon":77.22}],"radius_m":500,"top_n":2,"business_category":"retail"}'
```

```bash
curl 'http://localhost:8002/history?lat=28.61&lon=77.21&radius_m=500'
```

```bash
curl http://localhost:8002/zones/demo-zone-1
```

### Intelligence `:8003`

```bash
curl http://localhost:8003/health
```

```bash
curl -X POST http://localhost:8003/report \
	-H 'Content-Type: application/json' \
	-d '{"features":{"lat":28.61,"lon":77.21},"score":78.5,"location_name":"Connaught Place"}'
```

```bash
curl -X POST http://localhost:8003/batch_report \
	-H 'Content-Type: application/json' \
	-d '[{"features":{"lat":28.61,"lon":77.21},"score":78.5,"location_name":"Connaught Place"}]'
```

### Gateway `:8000`

```bash
curl http://localhost:8000/api/v1/demo
```

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
	-H 'Content-Type: application/json' \
	-d '{"lat":28.61,"lon":77.21,"radius_m":500,"top_n":3,"business_category":"retail"}'
```

```bash
curl 'http://localhost:8000/api/v1/zones/history?lat=28.61&lon=77.21&radius_m=500'
```

```bash
curl http://localhost:8000/api/v1/zones/demo-zone-1
```

```bash
curl http://localhost:8000/api/v1/health
```

## Free Tier Notes

- OpenStreetMap and Overpass are free to query, which replaces paid map/POI backends.
- Nominatim is free for light development use and powers geocoding and reverse geocoding in the pipeline.
- Foursquare free tier plus review-count heuristics is enough for a usable foot-traffic proxy in demos.
- Upstash Redis has a free tier that is enough for cached lookups and demo-scale usage.
- DuckDB runs embedded in-process, so there is no database bill for local development.
- Supabase has a free tier that can host the existing BAI integration without a paid plan during early demos.
- Ollama is local and free once the model is pulled, which keeps the SLM path GPU-friendly and offline after setup.

## Demo Mode

You can run the stack without any paid API keys.

- The Foursquare agent falls back to mock data when `FOURSQUARE_API_KEY` is missing.
- The SLM server falls back to a template report when Ollama is unavailable or the model is missing.
- The gateway still serves `/api/v1/demo` for a fully synthetic walk-through.
- The pipeline uses free sources only: Overpass, Nominatim, DuckDB, and local scoring.

## Project Structure

- `core/` contains the Julia scoring engine, simulation logic, and HTTP service.
- `pipeline/` contains the LangGraph ingestion pipeline, cache, and persistence layer.
- `intelligence/` contains the local report-generation server and Ollama client.
- `api/` contains the FastAPI gateway that orchestrates pipeline, Julia, and SLM calls.
- `frontend/` contains the React/Vite map dashboard and panel UI.
- `docker-compose.yml` wires the services for one-command startup.
- `.env.example` documents the runtime secrets and free-tier integrations.
- `Makefile` provides short commands for day-to-day local development.

## Cost Summary

- Frontend: $0 with Vercel free tier or local Docker.
- SLM: $0 with Ollama local, Phi-3-mini, or Gemma-2B.
- Pipeline: $0 with free OSM/Nominatim/Upstash/DuckDB.
- Julia core: $0 on any local machine or free VM.
- Existing BAI telemetry: $0 on Supabase free tier.

Total monthly cost: $0.

## Full Free Stack Summary

```text
Frontend    ->  React + deck.gl        ->  Vercel (free)
Telemetry   ->  BAI sensor.js          ->  Supabase (free, already live)
SLM         ->  Phi-3-mini             ->  Ollama local / Fly.io
Pipeline    ->  LangGraph + httpx      ->  Fly.io (free VM)
Cache       ->  Upstash Redis          ->  free tier
Storage     ->  DuckDB                 ->  embedded, zero cost
Data        ->  Overpass + Nominatim + Foursquare free + OpenRouteService
Core        ->  Julia + GeoStats.jl    ->  Fly.io same VM
```

Total monthly cost: $0.

# GeoSmart_Advis
