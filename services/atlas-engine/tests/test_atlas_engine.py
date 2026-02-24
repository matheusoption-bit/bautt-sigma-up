import json
import unittest
from pathlib import Path

from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException

try:
    from delta_engine.integration_contract import aplicar_atlas_ao_orcamento  # opcional
except Exception:
    aplicar_atlas_ao_orcamento = None

# Fonte única de verdade: carrega do arquivo JSON de produção
# parents[0] = tests/, parents[1] = atlas-engine/
_RULESET_PATH = Path(__file__).parents[1] / "config" / "atlas_ruleset_v0.2.json"
RULESET_V02 = json.loads(_RULESET_PATH.read_text(encoding="utf-8"))

_RULESET_V02_INLINE_STUB = {
    "version": "0.2.0",
    "metadata": {"name": "ATLAS_RULESET"},
    "caps_fator_custo": {
        "default": {
            "fundacoes": {"cap_warning": 2.0, "cap_maximo": 2.8},
            "terraplanagem": {"cap_warning": 1.6, "cap_maximo": 2.3},
            "contencoes": {"cap_warning": 2.2, "cap_maximo": 3.0},
            "infraestrutura": {"cap_warning": 1.5, "cap_maximo": 2.0},
            "drenagem": {"cap_warning": 1.7, "cap_maximo": 2.4},
        },
        "regional_overrides": [
            {
                "id": "SC_LITORAL",
                "when": {"all": [{"metric": "estado", "op": "==", "value": "SC"}]},
                "overrides": {"fundacoes": {"cap_warning": 1.8}},
            }
        ],
    },
    "gating_rules": [
        {
            "rule_id": "ATLAS_COMBO_004",
            "priority": 1000,
            "when": {
                "all": [
                    {"metric": "overlaps_area_uniao", "op": "==", "value": True},
                    {"metric": "pct_app_area", "op": ">", "value": 0},
                ]
            },
            "effect": {
                "block_viability": True,
                "block_code": "block_area_uniao_app",
                "block_reason": "Área da União com APP sobreposta – alto risco jurídico.",
                "alerts": [
                    {
                        "severity": "critical",
                        "code": "area_uniao_app",
                        "message": "Bloqueio jurídico-ambiental",
                    }
                ],
            },
        }
    ],
    "regras_compostas": [
        {
            "rule_id": "ATLAS_COMBO_001",
            "priority": 200,
            "when": {
                "all": [
                    {"metric": "declividade_media_pct", "op": ">=", "value": 20},
                    {"metric": "solo_classe", "op": "in", "value": ["gleissolo", "solo_hidromorfico"]},
                ]
            },
            "effect": {
                "macro_factors": {"fundacoes": 1.5, "drenagem": 1.3},
                "alerts": [
                    {
                        "severity": "critical",
                        "code": "risco_estabilidade_solo_umido",
                        "message": "Declividade alta em solo hidromórfico.",
                    }
                ],
            },
            "conflict_resolution": {"strategy": "multiply"},
        },
        {
            "rule_id": "ATLAS_COMBO_002",
            "priority": 190,
            "when": {
                "all": [
                    {"metric": "pct_app_area", "op": ">=", "value": 10},
                    {
                        "any": [
                            {"metric": "declividade_media_pct", "op": ">=", "value": 20},
                            {"metric": "declividade_max_pct", "op": ">=", "value": 30},
                        ]
                    },
                ]
            },
            "effect": {
                "fator_area_util_mult": 0.8,
                "alerts": [
                    {
                        "severity": "critical",
                        "code": "app_declive",
                        "message": "APP relevante em área declivosa.",
                    }
                ],
            },
        },
        {
            "rule_id": "ATLAS_COMBO_003",
            "priority": 180,
            "when": {
                "all": [
                    {"metric": "solo_classe", "op": "in", "value": ["gleissolo", "solo_hidromorfico"]},
                    {"metric": "infra_saneamento.esgoto_proximo", "op": "==", "value": False},
                    {"metric": "infra_saneamento.drenagem_superficial", "op": "in", "value": ["inexistente", "precaria"]},
                ]
            },
            "effect": {
                "macro_factors": {"infraestrutura": 1.4},
                "itens_custo_adicional": [
                    {
                        "codigo_item": "infra_ete_privada",
                        "descricao": "ETE privada/condominial",
                        "macroetapa": "infraestrutura",
                        "unidade_ref": "vb",
                        "custo_estimado_brl_range": [100000, 400000],
                    }
                ],
                "alerts": [
                    {
                        "severity": "critical",
                        "code": "solo_umido_sem_saneamento",
                        "message": "Solo encharcado sem saneamento.",
                    }
                ],
            },
        },
        {
            "rule_id": "ATLAS_COMBO_005",
            "priority": 170,
            "when": {
                "all": [
                    {"metric": "declividade_max_pct", "op": ">=", "value": 25},
                    {"metric": "acesso_pavimentado", "op": "==", "value": False},
                    {"metric": "distancia_pavimentacao_m", "op": ">=", "value": 150},
                ]
            },
            "effect": {
                "macro_factors": {"terraplanagem": 1.35},
                "itens_custo_adicional": [
                    {
                        "codigo_item": "acesso_pavimentacao",
                        "descricao": "Pavimentação de acesso",
                        "macroetapa": "infraestrutura",
                        "unidade_ref": "m",
                        "quantidade_formula_hint": "distancia_pavimentacao_m",
                        "custo_estimado_brl_range": [500, 3500],
                    }
                ],
                "alerts": [
                    {
                        "severity": "warning",
                        "code": "acesso_sem_pavimento_declive",
                        "message": "Declive alto + acesso sem pavimentação.",
                    }
                ],
            },
        },
    ],
    "regras_simples": [
        {
            "rule_id": "ATLAS_SLOPE_SIMPLE_020",
            "priority": 100,
            "when": {"metric": "declividade_media_pct", "op": ">=", "value": 20},
            "effect": {
                "macro_factors": {"terraplanagem": 1.25},
                "alerts": [{"severity": "warning", "code": "slope_forte", "message": "Declividade média alta."}],
            },
        },
        {
            "rule_id": "ATLAS_SOIL_GLEI_SIMPLE",
            "priority": 110,
            "when": {"metric": "solo_classe", "op": "in", "value": ["gleissolo", "solo_hidromorfico"]},
            "effect": {
                "macro_factors": {"fundacoes": 2.0},
                "alerts": [{"severity": "warning", "code": "solo_hidromorfico", "message": "Solo hidromórfico."}],
            },
            "conflict_resolution": {"strategy": "multiply"},
        },
        {
            "rule_id": "ATLAS_CAP_CONT_A",
            "priority": 120,
            "when": {"metric": "declividade_max_pct", "op": ">=", "value": 45},
            "effect": {"macro_factors": {"contencoes": 2.1}},
            "conflict_resolution": {"strategy": "multiply"},
        },
        {
            "rule_id": "ATLAS_CAP_CONT_B",
            "priority": 115,
            "when": {"metric": "historico_deslizamento_r4", "op": "==", "value": True},
            "effect": {"macro_factors": {"contencoes": 2.0}},
            "conflict_resolution": {"strategy": "multiply"},
        },
    ],
    "priorizacao_regras": {
        "order": ["gating_rules", "regras_compostas", "regras_simples"],
        "conflict_default_strategy": "max_factor",
    },
}


class TestATLASEngineV02(unittest.TestCase):
    def setUp(self):
        self.engine = ATLASEngine(RULESET_V02)

    def test_combo_001_gleissolo_declive_clampado(self):
        metrics = {
            "estado": "SC",
            "declividade_media_pct": 22,
            "declividade_max_pct": 28,
            "solo_classe": "gleissolo",
            "pct_app_area": 0,
        }
        rep = self.engine.evaluate(metrics, cluster_regional="SC_LITORAL")
        self.assertIn("ATLAS_COMBO_001", rep["regras_aplicadas"])
        # solo simples 2.0 * combo001 1.5 = 3.0 -> clamp fundações 2.8
        self.assertAlmostEqual(rep["ajustes_custo"]["fundações"], 2.8, places=4)
        # breakdown registra teórico vs efetivo
        fund = next(x for x in rep["breakdown_ajustes"] if x["macroetapa"] == "fundações")
        self.assertAlmostEqual(fund["fator_teorico"], 3.0, places=4)
        self.assertAlmostEqual(fund["fator_efetivo"], 2.8, places=4)

    def test_combo_002_app_declive_reduz_area_util(self):
        metrics = {"declividade_media_pct": 25, "declividade_max_pct": 35, "pct_app_area": 12}
        rep = self.engine.evaluate(metrics)
        self.assertIn("ATLAS_COMBO_002", rep["regras_aplicadas"])
        self.assertAlmostEqual(rep["fator_area_util"], 0.8, places=4)

    def test_combo_003_solo_hidromorfico_sem_saneamento_insere_item(self):
        metrics = {
            "declividade_media_pct": 10,
            "declividade_max_pct": 15,
            "tipo_solo": "Gleissolo Háplico Tb",
            "distancia_rede_esgoto_m": 800,
            "infra_saneamento": {"drenagem_superficial": "precaria"},
        }
        rep = self.engine.evaluate(metrics)
        self.assertIn("ATLAS_COMBO_003", rep["regras_aplicadas"])
        codigos = [i.get("codigo_item") for i in rep["itens_custo_adicional"]]
        self.assertIn("infra_ete_privada", codigos)

    def test_combo_004_area_uniao_app_gating(self):
        metrics = {"pct_app_area": 5, "flags_risco": ["area_uniao"]}
        with self.assertRaises(ATLASBlockedException) as ctx:
            self.engine.evaluate(metrics)
        self.assertTrue(ctx.exception.bloqueios)
        self.assertEqual(ctx.exception.bloqueios[0]["codigo"], "block_area_uniao_app")

    def test_combo_005_declive_acesso_sem_pavimentacao_item_com_hint(self):
        metrics = {
            "declividade_media_pct": 18,
            "declividade_max_pct": 30,
            "acesso_pavimentado": False,
            "distancia_pavimentacao_m": 260,
        }
        rep = self.engine.evaluate(metrics)
        self.assertIn("ATLAS_COMBO_005", rep["regras_aplicadas"])
        item = next(i for i in rep["itens_custo_adicional"] if i["codigo_item"] == "acesso_pavimentacao")
        self.assertEqual(item["quantidade_formula_hint"], "distancia_pavimentacao_m")
        self.assertEqual(item["unidade_ref"], "m")

    def test_cap_salva_analise_contencoes_4_2_para_3_0(self):
        metrics = {
            "declividade_media_pct": 10,
            "declividade_max_pct": 48,
            "historico_deslizamento_r4": True,
        }
        rep = self.engine.evaluate(metrics)
        # 2.1 * 2.0 = 4.2 clampado em 3.0
        self.assertAlmostEqual(rep["ajustes_custo"]["contenções"], 3.0, places=4)
        cont = next(x for x in rep["breakdown_ajustes"] if x["macroetapa"] == "contenções")
        self.assertAlmostEqual(cont["fator_teorico"], 4.2, places=4)
        self.assertAlmostEqual(cont["fator_efetivo"], 3.0, places=4)
        self.assertTrue(any(a.get("code") == "cap_atingido" and a.get("macroetapa") == "contenções" for a in rep["alertas"]))

    def test_saida_compatibilidade_v0_1(self):
        rep = self.engine.evaluate({"declividade_media_pct": 0, "declividade_max_pct": 0})
        for key in [
            "score_fisico", "ajustes_custo", "itens_custo_adicional", "alertas",
            "regras_aplicadas", "viabilidade_bloqueada", "bloqueios", "fator_area_util", "metadata"
        ]:
            self.assertIn(key, rep)

    @unittest.skipIf(aplicar_atlas_ao_orcamento is None, "delta_integration_contract não disponível neste ambiente")
    def test_compatibilidade_com_delta_contract_smoke(self):
        # smoke test opcional: só executa se o contrato estiver importável
        orc = {
            "premissas_area": {"area_computavel_base_m2": 1000, "area_vendavel_base_m2": 800, "distancia_pavimentacao_m": 260},
            "premissas_preco": {"preco_venda_m2": 5000, "custo_terreno_brl": 1000000, "custo_projetos_licencas_brl": 100000, "contingencia_pct_custo": 0.03},
            "orcamento_cub": {"macroetapas": {"fundações": 100000, "terraplanagem": 50000, "infraestrutura": 70000, "contenções": 0, "drenagem": 0}},
            "cronograma_financeiro": {"meses": 2, "distribuicao_custos": [0.5, 0.5], "distribuicao_receitas": [0.0, 1.0]},
            "rastreabilidade": {"delta_engine_version": "0.1.0"},
        }
        rep = self.engine.evaluate({
            "declividade_media_pct": 22, "declividade_max_pct": 30, "tipo_solo": "Gleissolo", "pct_app_area": 12,
            "distancia_rede_esgoto_m": 800, "infra_saneamento": {"drenagem_superficial": "precaria"},
            "acesso_pavimentado": False, "distancia_pavimentacao_m": 260,
        })
        out = aplicar_atlas_ao_orcamento(orc, rep)
        self.assertGreater(out.custo_total_revisado_brl, out.custo_total_base_brl)


class TestATLASEngineCoverage(unittest.TestCase):
    """Testes extras para cobrir edge-cases e atingir 85%+ de cobertura."""

    def test_ruleset_deve_ser_dict(self):
        """TypeError se ruleset não for dict."""
        with self.assertRaises(TypeError):
            ATLASEngine(ruleset="not a dict")
        with self.assertRaises(TypeError):
            ATLASEngine(ruleset=[1, 2])

    def test_property_ruleset_retorna_copia(self):
        """Acessa .ruleset e verifica que é cópia independente."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        r = engine.ruleset
        self.assertEqual(r["version"], "0.2.0")
        r["version"] = "HACK"
        self.assertEqual(engine.ruleset["version"], "0.2.0")  # não foi mutado

    def test_alias_normalization_declividade_avg(self):
        """Campo declividade_avg é normalizado para declividade_media_pct."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({"declividade_avg": 25, "solo_classe": "latossolo"})
        self.assertIn("ATLAS_SLOPE_SIMPLE_020", rep["regras_aplicadas"])

    def test_alias_normalization_area_app_pct(self):
        """Campo area_app_pct é normalizado para pct_app_area."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({
            "area_app_pct": 15,
            "declividade_media_pct": 25,
            "solo_classe": "latossolo",
            "overlaps_area_uniao": False,
        })
        self.assertIn("ATLAS_COMBO_002", rep["regras_aplicadas"])

    def test_alias_normalization_declividade_max(self):
        """Campo declividade_max normalizado para declividade_max_pct."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({"declividade_max": 50, "declividade_media_pct": 10})
        self.assertIn("ATLAS_CAP_CONT_A", rep["regras_aplicadas"])

    def test_normalize_tipo_solo_argissolo(self):
        """tipo_solo 'Argissolo' normalizado para solo_classe 'argissolo'."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({"tipo_solo": "Argissolo Vermelho-Amarelo", "declividade_media_pct": 5})
        # Argissolo não dispara nenhuma regra especial, mas não deve crashar
        self.assertIsInstance(rep["score_fisico"], int)

    def test_normalize_tipo_solo_espodossolo(self):
        """tipo_solo 'Espodossolo' reconhecido."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({"tipo_solo": "Espodossolo Humilúvico", "declividade_media_pct": 5})
        self.assertIsInstance(rep["score_fisico"], int)

    def test_merge_strategy_first_match(self):
        """Estratégia first_match usa o primeiro fator != 1.0."""
        ruleset = {
            "version": "test",
            "regras_simples": [
                {"rule_id": "A", "priority": 100,
                 "when": {"metric": "x", "op": ">=", "value": 0},
                 "effect": {"macro_factors": {"fundacoes": 1.3}},
                 "conflict_resolution": {"strategy": "first_match"}},
                {"rule_id": "B", "priority": 90,
                 "when": {"metric": "x", "op": ">=", "value": 0},
                 "effect": {"macro_factors": {"fundacoes": 1.6}},
                 "conflict_resolution": {"strategy": "first_match"}},
            ],
        }
        engine = ATLASEngine(ruleset=ruleset)
        rep = engine.evaluate({"x": 1})
        self.assertAlmostEqual(rep["ajustes_custo"]["fundações"], 1.3, places=4)

    def test_merge_strategy_sum_clamped(self):
        """Estratégia sum_clamped soma deltas acima de 1.0."""
        ruleset = {
            "version": "test",
            "regras_simples": [
                {"rule_id": "A", "priority": 100,
                 "when": {"metric": "x", "op": ">=", "value": 0},
                 "effect": {"macro_factors": {"fundacoes": 1.3}},
                 "conflict_resolution": {"strategy": "sum_clamped"}},
                {"rule_id": "B", "priority": 90,
                 "when": {"metric": "x", "op": ">=", "value": 0},
                 "effect": {"macro_factors": {"fundacoes": 1.5}},
                 "conflict_resolution": {"strategy": "sum_clamped"}},
            ],
        }
        engine = ATLASEngine(ruleset=ruleset)
        rep = engine.evaluate({"x": 1})
        # sum_clamped: 1.0 + 0.3 + 0.5 = 1.8
        self.assertAlmostEqual(rep["ajustes_custo"]["fundações"], 1.8, places=4)

    def test_distancia_pavimentacao_infere_acesso_pavimentado(self):
        """distancia_pavimentacao_m > 0 gera acesso_pavimentado = False."""
        engine = ATLASEngine(ruleset=RULESET_V02)
        rep = engine.evaluate({
            "declividade_max_pct": 30,
            "distancia_pavimentacao_m": 200,
            "declividade_media_pct": 10,
        })
        self.assertIn("ATLAS_COMBO_005", rep["regras_aplicadas"])


if __name__ == "__main__":
    unittest.main()
