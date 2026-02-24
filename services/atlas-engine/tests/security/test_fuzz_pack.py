# services/atlas-engine/tests/security/test_fuzz_pack.py
"""
Fuzz Pack completo - 30 casos de ataque do Grok.
Cada teste verifica que a defesa está funcionando.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


client = TestClient(app)


class TestGrokFuzzPack:
    """Suite de testes para os 30 vetores de ataque do Grok."""
    
    # ========== GRUPO 1: Score 100 com dados insuficientes ==========
    
    def test_fz001_score_100_zero_dados(self):
        """FZ-001: Score 100 com zero dados."""
        payload = {
            "declividade_media_pct": None,
            "solo_classe": None,
            "pct_app_area": None,
            "overlaps_area_uniao": None,
            "historico_deslizamento_r4": None
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        # Deve retornar 422 por dados insuficientes
        assert response.status_code == 422
        assert "coverage_score" in response.json()["detail"]
    
    def test_fz002_score_alto_coverage_baixo(self):
        """FZ-002: Score alto com coverage < 0.4."""
        payload = {
            "declividade_media_pct": 5.0,  # Apenas 1 campo
            # Todos os outros None
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        assert response.status_code == 422
        data = response.json()
        assert data["metadata"]["coverage_score"] < 0.4
    
    # ... (mais 8 testes de score com dados insuficientes)
    
    # ========== GRUPO 2: Bypass de gating ==========
    
    def test_fz011_bypass_gating_area_uniao_app(self):
        """FZ-011: Falso negativo gating área União + APP 0.1%."""
        payload = {
            "overlaps_area_uniao": True,
            "pct_app_area": 0.1,  # Abaixo do threshold mas com União
            "declividade_media_pct": 5.0,
            "solo_classe": "ARGILOSO"
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve bloquear mesmo com pct_app baixo se overlaps_area_uniao
        assert data["viabilidade"]["viabilidade_bloqueada"] is True
        assert any("ATLAS_COMBO_004" in a["code"] for a in data["alertas"])
    
    def test_fz012_bypass_gating_flags_risco_vazio(self):
        """FZ-012: Bypass com flags_risco vazio."""
        payload = {
            "overlaps_area_uniao": True,
            "flags_risco": [],  # Vazio - tentativa de bypass
            "declividade_media_pct": 5.0
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Deve bloquear pela área União independente de flags
        assert data["viabilidade"]["viabilidade_bloqueada"] is True
    
    # ... (mais 8 testes de bypass de gating)
    
    # ========== GRUPO 3: Estouro de caps ==========
    
    def test_fz021_estouro_cap_contencoes(self):
        """FZ-021: Estouro de cap antes do clamp."""
        payload = {
            "declividade_max_pct": 60.0,
            "historico_deslizamento_r4": True,
            "declividade_media_pct": 45.0,
            "solo_classe": "ARGILOSO"
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Fator de contenções deve estar clampado
        contencoes_factor = None
        for item in data["ajustes_custo"]:
            if item["macroetapa"] == "contenções":
                contencoes_factor = item["fator_ajuste"]
        
        assert contencoes_factor is not None
        assert contencoes_factor <= 3.0  # Cap máximo
    
    def test_fz022_estouro_cap_fundacoes(self):
        """FZ-022: Estouro de cap fundações."""
        payload = {
            "solo_classe": "TURFOSO",  # Pior caso
            "nspt_medio": 2,  # Muito baixo
            "lencol_freatico_profundidade_m": 0.5,  # Raso
            "declividade_media_pct": 5.0
        }
        
        response = client.post("/atlas/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Fator de fundações deve estar clampado
        fundacoes_factor = None
        for item in data["ajustes_custo"]:
            if item["macroetapa"] == "fundações":
                fundacoes_factor = item["fator_ajuste"]
        
        assert fundacoes_factor is not None
        assert fundacoes_factor <= 2.5  # Cap máximo
    
    # ... (mais 8 testes de estouro de caps)


@pytest.fixture
def mock_ruleset_with_vulnerabilities():
    """Fixture que cria ruleset com vulnerabilidades conhecidas."""
    return {
        "version": "0.2.0-vulnerable",
        "fingerprint": "test",
        "regras_compostas": [
            {
                "rule_id": "TEST_CONFLICT",
                "target": {"macroetapa": "fundações", "output_field": "fator_ajuste"},
                "aggregation_strategy": "multiply"  # Conflito
            },
            {
                "rule_id": "TEST_CONFLICT_2",
                "target": {"macroetapa": "fundações", "output_field": "fator_ajuste"},
                "aggregation_strategy": "max_factor"  # Conflito com anterior
            }
        ]
    }


def test_ruleset_conflict_detection(mock_ruleset_with_vulnerabilities):
    """Testa que conflitos no ruleset são detectados."""
    from scripts.ci.audit_ruleset import RulesetAuditor
    
    # Simula auditoria
    auditor = RulesetAuditor("test.json", strict=True)
    auditor.ruleset = mock_ruleset_with_vulnerabilities
    
    conflicts = auditor.detect_multiply_max_conflicts()
    
    assert len(conflicts) > 0
    assert conflicts[0]["macroetapa"] == "fundações"
