"""
Testes mínimos do contrato DELTA.

Cobertura:
  - caminho feliz (ajustes aplicados corretamente)
  - bloqueio ATLAS lança ATLASBlockedException
  - hash de rastreabilidade é determinístico
  - fator aplicado sobre macroetapa específica
  - cronograma inválido lança ValueError
"""
import pytest

from delta_engine.integration_contract import (
    ATLASBlockedException,
    OrcamentoAjustado,
    aplicar_atlas_ao_orcamento,
)


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

def _orcamento_base():
    """Orçamento CUB mínimo e válido para os testes."""
    return {
        "premissas_area": {
            "area_computavel_base_m2": 1000.0,
            "area_vendavel_base_m2": 800.0,
            "distancia_pavimentacao_m": 200.0,
        },
        "premissas_preco": {
            "preco_venda_m2": 5000.0,
            "custo_terreno_brl": 500_000.0,
            "custo_projetos_licencas_brl": 80_000.0,
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


def _atlas_report_simples(fatores=None, fator_area_util=1.0):
    """Atlas report sem bloqueio, com fatores configuráveis."""
    return {
        "viabilidade_bloqueada": False,
        "bloqueios": [],
        "ajustes_custo": fatores or {},
        "fator_area_util": fator_area_util,
        "itens_custo_adicional": [],
        "regras_aplicadas": ["ATLAS_SLOPE_SIMPLE_020"],
        "metadata": {
            "ruleset_id": "ATLAS_RULESET",
            "versao_ruleset": "0.2.0",
        },
    }


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

def test_caminho_feliz_retorna_orcamento_ajustado():
    """Caminho feliz: com fator de ajuste, custo revisado deve ser > base."""
    orc = _orcamento_base()
    report = _atlas_report_simples(fatores={"fundações": 1.4, "terraplanagem": 1.2})

    resultado = aplicar_atlas_ao_orcamento(orc, report)

    assert isinstance(resultado, OrcamentoAjustado)
    assert resultado.custo_total_revisado_brl > resultado.custo_total_base_brl
    # fundações: 100k * 1.4 = 140k
    assert resultado.macroetapas_ajustadas_brl["fundações"] == pytest.approx(140_000.0)
    # terraplanagem: 50k * 1.2 = 60k
    assert resultado.macroetapas_ajustadas_brl["terraplanagem"] == pytest.approx(60_000.0)


def test_bloqueio_atlas_lanca_excecao():
    """Atlas report com viabilidade_bloqueada=True deve lançar ATLASBlockedException."""
    orc = _orcamento_base()
    report_bloqueado = {
        "viabilidade_bloqueada": True,
        "bloqueios": [
            {
                "codigo": "block_area_uniao_app",
                "motivo": "Área da União com APP sobreposta – alto risco jurídico.",
                "regra_id": "ATLAS_COMBO_004",
            }
        ],
        "ajustes_custo": {},
        "fator_area_util": 1.0,
        "itens_custo_adicional": [],
    }

    with pytest.raises(ATLASBlockedException) as exc_info:
        aplicar_atlas_ao_orcamento(orc, report_bloqueado)

    assert exc_info.value.bloqueios
    assert exc_info.value.bloqueios[0]["codigo"] == "block_area_uniao_app"


def test_hash_rastreabilidade_deterministico():
    """Mesmos inputs devem gerar exatamente o mesmo hash de rastreabilidade."""
    orc = _orcamento_base()
    report = _atlas_report_simples(fatores={"fundações": 1.5})

    resultado_1 = aplicar_atlas_ao_orcamento(orc, report)
    resultado_2 = aplicar_atlas_ao_orcamento(orc, report)

    assert resultado_1.rastreabilidade["hash_rastreabilidade"] == \
           resultado_2.rastreabilidade["hash_rastreabilidade"]


def test_fator_macroetapa_aplicado_corretamente():
    """Fator de fundação 1.5 sobre base de R$100k deve resultar em R$150k."""
    orc = _orcamento_base()
    report = _atlas_report_simples(fatores={"fundações": 1.5})

    resultado = aplicar_atlas_ao_orcamento(orc, report)

    assert resultado.macroetapas_ajustadas_brl["fundações"] == pytest.approx(150_000.0)
    assert resultado.fatores_aplicados.get("fundações") == pytest.approx(1.5)


def test_cronograma_invalido_lanca_value_error():
    """Distribuição de custos que não soma 1.0 deve lançar ValueError."""
    orc = _orcamento_base()
    # distribuicao_custos soma 0.9 (deveria ser 1.0)
    orc["cronograma_financeiro"]["distribuicao_custos"] = [0.4, 0.5]
    report = _atlas_report_simples()

    with pytest.raises(ValueError, match="somar 1.0"):
        aplicar_atlas_ao_orcamento(orc, report)
