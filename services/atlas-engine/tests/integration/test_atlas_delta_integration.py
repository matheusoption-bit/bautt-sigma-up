"""
Testes de integração ATLAS Engine + DELTA Engine.

Valida o fluxo end-to-end:
  ATLAS evaluate → DELTA aplicar_atlas_ao_orcamento

Cenários cobertos:
  1. Caminho feliz: terreno com agravantes → ajustes aplicados → custo revisado > base
  2. Gating block: terreno com bloqueio → DELTA lança ATLASBlockedException
  3. Terreno plano sem risco → custos ficam iguais à base
  4. Combo completo (declive + gleissolo + APP + sem pavimentação) → múltiplos ajustes
  5. Fator_area_util reduzido reflete no orçamento
  6. Itens de custo adicional precificados corretamente
  7. Hash de rastreabilidade determinístico no fluxo integrado
"""
import json
import pytest
from pathlib import Path

from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException
from delta_engine.integration_contract import (
    aplicar_atlas_ao_orcamento,
    OrcamentoAjustado,
    ATLASBlockedException as DeltaATLASBlockedException,
)

# ---- Carrega ruleset de produção ----
_RULESET_PATH = Path(__file__).resolve().parents[2] / "config" / "atlas_ruleset_v0.2.json"
RULESET = json.loads(_RULESET_PATH.read_text(encoding="utf-8"))


# ---- Fixtures ----

def _orcamento_base():
    """Orçamento CUB mínimo válido."""
    return {
        "premissas_area": {
            "area_computavel_base_m2": 1000.0,
            "area_vendavel_base_m2": 800.0,
            "distancia_pavimentacao_m": 260.0,
        },
        "premissas_preco": {
            "preco_venda_m2": 5000.0,
            "custo_terreno_brl": 1_000_000.0,
            "custo_projetos_licencas_brl": 100_000.0,
            "contingencia_pct_custo": 0.03,
        },
        "orcamento_cub": {
            "macroetapas": {
                "fundações": 100_000.0,
                "terraplanagem": 50_000.0,
                "infraestrutura": 70_000.0,
                "contenções": 0.0,
                "drenagem": 0.0,
            }
        },
        "cronograma_financeiro": {
            "meses": 2,
            "distribuicao_custos": [0.5, 0.5],
            "distribuicao_receitas": [0.0, 1.0],
        },
        "rastreabilidade": {"delta_engine_version": "0.1.0"},
    }


def _engine():
    return ATLASEngine(ruleset=RULESET)


# ---- Testes de integração ----


class TestAtlasDeltaIntegration:
    """End-to-end: ATLAS evaluate → DELTA aplicar_atlas_ao_orcamento."""

    def test_caminho_feliz_declive_alto_gleissolo(self):
        """Terreno com declive alto + gleissolo → custo revisado > base."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 22,
            "declividade_max_pct": 28,
            "solo_classe": "gleissolo",
            "pct_app_area": 0,
            "overlaps_area_uniao": False,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert not report["viabilidade_bloqueada"]
        assert "ATLAS_COMBO_001" in report["regras_aplicadas"]
        assert report["ajustes_custo"]["fundações"] > 1.0

        orc = _orcamento_base()
        resultado = aplicar_atlas_ao_orcamento(orc, report)

        assert isinstance(resultado, OrcamentoAjustado)
        assert resultado.custo_total_revisado_brl > resultado.custo_total_base_brl
        assert resultado.macroetapas_ajustadas_brl["fundações"] > 100_000.0

    def test_gating_block_area_uniao_propagado_ao_delta(self):
        """Terreno com overlaps_area_uniao + APP > 0 → ATLAS bloqueia → DELTA lança exceção."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 5,
            "pct_app_area": 5,
            "overlaps_area_uniao": True,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert report["viabilidade_bloqueada"]
        assert len(report["bloqueios"]) > 0

        orc = _orcamento_base()
        with pytest.raises(DeltaATLASBlockedException):
            aplicar_atlas_ao_orcamento(orc, report)

    def test_terreno_plano_sem_risco_custos_iguais(self):
        """Terreno plano, latossolo, sem APP → nenhuma regra dispara, custos iguais."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 2,
            "declividade_max_pct": 5,
            "solo_classe": "latossolo",
            "pct_app_area": 0,
            "overlaps_area_uniao": False,
            "acesso_pavimentado": True,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert not report["viabilidade_bloqueada"]
        assert report["score_fisico"] >= 90

        orc = _orcamento_base()
        resultado = aplicar_atlas_ao_orcamento(orc, report)

        # Sem ajustes significativos, custo revisado ≈ custo base (apenas contingência pode diferir)
        assert resultado.macroetapas_ajustadas_brl["fundações"] == pytest.approx(100_000.0)
        assert resultado.macroetapas_ajustadas_brl["terraplanagem"] == pytest.approx(50_000.0)

    def test_combo_completo_multiplos_ajustes(self):
        """Cenário severo: declive + gleissolo + APP + sem pavimento → múltiplos fatores."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 25,
            "declividade_max_pct": 35,
            "solo_classe": "gleissolo",
            "pct_app_area": 15,
            "overlaps_area_uniao": False,
            "acesso_pavimentado": False,
            "distancia_pavimentacao_m": 300,
            "infra_saneamento": {
                "esgoto_proximo": False,
                "drenagem_superficial": "precaria",
            },
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert not report["viabilidade_bloqueada"]
        assert len(report["regras_aplicadas"]) >= 3
        assert report["fator_area_util"] < 1.0

        orc = _orcamento_base()
        resultado = aplicar_atlas_ao_orcamento(orc, report)

        assert resultado.custo_total_revisado_brl > resultado.custo_total_base_brl
        # Fundações devem ter fator > 1
        assert resultado.macroetapas_ajustadas_brl["fundações"] > 100_000.0

    def test_fator_area_util_reduz_vgv(self):
        """Fator de área útil < 1 reduz a receita no orçamento ajustado."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 25,
            "declividade_max_pct": 35,
            "pct_app_area": 12,
            "solo_classe": "latossolo",
            "overlaps_area_uniao": False,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert report["fator_area_util"] < 1.0

        orc = _orcamento_base()
        resultado = aplicar_atlas_ao_orcamento(orc, report)

        vgv_base = 800.0 * 5000.0  # area_vendavel * preco_m2
        assert resultado.receita["vgv_ajustado_brl"] < vgv_base

    def test_itens_custo_adicional_precificados(self):
        """Itens de custo adicional do ATLAS são precificados pelo DELTA."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 10,
            "declividade_max_pct": 15,
            "tipo_solo": "Gleissolo Háplico Tb",
            "distancia_rede_esgoto_m": 800,
            "infra_saneamento": {"drenagem_superficial": "precaria"},
            "overlaps_area_uniao": False,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert "ATLAS_COMBO_003" in report["regras_aplicadas"]
        assert len(report["itens_custo_adicional"]) > 0

        orc = _orcamento_base()
        resultado = aplicar_atlas_ao_orcamento(orc, report)

        assert resultado.custo_total_itens_adicionais_brl > 0
        assert len(resultado.itens_custo_adicional) > 0

    def test_hash_rastreabilidade_deterministico_integrado(self):
        """Mesmo terreno + mesmo orçamento → mesmo hash de rastreabilidade."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 22,
            "solo_classe": "gleissolo",
            "pct_app_area": 0,
            "overlaps_area_uniao": False,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        r1 = aplicar_atlas_ao_orcamento(_orcamento_base(), report)
        r2 = aplicar_atlas_ao_orcamento(_orcamento_base(), report)

        assert r1.rastreabilidade["hash_rastreabilidade"] == \
               r2.rastreabilidade["hash_rastreabilidade"]

    def test_engine_defense_metadata_presente(self):
        """O report do engine inclui metadata de engine_defense."""
        engine = _engine()
        terrain = {
            "declividade_media_pct": 5,
            "solo_classe": "latossolo",
            "pct_app_area": 0,
        }
        report = engine.evaluate(terrain, raise_on_block=False)

        assert "engine_defense" in report.get("metadata", {})
        defense = report["metadata"]["engine_defense"]
        assert "events" in defense
        assert "events_count" in defense

    def test_raise_on_block_true_lanca_excecao(self):
        """Com raise_on_block=True, gating lança ATLASBlockedException do engine."""
        engine = _engine()
        terrain = {
            "pct_app_area": 5,
            "overlaps_area_uniao": True,
        }
        with pytest.raises(ATLASBlockedException) as exc_info:
            engine.evaluate(terrain, raise_on_block=True)

        assert len(exc_info.value.bloqueios) > 0
        assert exc_info.value.bloqueios[0]["codigo"] == "block_area_uniao_app"
