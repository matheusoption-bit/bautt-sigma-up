from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import copy
import json
import re

class ATLASBlockedException(Exception):
    """Levantada quando o ATLAS bloqueia a viabilidade do terreno (gating rules)."""
    def __init__(self, bloqueios: List[Dict[str, Any]], mensagem: str = "Viabilidade bloqueada pelo ATLAS", atlas_report: Optional[Dict[str, Any]] = None):
        self.bloqueios = bloqueios or []
        self.mensagem = mensagem
        self.atlas_report = atlas_report or {}
        super().__init__(f"{mensagem}: {self.bloqueios}")


@dataclass(frozen=True)
class _RuleHit:
    rule_id: str
    group: str
    priority: int


class ATLASEngine:
    """
    Executor stateless de ruleset v0.2 (simples + compostas + gating + caps + override regional).
    """

    def __init__(self, ruleset: Dict[str, Any]):
        if not isinstance(ruleset, dict):
            raise TypeError("ruleset deve ser dict")
        self._ruleset: Dict[str, Any] = copy.deepcopy(ruleset)
        self._ruleset_fingerprint = self._fingerprint_ruleset(self._ruleset)

    @property
    def ruleset(self) -> Dict[str, Any]:
        return copy.deepcopy(self._ruleset)

    def evaluate(
        self,
        terrain_metrics: Dict[str, Any],
        cluster_regional: Optional[str] = None,
        raise_on_block: bool = True,
    ) -> Dict[str, Any]:
        metrics = self._normalize_metrics(terrain_metrics or {})
        active_caps, regional_meta = self._resolve_caps(metrics, cluster_regional=cluster_regional)

        order = (
            self._ruleset.get("priorizacao_regras", {}).get("order")
            or ["gating_rules", "regras_compostas", "regras_simples"]
        )
        default_strategy = (
            self._ruleset.get("priorizacao_regras", {}).get("conflict_default_strategy")
            or "max_factor"
        )

        theoretical_factors: Dict[str, float] = {}
        effective_factors_pre_cap: Dict[str, float] = {}
        factor_sources: Dict[str, List[Dict[str, Any]]] = {}
        itens_custo_adicional: List[Dict[str, Any]] = []
        alertas: List[Dict[str, Any]] = []
        regras_aplicadas: List[str] = []
        bloqueios: List[Dict[str, Any]] = []
        score_penalty_total = 0.0
        fator_area_util = 1.0
        cap_events: List[Dict[str, Any]] = []
        hits: List[_RuleHit] = []

        for group_name in order:
            rules = self._ruleset.get(group_name, []) or []
            rules_sorted = sorted(rules, key=lambda r: int(r.get("priority", 0)), reverse=True)
            for rule in rules_sorted:
                when = rule.get("when")
                if not when:
                    continue
                if not self._eval_condition_tree(when, metrics):
                    continue

                rule_id = str(rule.get("rule_id", f"UNNAMED_{group_name}"))
                rules_effect = rule.get("effect", {}) or {}
                regras_aplicadas.append(rule_id)
                hits.append(_RuleHit(rule_id=rule_id, group=group_name, priority=int(rule.get("priority", 0))))

                if group_name == "gating_rules" or bool(rules_effect.get("block_viability", False)):
                    block_code = rules_effect.get("block_code", f"block_{rule_id.lower()}")
                    block_reason = rules_effect.get("block_reason", "Bloqueio por regra de gating")
                    bloqueios.append({"codigo": block_code, "motivo": block_reason, "regra_id": rule_id})
                    for a in self._normalize_alerts(rules_effect.get("alerts", []), rule_id=rule_id):
                        alertas.append(a)
                    score_penalty_total += float(rules_effect.get("score_penalty", 0) or 0)
                    continue

                macro_factors = rules_effect.get("macro_factors", {}) or {}
                rule_strategy = ((rule.get("conflict_resolution") or {}).get("strategy") or default_strategy)
                for macro, fator in macro_factors.items():
                    macro_norm = self._normalize_macro_name(str(macro))
                    fator_novo = float(fator)
                    fator_atual = effective_factors_pre_cap.get(macro_norm, 1.0)
                    fator_result = self._merge_factor(fator_atual, fator_novo, rule_strategy)
                    effective_factors_pre_cap[macro_norm] = fator_result
                    theoretical_factors[macro_norm] = fator_result
                    factor_sources.setdefault(macro_norm, []).append({
                        "regra_id": rule_id,
                        "strategy": rule_strategy,
                        "fator_regra": fator_novo,
                        "fator_resultante_teorico": round(fator_result, 6),
                    })

                if "fator_area_util_mult" in rules_effect:
                    fator_area_util *= float(rules_effect["fator_area_util_mult"])
                elif "fator_area_util" in rules_effect:
                    fator_area_util *= float(rules_effect["fator_area_util"])

                items = rules_effect.get("itens_custo_adicional") or rules_effect.get("items_add") or []
                for item in items:
                    item_c = copy.deepcopy(item)
                    item_c.setdefault("regra_id", rule_id)
                    itens_custo_adicional.append(item_c)

                for a in self._normalize_alerts(rules_effect.get("alerts", []), rule_id=rule_id):
                    alertas.append(a)

                score_penalty_total += float(rules_effect.get("score_penalty", 0) or 0)

        ajustes_custo: Dict[str, float] = {}
        breakdown_caps: List[Dict[str, Any]] = []
        for macro, fator_teorico in theoretical_factors.items():
            fator_efetivo = fator_teorico
            cap_cfg = active_caps.get(self._normalize_macro_name(macro), {})
            cap_warning = cap_cfg.get("cap_warning")
            cap_maximo = cap_cfg.get("cap_maximo")

            if cap_warning is not None and fator_teorico > float(cap_warning):
                alertas.append({
                    "severity": "warning",
                    "code": "cap_warning",
                    "mensagem": f"Fator teórico de {macro} ({fator_teorico:.2f}) acima do cap_warning ({float(cap_warning):.2f}). Revisão técnica recomendada.",
                    "regra_id": "ATLAS_CAP_WARNING",
                    "macroetapa": macro,
                })

            if cap_maximo is not None and fator_teorico > float(cap_maximo):
                fator_efetivo = float(cap_maximo)
                delta_clamp = fator_teorico - fator_efetivo
                cap_events.append({
                    "macroetapa": macro,
                    "fator_teorico": round(fator_teorico, 6),
                    "fator_efetivo": round(fator_efetivo, 6),
                    "delta_clamp": round(delta_clamp, 6),
                    "cap_maximo": float(cap_maximo),
                })
                alertas.append({
                    "severity": "critical",
                    "code": "cap_atingido",
                    "mensagem": f"Fator de {macro} clampado de {fator_teorico:.2f} para {float(cap_maximo):.2f} (cap_maximo).",
                    "regra_id": "ATLAS_CAP_MAX",
                    "macroetapa": macro,
                })

            ajustes_custo[macro] = round(max(1.0, fator_efetivo), 6)
            breakdown_caps.append({
                "macroetapa": macro,
                "fator_teorico": round(fator_teorico, 6),
                "fator_efetivo": round(max(1.0, fator_efetivo), 6),
                "cap_warning": float(cap_warning) if cap_warning is not None else None,
                "cap_maximo": float(cap_maximo) if cap_maximo is not None else None,
                "cap_aplicado": bool(cap_maximo is not None and fator_teorico > float(cap_maximo)),
                "fontes": factor_sources.get(macro, []),
            })

        alert_penalty_map = {"info": 1.0, "warning": 5.0, "critical": 12.0}
        score_from_alerts = sum(alert_penalty_map.get(str(a.get("severity", "")).lower(), 0.0) for a in alertas)
        score_raw = 100.0 - score_penalty_total - score_from_alerts
        score_fisico = int(round(max(0.0, min(100.0, score_raw))))

        alertas = self._dedupe_alerts(alertas)

        atlas_report: Dict[str, Any] = {
            "score_fisico": score_fisico,
            "ajustes_custo": {self._normalize_macro_name(k): round(float(v), 4) for k, v in ajustes_custo.items()},
            "itens_custo_adicional": itens_custo_adicional,
            "alertas": alertas,
            "regras_aplicadas": regras_aplicadas,
            "viabilidade_bloqueada": len(bloqueios) > 0,
            "bloqueios": bloqueios,
            "fator_area_util": round(max(0.0, min(1.0, fator_area_util)), 4),
            "metadata": {
                "ruleset_id": self._ruleset.get("metadata", {}).get("name", "ATLAS_RULESET"),
                "versao_ruleset": self._ruleset.get("version") or self._ruleset.get("metadata", {}).get("version") or "0.2.0",
                "cluster_regional": regional_meta.get("cluster_regional", cluster_regional or "BR_DEFAULT"),
                "caps_fator_custo_aplicados": active_caps,
                "regional_override_aplicado": regional_meta.get("regional_override_aplicado"),
                "conflict_default_strategy": default_strategy,
                "ruleset_fingerprint": self._ruleset_fingerprint,
                "breakdown_ajustes_atlas": breakdown_caps,
                "cap_events": cap_events,
                "hits": [hit.__dict__ for hit in hits],
            },
            "breakdown_ajustes": breakdown_caps,
        }

        if bloqueios and raise_on_block:
            raise ATLASBlockedException(bloqueios=bloqueios, mensagem="Viabilidade bloqueada por gating ATLAS", atlas_report=atlas_report)

        return atlas_report

    def _fingerprint_ruleset(self, ruleset: Dict[str, Any]) -> str:
        try:
            raw = json.dumps(ruleset, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        except TypeError:
            raw = repr(ruleset)
        return f"rs_{abs(hash(raw))}"

    def _normalize_macro_name(self, name: str) -> str:
        n = (name or "").strip().lower()
        mapping = {
            "fundacoes": "fundações",
            "fundações": "fundações",
            "terr": "terraplanagem",
            "terraplanagem": "terraplanagem",
            "infra": "infraestrutura",
            "infraestrutura": "infraestrutura",
            "contencoes": "contenções",
            "contenções": "contenções",
            "drenagem": "drenagem",
        }
        return mapping.get(n, name)

    def _normalize_metrics(self, terrain_metrics: Dict[str, Any]) -> Dict[str, Any]:
        m = copy.deepcopy(terrain_metrics or {})
        if "declividade_media_pct" not in m and "declividade_avg" in m:
            m["declividade_media_pct"] = m["declividade_avg"]
        if "declividade_max_pct" not in m and "declividade_max" in m:
            m["declividade_max_pct"] = m["declividade_max"]
        if "pct_app_area" not in m and "area_app_pct" in m:
            m["pct_app_area"] = m["area_app_pct"]
        if "solo_classe" not in m and "tipo_solo" in m:
            m["solo_classe"] = self._normalize_solo_classe(str(m["tipo_solo"]))

        flags = m.get("flags_risco", [])
        if isinstance(flags, list):
            flags_norm = {str(f).strip().lower() for f in flags}
            m.setdefault("flags_risco", list(flags_norm))
            m.setdefault("overlaps_area_uniao", "area_uniao" in flags_norm)
            m.setdefault("sirene_jud_ativo", "sirene_jud" in flags_norm)
            m.setdefault("indisponibilidade_ativo", "indisponibilidade" in flags_norm)

        infra = m.get("infra_saneamento") if isinstance(m.get("infra_saneamento"), dict) else {}
        infra = copy.deepcopy(infra)
        if "distancia_rede_esgoto_m" in m and "esgoto_proximo" not in infra:
            try:
                infra["esgoto_proximo"] = float(m["distancia_rede_esgoto_m"]) <= 500.0
            except Exception:
                pass
        if "drenagem_superficial" in m and "drenagem_superficial" not in infra:
            infra["drenagem_superficial"] = m["drenagem_superficial"]
        m["infra_saneamento"] = infra

        if "acesso_pavimentado" not in m and "distancia_pavimentacao_m" in m:
            try:
                m["acesso_pavimentado"] = float(m["distancia_pavimentacao_m"]) <= 0.0
            except Exception:
                pass
        return m

    def _normalize_solo_classe(self, tipo_solo: str) -> str:
        s = (tipo_solo or "").lower()
        if re.search(r"gleissolo|hidrom[oó]rf", s):
            return "gleissolo"
        if re.search(r"argissolo", s):
            return "argissolo"
        if re.search(r"latossolo", s):
            return "latossolo"
        if re.search(r"cambissolo", s):
            return "cambissolo"
        if re.search(r"espodossolo", s):
            return "espodossolo"
        return s.strip() or "desconhecido"

    def _resolve_caps(self, metrics: Dict[str, Any], cluster_regional: Optional[str]) -> Tuple[Dict[str, Dict[str, float]], Dict[str, Any]]:
        caps_cfg = self._ruleset.get("caps_fator_custo", {}) or {}
        default_caps = copy.deepcopy(caps_cfg.get("default", {}) or {})
        default_caps = {self._normalize_macro_name(k): v for k, v in default_caps.items()}
        regionals = caps_cfg.get("regional_overrides", []) or []
        applied = None
        if cluster_regional:
            for reg in regionals:
                if str(reg.get("id")) == str(cluster_regional):
                    applied = reg
                    break
        if applied is None:
            for reg in regionals:
                if self._eval_condition_tree(reg.get("when", {}), metrics):
                    applied = reg
                    break
        active_caps = copy.deepcopy(default_caps)
        if applied:
            overrides = copy.deepcopy(applied.get("overrides", {}) or {})
            for macro, cfg in overrides.items():
                if str(macro).startswith("_"):
                    continue
                macro_norm = self._normalize_macro_name(macro)
                active_caps.setdefault(macro_norm, {})
                active_caps[macro_norm].update(cfg or {})
        return active_caps, {
            "cluster_regional": (applied or {}).get("id") if applied else (cluster_regional or "BR_DEFAULT"),
            "regional_override_aplicado": (applied or {}).get("id"),
        }

    def _get_metric_value(self, metrics: Dict[str, Any], metric_path: str) -> Any:
        current: Any = metrics
        for part in str(metric_path).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _eval_leaf_condition(self, cond: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        metric = cond.get("metric")
        op = cond.get("op")
        value = cond.get("value")
        actual = self._get_metric_value(metrics, metric)
        op_alias = {"==":"eq","=":"eq","eq":"eq","!=":"ne","ne":"ne",">":"gt","gt":"gt",">=":"gte","gte":"gte","<":"lt","lt":"lt","<=":"lte","lte":"lte","in":"in","not_in":"not_in","contains":"contains","regex":"regex","matches":"regex"}
        op_n = op_alias.get(str(op).lower(), str(op).lower())
        try:
            if op_n == "eq": return actual == value
            if op_n == "ne": return actual != value
            if op_n == "gt": return actual is not None and float(actual) > float(value)
            if op_n == "gte": return actual is not None and float(actual) >= float(value)
            if op_n == "lt": return actual is not None and float(actual) < float(value)
            if op_n == "lte": return actual is not None and float(actual) <= float(value)
            if op_n == "in": return actual in (value or [])
            if op_n == "not_in": return actual not in (value or [])
            if op_n == "contains":
                if isinstance(actual, (list, tuple, set)): return value in actual
                if isinstance(actual, str): return str(value) in actual
                return False
            if op_n == "regex": return actual is not None and re.search(str(value), str(actual), flags=re.IGNORECASE) is not None
        except Exception:
            return False
        return False

    def _eval_condition_tree(self, cond: Dict[str, Any], metrics: Dict[str, Any]) -> bool:
        if not isinstance(cond, dict) or not cond:
            return False
        if "all" in cond:
            return all(self._eval_condition_tree(node, metrics) for node in (cond.get("all") or []))
        if "any" in cond:
            return any(self._eval_condition_tree(node, metrics) for node in (cond.get("any") or []))
        return self._eval_leaf_condition(cond, metrics)

    def _merge_factor(self, current_factor: float, new_factor: float, strategy: str) -> float:
        st = (strategy or "max_factor").lower()
        cf = float(current_factor or 1.0)
        nf = float(new_factor or 1.0)
        if st == "max_factor":
            return max(cf, nf)
        if st == "multiply":
            return (cf if cf > 0 else 1.0) * (nf if nf > 0 else 1.0)
        if st == "first_match":
            return cf if cf != 1.0 else nf
        if st == "sum_clamped":
            return 1.0 + max(0.0, cf - 1.0) + max(0.0, nf - 1.0)
        return max(cf, nf)

    def _normalize_alerts(self, alerts: List[Dict[str, Any]], rule_id: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for a in alerts or []:
            if not isinstance(a, dict):
                continue
            sev = str(a.get("severity", "warning")).lower()
            code = a.get("code", f"alert_{rule_id.lower()}")
            msg = a.get("mensagem") or a.get("message") or "Alerta ATLAS"
            item = copy.deepcopy(a)
            item["severity"] = sev
            item["code"] = code
            item["mensagem"] = msg
            item["regra_id"] = item.get("regra_id") or rule_id
            out.append(item)
        return out

    def _dedupe_alerts(self, alertas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for a in alertas:
            key = (a.get("severity"), a.get("code"), a.get("regra_id"), a.get("macroetapa"), a.get("mensagem"))
            if key in seen:
                continue
            seen.add(key)
            out.append(a)
        return out
