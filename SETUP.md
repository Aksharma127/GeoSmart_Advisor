# GeoSmart Advisor - Setup Instructions

Complete guide for what **you** need to do to get the system running locally.

## Prerequisites

Install these on your machine first:

### Required
- **Docker** & **Docker Compose** (v3.9+): https://www.docker.com/products/docker-desktop
- **Node.js** 20+: https://nodejs.org (needed for frontend hot reload during dev)
- **Julia** 1.10+: https://julialang.org/downloads (needed for direct Julia development)
- **Ollama**: https://ollama.ai (downloads AI models locally)

### Optional (but recommended for development)
- **Git**: https://git-scm.com
- **VS Code**: https://code.visualstudio.com with Julia + Python extensions
- **Redis CLI**: `brew install redis` (macOS) or `apt install redis-tools` (Linux)
- **curl** or **Postman** (for testing APIs)

---

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd geosmart-advisor

# Copy environment template
cp .env.example .env

# Review .env - no changes needed for demo mode
cat .env
```

### Expected output:
```
FOURSQUARE_API_KEY=your_key_here
UPSTASH_REDIS_URL=your_upstash_url
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
```

---

## Step 2: Download Ollama Model (One-Time)

The SLM server needs a local AI model. Download it once:

```bash
# Download Phi-3-mini (2GB, recommended)
ollama pull phi3:mini

# Alternative: Gemma 2B (lighter, also free)
ollama pull gemma:2b
```

Ollama will run in the background. Check it's working:
```bash
curl http://localhost:11434/api/tags
```

---

## Step 3: Start the Stack

### Option A: One-Command Start (Recommended for testing)
```bash
make dev
# This runs: docker-compose up
```

### Option B: Build from scratch
```bash
make build
# This runs: docker-compose up --build
# (Use this if you changed code in any service)
```

### Option C: Start just Julia core
```bash
make julia
# Useful for testing geospatial logic in isolation
```

### Option D: Demo Mode (works without any API keys)
```bash
make demo
# Automatically creates .env from .env.example if missing
```

**Wait for all services to be healthy** (~2-3 minutes first run, then 30s on subsequent starts):

```
geosmart-core      | Listening on port 8001
geosmart-pipeline  | Application startup complete
geosmart-slm       | Application startup complete
geosmart-api       | Application startup complete
geosmart-frontend  | Local:   http://localhost:3000
```

---

## Step 4: Access the System

Once all services are running:

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend Dashboard** | http://localhost:3000 | Map & business intelligence UI |
| **API Gateway** | http://localhost:8000 | Main API entry point |
| **Julia Core** | http://localhost:8001 | Viability scoring engine |
| **Pipeline** | http://localhost:8002 | Data ingestion (internal only) |
| **SLM Server** | http://localhost:8003 | Report generation (internal only) |

---

## Step 5: Test the API

### Test demo endpoint (no parameters needed)
```bash
curl -X GET http://localhost:8000/api/v1/demo
```

### Analyze a single location
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "category": "restaurant",
    "radius_km": 2
  }'
```

### Get a report for a location
```bash
curl -X POST http://localhost:8000/api/v1/report \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "zone_id": "restaurant-delhi-001"
  }'
```

### Check Julia core directly
```bash
curl -X GET http://localhost:8001/health
```

---

## Step 6: Development Workflow

### Running locally without Docker (faster iteration)

#### Julia Core
```bash
cd core
julia --project=. -e 'include("src/GeoSmartCore.jl")'
```

#### Python Services
```bash
cd pipeline
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

#### Frontend (hot reload)
```bash
cd frontend
npm install
npm run dev
```

### Making code changes

**Python code** (`pipeline/`, `intelligence/`, `api/`):
1. Edit file
2. Service auto-reloads (Uvicorn --reload)
3. No Docker rebuild needed

**Julia code** (`core/src/`):
1. Edit file
2. Rebuild Julia environment: `cd core && julia --project=. -e 'using Pkg; Pkg.instantiate()'`
3. Restart Julia REPL

**Frontend code** (`frontend/src/`):
1. Edit file
2. Vite hot reload happens automatically in browser
3. No rebuild needed

**Docker configuration changed** (Dockerfile, docker-compose.yml):
1. Run `make build` or `docker-compose up --build`

---

## Step 7: (Optional) Add Real API Keys

To use real data instead of demo mode, add these to `.env`:

### Foursquare API Key
- Sign up: https://developer.foursquare.com
- Free tier: 1000 API calls/day
- Set in `.env`:
  ```
  FOURSQUARE_API_KEY=your_actual_key_here
  ```

### Upstash Redis URL
- Sign up: https://upstash.com
- Free tier: 10k commands/day
- Create a database and copy the URL
- Set in `.env`:
  ```
  UPSTASH_REDIS_URL=redis://default:password@host:port
  ```

### Supabase (for existing BAI telemetry)
- Sign up: https://supabase.com
- Free tier: 1GB storage, realtime, 500MB bandwidth
- Set in `.env`:
  ```
  SUPABASE_URL=https://your-project.supabase.co
  SUPABASE_ANON_KEY=your_anon_key_here
  ```

**After updating `.env`:**
```bash
docker-compose restart geosmart-pipeline geosmart-api
# Services will now use real APIs instead of fallback demo data
```

---

## Step 8: Clean Up

### Stop all services
```bash
make clean
# This runs: docker-compose down -v
# (-v flag removes volumes, clearing cached data)
```

### View logs
```bash
docker-compose logs -f geosmart-api
docker-compose logs -f geosmart-pipeline
docker-compose logs -f geosmart-core
```

### Restart a single service
```bash
docker-compose restart geosmart-pipeline
```

---

## Troubleshooting

### "Docker not found"
- Install Docker Desktop: https://www.docker.com/products/docker-desktop

### "Ollama connection refused"
```bash
# Make sure Ollama is running in background
ollama serve
# Or pull a model again
ollama pull phi3:mini
```

### "Port 8000 already in use"
```bash
# Find what's using the port
lsof -i :8000
# Or change docker-compose.yml port mapping
```

### "Julia packages not found"
```bash
cd core
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

### "Frontend shows "Cannot reach API"
1. Check that geosmart-api is running: `curl http://localhost:8000/health`
2. Check frontend env vars: look for VITE_API_URL in frontend/Dockerfile
3. Restart frontend: `docker-compose restart geosmart-frontend`

### "Demo mode not working (still asking for API keys)"
- Make sure `.env.example` values are unchanged (contain `your_` prefix)
- Restart services: `make clean && make dev`

---

## Development Tips

### Test individual services in isolation

```bash
# Julia only
make julia

# Just Python pipeline
cd pipeline
python -m uvicorn main:app --reload --port 8002

# Just React frontend
cd frontend
npm run dev

# Just FastAPI gateway
cd api
python -m uvicorn main:app --reload --port 8000
```

### Check service health

```bash
# API gateway
curl http://localhost:8000/health

# Julia core
curl http://localhost:8001/health

# Pipeline
curl http://localhost:8002/health

# SLM server
curl http://localhost:8003/health
```

### Monitor resource usage
```bash
docker stats
```

### View service dependencies
```bash
# See how services call each other
grep -r "http://" pipeline/ api/ intelligence/ --include="*.py"
```

---

## Architecture Reminder

```
┌─────────────────────────────────────────┐
│     Frontend (React + Vite + deck.gl)   │ :3000
│              localhost                   │
└──────────────────┬──────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────┐
│       API Gateway (FastAPI)             │ :8000
│    Service orchestration + caching      │
└─┬──────────────────┬────────────────┬───┘
  │                  │                │
  ↓                  ↓                ↓
┌──────────┐    ┌──────────┐    ┌───────────┐
│ Pipeline │    │ SLM      │    │ Julia     │
│ (Data)   │    │ (Reports)│    │ (Scoring) │
│ :8002    │    │ :8003    │    │ :8001     │
└────┬─────┘    └────┬─────┘    └───────────┘
     │               │
     ↓               ↓
┌─────────────────────────────┐
│  External APIs & Cache      │
│  Foursquare, Upstash Redis, │
│  OSM, Nominatim, Ollama     │
└─────────────────────────────┘
```

---

## What's in Each Directory

```
geosmart-advisor/
├── core/                  # Julia viability engine
│   ├── src/
│   │   ├── GeoSmartCore.jl          # Entry point
│   │   ├── scoring.jl               # Viability scoring logic
│   │   └── server.jl                # HTTP server
│   ├── Project.toml                 # Julia dependencies
│   └── Dockerfile
│
├── pipeline/              # Python data ingestion (LangGraph)
│   ├── main.py                      # FastAPI entry
│   ├── graph.py                     # LangGraph orchestration
│   ├── cache.py                     # Redis + DuckDB
│   ├── agents/
│   │   ├── osm_agent.py             # OpenStreetMap data
│   │   ├── foursquare_agent.py      # POI data
│   │   ├── zoning_agent.py          # Zone data
│   │   └── demographics_agent.py    # Demographics data
│   ├── requirements.txt
│   └── Dockerfile
│
├── intelligence/          # SLM local inference server
│   ├── server.py                    # FastAPI + Ollama client
│   ├── ollama_client.py             # Ollama integration
│   ├── requirements.txt
│   └── Dockerfile
│
├── api/                   # FastAPI gateway
│   ├── main.py                      # Entry point
│   ├── clients.py                   # Service HTTP clients
│   ├── routes/
│   │   ├── analyze.py               # Analysis endpoint
│   │   ├── zones.py                 # Zone endpoint
│   │   └── demo.py                  # Demo endpoint
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/              # React + Vite dashboard
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   ├── components/
│   │   └── stores/
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml               # Orchestration
├── .env.example                     # Environment template
├── Makefile                         # Development shortcuts
├── README.md                        # Project overview
└── SETUP.md                         # This file
```

---

## Next Steps

1. ✅ Run `make dev` to start everything
2. ✅ Open http://localhost:3000 in your browser
3. ✅ Test `/api/v1/demo` endpoint
4. ✅ Explore data for a real location
5. ✅ (Optional) Add API keys to `.env` for real data
6. ✅ Deploy to Vercel (frontend) + Fly.io (backend)

---

## Cost Summary

**Local development**: $0/month
- Docker: free
- Ollama: free (local GPU)
- Demo data: free (mock fallbacks)

**With optional real APIs**: $0/month
- Foursquare free tier: 1000 calls/day free
- Upstash Redis free tier: 10k commands/day free
- Supabase free tier: unlimited

**Production (recommended)**: $0/month
- Vercel: free tier (frontend)
- Fly.io: free tier (backend VM)
- Upstash Redis: free tier (cache)
- Supabase: free tier (telemetry)

---

## Support

If something breaks:
1. Check [Troubleshooting](#troubleshooting) above
2. Run `docker-compose logs -f` to see all service logs
3. Verify prerequisites are installed
4. Try `make clean && make build` to rebuild from scratch
