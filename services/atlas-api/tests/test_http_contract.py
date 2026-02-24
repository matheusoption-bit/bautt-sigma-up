from fastapi.testclient import TestClient
from atlas_api.main import app

client = TestClient(app)

def _orcamento_base():
    return {
        "premissas_area": {"area_computavel_base_m2": 1600.0, "area_vendavel_base_m2": 1312.0},
        "premissas_preco": {"preco_venda_m2": 8000.0, "custo_terreno_brl": 2500000.0, "custo_projetos_licencas_brl": 350000.0},
        "orcamento_cub": {"macroetapas": {"fundações": 384000.0, "terraplanagem": 128000.0, "infraestrutura": 192000.0, "contenções": 0.0, "drenagem": 0.0}},
        "cronograma_financeiro": {"meses": 1, "distribuicao_custos": [1.0], "distribuicao_receitas": [1.0]},
        "rastreabilidade": {"delta_engine_version": "0.1.0"},
    }

# ---------------------------------------------------------------------------
# Health & metadata endpoints
# ---------------------------------------------------------------------------

def test_health_returns_ok():
    """GET /health deve retornar status ok com timestamp."""
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "ts" in body

def test_ruleset_version_returns_metadata():
    """GET /atlas/ruleset/version deve retornar versão e nome do ruleset."""
    r = client.get("/atlas/ruleset/version")
    assert r.status_code == 200
    body = r.json()
    assert "ruleset_version" in body
    assert "ruleset_name" in body
    assert "ruleset_fingerprint" in body

# ---------------------------------------------------------------------------
# ATLAS evaluate
# ---------------------------------------------------------------------------

def test_atlas_evaluate_gating_returns_200_blocked():
    payload = {
        "cluster_regional": "BR_DEFAULT",
        "pct_app_area": 5,
        "overlaps_area_uniao": True,
        "declividade_media_pct": 8,
        "solo_classe": "latossolo"
    }
    r = client.post("/atlas/evaluate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["viabilidade_bloqueada"] is True

def test_atlas_evaluate_happy_path():
    """Terreno sem risco → viabilidade livre, metadata com coverage_score."""
    payload = {
        "cluster_regional": "BR_DEFAULT",
        "declividade_media_pct": 3,
        "solo_classe": "latossolo",
        "pct_app_area": 0,
        "overlaps_area_uniao": False,
    }
    r = client.post("/atlas/evaluate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["viabilidade_bloqueada"] is False
    assert "metadata" in body
    assert "coverage_score" in body["metadata"]
    assert "tempo_evaluate_ms" in body["metadata"]

# ---------------------------------------------------------------------------
# DELTA apply-atlas
# ---------------------------------------------------------------------------

def test_delta_apply_atlas_gating_returns_409():
    req = {
        "cluster_regional": "BR_DEFAULT",
        "terrain_metrics": {
            "cluster_regional": "BR_DEFAULT",
            "pct_app_area": 5,
            "overlaps_area_uniao": True
        },
        "orcamento_base": _orcamento_base()
    }
    r = client.post("/delta/apply-atlas", json=req)
    assert r.status_code == 409

def test_delta_apply_atlas_happy_path():
    """Terreno sem bloqueio → DELTA processa orçamento com sucesso."""
    req = {
        "cluster_regional": "BR_DEFAULT",
        "terrain_metrics": {
            "cluster_regional": "BR_DEFAULT",
            "declividade_media_pct": 3,
            "solo_classe": "latossolo",
            "pct_app_area": 0,
            "overlaps_area_uniao": False,
        },
        "orcamento_base": _orcamento_base()
    }
    r = client.post("/delta/apply-atlas", json=req)
    assert r.status_code == 200
    body = r.json()
    assert "atlas_report" in body
    assert "orcamento_ajustado" in body

def test_atlas_evaluate_validation_error_returns_422():
    """Payload inválido (campo numérico fora de range) → 422 Unprocessable Entity."""
    payload = {
        "cluster_regional": "BR_DEFAULT",
        "declividade_media_pct": -999,
    }
    r = client.post("/atlas/evaluate", json=payload)
    assert r.status_code == 422
