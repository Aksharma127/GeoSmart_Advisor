DOCKER_COMPOSE_V1 := $(shell command -v docker-compose 2>/dev/null)
DOCKER_COMPOSE_V2 := $(shell command -v docker 2>/dev/null)
COMPOSE ?= $(if $(DOCKER_COMPOSE_V1),docker-compose,$(if $(DOCKER_COMPOSE_V2),docker compose,))
JULIAUP_LAUNCHER := $(HOME)/.juliaup/bin/julialauncher
JULIA ?= $(if $(wildcard $(JULIAUP_LAUNCHER)),$(JULIAUP_LAUNCHER) +release,julia)

.PHONY: check-compose dev build julia demo clean local-core local-pipeline local-slm local-api local-frontend

check-compose:
	@if [ -z "$(COMPOSE)" ]; then \
		echo "Docker is not installed or not on PATH."; \
		echo "Install Docker/Compose, then retry."; \
		echo "On this Fedora repo set, use Podman Docker compatibility:"; \
		echo "  sudo dnf install -y podman podman-docker docker-compose"; \
		echo "  systemctl --user enable --now podman.socket"; \
		echo "  export DOCKER_HOST=unix:///run/user/$$UID/podman/podman.sock"; \
		exit 127; \
	fi

dev: check-compose
	$(COMPOSE) up

build: check-compose
	$(COMPOSE) up --build

julia: check-compose
	$(COMPOSE) up --build geosmart-core

demo: check-compose
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up --build

clean: check-compose
	$(COMPOSE) down -v

local-core:
	cd core && $(JULIA) --project=. src/GeoSmartCore.jl

local-pipeline:
	cd pipeline && python3 -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

local-slm:
	cd intelligence && python3 -m uvicorn server:app --host 0.0.0.0 --port 8003 --reload

local-api:
	cd api && python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

local-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 3000
