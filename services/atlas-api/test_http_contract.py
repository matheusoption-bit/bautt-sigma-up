from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def _orcamento_base():
    return {
        "premissas_area": {"area_computavel_base_m2": 1600.0, "area_vendavel_base_m2": 1312.0},
        "premissas_preco": {"preco_venda_m2": 8000.0, "custo_terreno_brl": 2500000.0, "custo_projetos_licencas_brl": 350000.0},
        "orcamento_cub": {"macroetapas": {"fundações": 384000.0, "terraplanagem": 128000.0, "infraestrutura": 192000.0, "contenções": 0.0, "drenagem": 0.0}},
        "cronograma_financeiro": {"meses": 1, "distribuicao_custos": [1.0], "distribuicao_receitas": [1.0]},
        "rastreabilidade": {"delta_engine_version": "0.1.0"},
    }

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
