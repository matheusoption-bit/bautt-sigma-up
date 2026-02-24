"""
Testes reais de rate limiting contra o middleware SmartRateLimiter.

Verifica:
  1. Requisições normais passam (200)
  2. Acima do limite retorna 429
  3. Endpoint /health NÃO é limitado
"""
from __future__ import annotations

import json as _json
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from atlas_api.middleware.rate_limiter import SmartRateLimiter
from atlas_api.schemas import TerrainMetricsInput, ATLASReportResponse
from atlas_engine.atlas_engine import ATLASEngine

# ---- Carrega ruleset real (uma vez) ----
_RULESET_PATH = (
    Path(__file__).resolve().parents[3]
    / "atlas-engine"
    / "config"
    / "atlas_ruleset_v0.2.json"
)
_RULESET = _json.loads(_RULESET_PATH.read_text(encoding="utf-8"))
_ENGINE = ATLASEngine(ruleset=_RULESET)


def _make_app(max_rpm: int = 5):
    """Cria FastAPI com rate limit baixo para testes rápidos."""
    a = FastAPI()
    a.add_middleware(SmartRateLimiter, max_rpm=max_rpm)

    @a.get("/health")
    def health():
        return {"status": "ok", "ts": int(time.time())}

    @a.post("/atlas/evaluate")
    def evaluate(payload: TerrainMetricsInput):
        terrain = payload.terrain_metrics_dict()
        return _ENGINE.evaluate(
            terrain_metrics=terrain,
            cluster_regional=payload.cluster_regional,
            raise_on_block=False,
        )

    return a


_SIMPLE_PAYLOAD = {
    "declividade_media_pct": 10.0,
    "solo_classe": "latossolo",
    "pct_app_area": 0.0,
    "overlaps_area_uniao": False,
}


class TestRateLimiting:
    """Suite de testes de rate limiting."""

    def test_requests_below_limit_pass(self):
        """Até max_rpm requisições devem retornar 200."""
        client = TestClient(_make_app(max_rpm=5), raise_server_exceptions=False)
        for i in range(5):
            resp = client.post("/atlas/evaluate", json=_SIMPLE_PAYLOAD)
            assert resp.status_code == 200, f"req #{i+1}: esperava 200, recebeu {resp.status_code} — {resp.text[:200]}"

    def test_requests_above_limit_get_429(self):
        """Acima de max_rpm, deve retornar 429."""
        client = TestClient(_make_app(max_rpm=5), raise_server_exceptions=False)
        statuses = []
        for _ in range(8):
            resp = client.post("/atlas/evaluate", json=_SIMPLE_PAYLOAD)
            statuses.append(resp.status_code)

        assert 429 in statuses, f"Esperava pelo menos um 429 em {statuses}"
        # Verifica corpo do 429
        idx = statuses.index(429)
        # Faz mais uma chamada para pegar o JSON completo
        resp_429 = client.post("/atlas/evaluate", json=_SIMPLE_PAYLOAD)
        if resp_429.status_code == 429:
            body = resp_429.json()
            assert "detail" in body
            assert body["detail"]["error"] == "RATE_LIMIT_EXCEEDED"

    def test_health_endpoint_not_rate_limited(self):
        """GET /health NÃO passa pelo rate limiter."""
        client = TestClient(_make_app(max_rpm=5), raise_server_exceptions=False)
        # Esgota o limite com /atlas/evaluate
        for _ in range(10):
            client.post("/atlas/evaluate", json=_SIMPLE_PAYLOAD)

        # /health deve continuar funcionando
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
