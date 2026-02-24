import json
import sys
import unittest
from pathlib import Path

from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException

try:
    from delta_engine.integration_contract import aplicar_atlas_ao_orcamento  # opcional
except Exception:
    aplicar_atlas_ao_orcamento = None

# Adiciona o path do atlas-api para importar o decorator de defesa
_ATLAS_API_ROOT = Path(__file__).resolve().parents[2] / "atlas-api"
if str(_ATLAS_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_ATLAS_API_ROOT))

# Fonte única de verdade: carrega do arquivo JSON de produção
# parents[0] = tests/, parents[1] = atlas-engine/
_RULESET_PATH = Path(__file__).parents[1] / "config" / "atlas_ruleset_v0.2.json"
RULESET_V02 = json.loads(_RULESET_PATH.read_text(encoding="utf-8"))

# Carrega o fuzz_pack_40.json com os 40 casos de teste (30 originais + 10 Red Team v2)
_FUZZ_PACK_40_PATH = Path(__file__).resolve().parents[3] / "tools" / "validation" / "fuzz_pack_40.json"
FUZZ_PACK_40 = json.loads(_FUZZ_PACK_40_PATH.read_text(encoding="utf-8")) if _FUZZ_PACK_40_PATH.exists() else []

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


class TestFuzzPack40(unittest.TestCase):
    """Roda automaticamente todos os 40 casos do fuzz_pack_40.json contra o ATLASEngine."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ATLASEngine(RULESET_V02)
        cls.fuzz_cases = FUZZ_PACK_40
        # Importa o sanitizer do decorator de defesa
        try:
            from app.decorators import sanitize_payload
            cls.sanitize_payload = staticmethod(sanitize_payload)
        except ImportError:
            cls.sanitize_payload = None

    def _run_fuzz_case(self, case):
        """Executa um caso de fuzz e retorna (report, decorator_defense_events).

        O payload ORIGINAL é enviado ao engine (para que o engine execute
        sua própria _pre_defense).  O decorator sanitize_payload é executado
        em paralelo apenas para verificar os eventos do decorator.
        """
        import copy as _copy
        payload_original = _copy.deepcopy(case["payload"])
        cluster = case.get("cluster_regional", "BR_DEFAULT")

        # Decorator defense events (rodado no payload original, sem mutar)
        decorator_events = []
        if self.sanitize_payload is not None:
            _, decorator_events = self.sanitize_payload(_copy.deepcopy(payload_original))

        # Engine recebe o payload ORIGINAL — ele faz sua própria sanitização
        report = self.engine.evaluate(
            terrain_metrics=payload_original,
            cluster_regional=cluster,
            raise_on_block=False,
        )
        return report, decorator_events


def _make_fuzz_test(case):
    """Factory que cria um test method para um caso de fuzz."""
    def test_method(self):
        report, defense_events = self._run_fuzz_case(case)
        case_id = case["id"]

        # Assert: bloqueio esperado?
        if "expect_blocked" in case:
            expected_blocked = case["expect_blocked"]
            actual_blocked = report.get("viabilidade_bloqueada", False)
            self.assertEqual(
                actual_blocked, expected_blocked,
                f"{case_id}: expect_blocked={expected_blocked}, got={actual_blocked}"
            )

        # Assert: regra aplicada?
        if "assert_rule_applied" in case:
            self.assertIn(
                case["assert_rule_applied"], report.get("regras_aplicadas", []),
                f"{case_id}: regra {case['assert_rule_applied']} não encontrada em regras_aplicadas"
            )

        # Assert: cap aplicado?
        if "assert_cap_applied" in case:
            macro = case["assert_cap_applied"]
            caps = [e for e in report.get("metadata", {}).get("cap_events", [])
                    if e.get("macroetapa") == macro]
            self.assertTrue(len(caps) > 0, f"{case_id}: cap em '{macro}' não foi aplicado")

        # Assert: score acima de limiar?
        if "assert_score_above" in case:
            self.assertGreater(
                report["score_fisico"], case["assert_score_above"],
                f"{case_id}: score_fisico={report['score_fisico']} <= {case['assert_score_above']}"
            )

        # Assert: score abaixo de limiar?
        if "assert_score_below" in case:
            self.assertLess(
                report["score_fisico"], case["assert_score_below"],
                f"{case_id}: score_fisico={report['score_fisico']} >= {case['assert_score_below']}"
            )

        # Assert: eventos de defesa esperados (Red Team v2)?
        if "expect_defense_events" in case and self.sanitize_payload is not None:
            expected_codes = set(case["expect_defense_events"])
            actual_codes = {e.get("code") for e in defense_events}
            for code in expected_codes:
                self.assertIn(
                    code, actual_codes,
                    f"{case_id}: evento de defesa '{code}' esperado mas não encontrado. "
                    f"Eventos reais: {actual_codes}"
                )

        # Assert: engine defense events (engine-level blindagens)?
        if "assert_engine_defense" in case:
            engine_defense = report.get("metadata", {}).get("engine_defense", {})
            actual_engine_codes = {e.get("code") for e in engine_defense.get("events", [])}
            for code in case["assert_engine_defense"]:
                self.assertIn(
                    code, actual_engine_codes,
                    f"{case_id}: engine defense event '{code}' expected but not found. "
                    f"Actual: {actual_engine_codes}"
                )

    test_method.__doc__ = f"Fuzz {case['id']}: {case.get('description', '')}"
    return test_method


# Gera dinamicamente um test method para cada um dos 40 casos
for _case in FUZZ_PACK_40:
    _test_name = f"test_fuzz_{_case['id'].lower().replace('-', '_')}"
    setattr(TestFuzzPack40, _test_name, _make_fuzz_test(_case))


class TestAtlasDefenseDecorator(unittest.TestCase):
    """Testes unitários do decorator @atlas_defense e do sanitize_payload."""

    @classmethod
    def setUpClass(cls):
        try:
            from app.decorators import (
                sanitize_payload,
                atlas_defense,
                _strip_whitespace_keys,
                _detect_injected_output_fields,
                _validate_solo_classe,
                _validate_risk_flags,
                _detect_null_critical_fields,
                _detect_boundary_proximity,
                _detect_contradictions,
            )
            cls.sanitize_payload = staticmethod(sanitize_payload)
            cls.atlas_defense = staticmethod(atlas_defense)
            cls._strip_whitespace_keys = staticmethod(_strip_whitespace_keys)
            cls.available = True
        except ImportError:
            cls.available = False

    def test_strip_whitespace_keys(self):
        """Chaves com espaços são normalizadas."""
        if not self.available:
            self.skipTest("decorator não disponível")
        result = self._strip_whitespace_keys({" foo ": 1, "bar": {" baz ": 2}})
        self.assertIn("foo", result)
        self.assertIn("baz", result["bar"])
        self.assertNotIn(" foo ", result)

    def test_remove_ajustes_custo_injection(self):
        """ajustes_custo no input é removido e logado como critical."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"ajustes_custo": {"fundações": 1.8}, "declividade_media_pct": 10}
        cleaned, events = self.sanitize_payload(payload)
        self.assertNotIn("ajustes_custo", cleaned)
        critical_events = [e for e in events if e.get("severity") == "critical"]
        self.assertGreater(len(critical_events), 0)

    def test_unknown_solo_classe_warning(self):
        """solo_classe desconhecido gera warning."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"solo_classe": "desconhecido", "declividade_media_pct": 4}
        _, events = self.sanitize_payload(payload)
        codes = {e["code"] for e in events}
        self.assertIn("UNKNOWN_SOLO_CLASSE", codes)

    def test_null_critical_fields_detection(self):
        """Campos críticos explicitamente nulos são detectados."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"solo_classe": None, "pct_app_area": None}
        _, events = self.sanitize_payload(payload)
        null_events = [e for e in events if e["code"] == "EXPLICIT_NULL_CRITICAL"]
        self.assertEqual(len(null_events), 2)

    def test_unknown_risk_flag_warning(self):
        """Flags de risco não reconhecidas geram warning."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"flags_risco": ["info_only", "area_uniao"]}
        _, events = self.sanitize_payload(payload)
        unknown = [e for e in events if e["code"] == "UNKNOWN_RISK_FLAG"]
        self.assertEqual(len(unknown), 1)
        self.assertIn("info_only", unknown[0]["detail"])

    def test_boundary_proximity_detection(self):
        """Valores próximos de limiares são detectados."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"pct_app_area": 9.99, "declividade_media_pct": 19.99}
        _, events = self.sanitize_payload(payload)
        boundary = [e for e in events if "BOUNDARY_PROXIMITY" in e["code"]]
        self.assertGreater(len(boundary), 0)

    def test_union_area_no_app_contradiction(self):
        """overlaps_area_uniao=true + pct_app_area=0 é sinalizado."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"overlaps_area_uniao": True, "pct_app_area": 0, "flags_risco": []}
        _, events = self.sanitize_payload(payload)
        codes = {e["code"] for e in events}
        self.assertIn("UNION_AREA_NO_APP", codes)
        self.assertIn("UNION_AREA_EMPTY_FLAGS", codes)

    def test_whitespace_padded_injection_keys(self):
        """Chaves com whitespace no ajustes_custo são normalizadas antes da remoção."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {"ajustes_custo": {" fundacoes ": 2.5, "terraplanagem": 1.6}}
        cleaned, events = self.sanitize_payload(payload)
        self.assertNotIn("ajustes_custo", cleaned)
        injection_events = [e for e in events if e["code"] == "AJUSTES_CUSTO_INJECTION"]
        self.assertGreater(len(injection_events), 0)

    def test_valid_solo_no_warning(self):
        """Solo classes válidas não geram warning."""
        if not self.available:
            self.skipTest("decorator não disponível")
        for solo in ["latossolo", "gleissolo", "argissolo", "cambissolo"]:
            _, events = self.sanitize_payload({"solo_classe": solo})
            solo_warnings = [e for e in events if e["code"] in ("UNKNOWN_SOLO_CLASSE", "NULL_SOLO_CLASSE")]
            self.assertEqual(len(solo_warnings), 0, f"Warning inesperado para solo_classe={solo}")

    def test_clean_payload_no_events(self):
        """Payload limpo não gera eventos de defesa."""
        if not self.available:
            self.skipTest("decorator não disponível")
        payload = {
            "declividade_media_pct": 10,
            "declividade_max_pct": 15,
            "solo_classe": "latossolo",
            "pct_app_area": 3,
            "overlaps_area_uniao": False,
        }
        _, events = self.sanitize_payload(payload)
        critical = [e for e in events if e.get("severity") == "critical"]
        self.assertEqual(len(critical), 0)


class TestRedTeamBlindagens(unittest.TestCase):
    """Testes explícitos para cada uma das 10 blindagens do Red Team no engine."""

    def setUp(self):
        self.engine = ATLASEngine(RULESET_V02)

    def _get_defense_codes(self, report):
        return {e.get("code") for e in report.get("metadata", {}).get("engine_defense", {}).get("events", [])}

    def _get_defense_events(self, report):
        return report.get("metadata", {}).get("engine_defense", {}).get("events", [])

    # ---- B01: Whitespace key sanitization ----
    def test_b01_whitespace_keys_normalized(self):
        """B01: Chaves com whitespace são normalizadas pelo engine."""
        rep = self.engine.evaluate(
            {" declividade_media_pct ": 25, "solo_classe": "latossolo"},
            raise_on_block=False,
        )
        self.assertIn("ATLAS_SLOPE_SIMPLE_020", rep["regras_aplicadas"])

    # ---- B02: Output field stripping ----
    def test_b02_output_field_stripped(self):
        """B02: ajustes_custo no input é removido com alerta critical."""
        rep = self.engine.evaluate(
            {"ajustes_custo": {"fundações": 1.8}, "declividade_media_pct": 10},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_OUTPUT_FIELD_STRIPPED", codes)
        defense = rep["metadata"]["engine_defense"]
        self.assertTrue(defense["sanitized"])
        self.assertGreater(defense["critical_count"], 0)

    def test_b02_multiple_output_fields(self):
        """B02: Múltiplos campos output-only são removidos."""
        rep = self.engine.evaluate(
            {"ajustes_custo": {"fundações": 1.8}, "score_fisico": 50, "viabilidade_bloqueada": True},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_OUTPUT_FIELD_STRIPPED", codes)
        stripped_fields = [e["field"] for e in self._get_defense_events(rep) if e["code"] == "ENGINE_OUTPUT_FIELD_STRIPPED"]
        self.assertIn("ajustes_custo", stripped_fields)
        self.assertIn("score_fisico", stripped_fields)
        self.assertIn("viabilidade_bloqueada", stripped_fields)

    # ---- B03: NaN/Inf guard ----
    def test_b03_nan_guard(self):
        """B03: NaN é substituído por None."""
        rep = self.engine.evaluate(
            {"declividade_media_pct": float("nan"), "solo_classe": "latossolo"},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_NAN_INF_GUARD", codes)

    def test_b03_inf_guard(self):
        """B03: Inf é substituído por None."""
        rep = self.engine.evaluate(
            {"declividade_media_pct": float("inf"), "solo_classe": "latossolo"},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_NAN_INF_GUARD", codes)

    # ---- B04: Fuzzy macro name normalization ----
    def test_b04_fuzzy_normalize_padded(self):
        """B04: Nomes de macroetapas com espaços são normalizados."""
        self.assertEqual(self.engine._normalize_macro_name(" fundacoes "), "fundações")
        self.assertEqual(self.engine._normalize_macro_name(" CONTENCOES "), "contenções")
        self.assertEqual(self.engine._normalize_macro_name(" terraplanagem "), "terraplanagem")

    def test_b04_fuzzy_normalize_unicode_variants(self):
        """B04: Variantes unicode de macroetapas são normalizadas."""
        self.assertEqual(self.engine._normalize_macro_name("fundaçoes"), "fundações")
        self.assertEqual(self.engine._normalize_macro_name("contençoes"), "contenções")

    def test_b04_unknown_macro_returns_normalized(self):
        """B04: Macro desconhecida retorna versão normalizada (não original)."""
        self.assertEqual(self.engine._normalize_macro_name(" Foo "), "foo")

    # ---- B05: Solo classe validation ----
    def test_b05_unknown_solo(self):
        """B05: solo_classe desconhecido gera alerta engine."""
        rep = self.engine.evaluate(
            {"solo_classe": "desconhecido", "declividade_media_pct": 4, "pct_app_area": 3},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_UNKNOWN_SOLO", codes)

    def test_b05_null_solo(self):
        """B05: solo_classe null gera alerta engine."""
        rep = self.engine.evaluate(
            {"solo_classe": None, "declividade_media_pct": 5},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_NULL_SOLO", codes)

    def test_b05_valid_solo_no_alert(self):
        """B05: Solo classes válidas não geram alerta."""
        for solo in ["latossolo", "gleissolo", "argissolo"]:
            rep = self.engine.evaluate({"solo_classe": solo, "declividade_media_pct": 5}, raise_on_block=False)
            codes = self._get_defense_codes(rep)
            self.assertNotIn("ENGINE_UNKNOWN_SOLO", codes, f"Alerta inesperado para solo={solo}")
            self.assertNotIn("ENGINE_NULL_SOLO", codes, f"Alerta null inesperado para solo={solo}")

    # ---- B06: Risk flag filtering ----
    def test_b06_unknown_flags_filtered(self):
        """B06: Flags de risco desconhecidas são filtradas."""
        rep = self.engine.evaluate(
            {"flags_risco": ["info_only", "area_uniao"], "pct_app_area": 5,
             "overlaps_area_uniao": True, "declividade_media_pct": 5},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_UNKNOWN_FLAGS", codes)

    # ---- B07: Boundary proximity detection ----
    def test_b07_boundary_below(self):
        """B07: Valor próximo abaixo de limiar detectado."""
        rep = self.engine.evaluate(
            {"pct_app_area": 9.99, "declividade_media_pct": 22, "solo_classe": "gleissolo"},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_BOUNDARY_BELOW", codes)

    def test_b07_boundary_above(self):
        """B07: Valor próximo acima de limiar detectado."""
        rep = self.engine.evaluate(
            {"pct_app_area": 10.01, "declividade_media_pct": 19.99},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_BOUNDARY_ABOVE", codes)
        self.assertIn("ENGINE_BOUNDARY_BELOW", codes)

    def test_b07_no_boundary_for_normal_values(self):
        """B07: Valores normais não geram boundary alerts."""
        rep = self.engine.evaluate(
            {"pct_app_area": 3, "declividade_media_pct": 10, "solo_classe": "latossolo"},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertNotIn("ENGINE_BOUNDARY_BELOW", codes)
        self.assertNotIn("ENGINE_BOUNDARY_ABOVE", codes)

    # ---- B08: Contradiction / gating evasion ----
    def test_b08_gating_evasion(self):
        """B08: overlaps_area_uniao=true + pct_app=0 detectado como evasão."""
        rep = self.engine.evaluate(
            {"overlaps_area_uniao": True, "pct_app_area": 0, "flags_risco": []},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_GATING_EVASION", codes)
        self.assertIn("ENGINE_UNION_EMPTY_FLAGS", codes)
        # Não deve bloquear (pct_app_area=0 não satisfaz gating rule op >0)
        self.assertFalse(rep["viabilidade_bloqueada"])

    def test_b08_contradiction_access(self):
        """B08: Contradição acesso_pavimentado + declive extremo detectada."""
        rep = self.engine.evaluate(
            {"acesso_pavimentado": True, "distancia_pavimentacao_m": 0,
             "declividade_max_pct": 48, "solo_classe": "gleissolo"},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_CONTRADICTION", codes)
        self.assertIn("ATLAS_CAP_CONT_A", rep["regras_aplicadas"])

    # ---- B09: Null critical fields ----
    def test_b09_null_critical_fields(self):
        """B09: Campos críticos explicitamente null são detectados."""
        rep = self.engine.evaluate(
            {"solo_classe": None, "pct_app_area": None, "declividade_media_pct": 5},
            raise_on_block=False,
        )
        codes = self._get_defense_codes(rep)
        self.assertIn("ENGINE_NULL_CRITICAL", codes)
        null_events = [e for e in self._get_defense_events(rep) if e["code"] == "ENGINE_NULL_CRITICAL"]
        null_fields = {e["field"] for e in null_events}
        self.assertIn("solo_classe", null_fields)
        self.assertIn("pct_app_area", null_fields)

    # ---- B10: Factor safety cap ----
    def test_b10_factor_cap_preserves_existing_behavior(self):
        """B10: Safety cap não altera comportamento existente (valores normais)."""
        rep = self.engine.evaluate(
            {"declividade_max_pct": 48, "historico_deslizamento_r4": True, "declividade_media_pct": 10},
            raise_on_block=False,
        )
        # 2.1 * 2.0 = 4.2 clampado pelo cap_maximo de 3.0
        self.assertAlmostEqual(rep["ajustes_custo"]["contenções"], 3.0, places=4)

    def test_b10_nan_factor_treated_as_1(self):
        """B10: NaN em factor é tratado como 1.0."""
        result = self.engine._merge_factor(float("nan"), 1.5, "multiply")
        self.assertAlmostEqual(result, 1.5, places=4)

    def test_b10_inf_factor_treated_as_1(self):
        """B10: Inf em factor é tratado como 1.0."""
        result = self.engine._merge_factor(float("inf"), 2.0, "max_factor")
        self.assertAlmostEqual(result, 2.0, places=4)

    # ---- Defense metadata presence ----
    def test_defense_metadata_always_present(self):
        """Engine defense metadata está sempre presente na saída."""
        rep = self.engine.evaluate(
            {"declividade_media_pct": 10, "solo_classe": "latossolo"},
            raise_on_block=False,
        )
        self.assertIn("engine_defense", rep["metadata"])
        defense = rep["metadata"]["engine_defense"]
        self.assertEqual(defense["version"], "2.0")
        self.assertIsInstance(defense["events"], list)
        self.assertIsInstance(defense["events_count"], int)

    def test_clean_input_no_defense_events(self):
        """Input limpo não gera eventos de defesa."""
        rep = self.engine.evaluate(
            {"declividade_media_pct": 10, "declividade_max_pct": 15,
             "solo_classe": "latossolo", "pct_app_area": 3},
            raise_on_block=False,
        )
        defense = rep["metadata"]["engine_defense"]
        self.assertEqual(defense["events_count"], 0)
        self.assertFalse(defense["sanitized"])
        self.assertEqual(defense["critical_count"], 0)


if __name__ == "__main__":
    unittest.main()
