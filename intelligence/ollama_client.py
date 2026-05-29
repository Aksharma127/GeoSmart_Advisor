from __future__ import annotations

import os
from typing import Any

import httpx

OLLAMA_BASE_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = "phi3:mini"


def _base_url() -> str:
    value = OLLAMA_BASE_URL.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return value.rstrip("/")
    return f"http://{value.rstrip('/')}"


async def generate(prompt: str, system: str, max_tokens: int = 512) -> str:
    body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": max_tokens,
        },
    }
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(f"{_base_url()}/api/generate", json=body)
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        return str(payload.get("response", ""))


async def check_ollama_health() -> bool:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{_base_url()}/api/tags")
        response.raise_for_status()
        payload = response.json()

    models = payload.get("models", []) if isinstance(payload, dict) else []
    for model in models:
        if isinstance(model, dict) and model.get("name") == OLLAMA_MODEL:
            return True

    raise RuntimeError("Run: ollama pull phi3:mini")
