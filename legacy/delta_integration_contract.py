from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List
import copy
import hashlib
import json


class ATLASBlockedException(Exception):
    def __init__(self, bloqueios: List[Dict[str, Any]], mensagem: str = "Viabilidade bloqueada pelo ATLAS"):
        self.bloqueios = bloqueios or []
        self.mensagem = mensagem
        super().__init__(f"{mensagem}: {self.bloqueios}")


@dataclass
class OrcamentoAjustado:
    custo_total_base_brl: float
    custo_total_revisado_brl: float
    custo_total_itens_adicionais_brl: float
    custo_total_contingencia_brl: float
    macroetapas_base_brl: Dict[str, float]
    macroetapas_ajustadas_brl: Dict[str, float]
    fatores_aplicados: Dict[str, float]
    itens_custo_adicional: List[Dict[str, Any]]
    receita: Dict[str, float]
    impacto_atlas: Dict[str, Any]
    rastreabilidade: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _canonical_hash(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sum_dict_values(d: Dict[str, Any]) -> float:
    total = 0.0
    for _, v in (d or {}).items():
        try:
            total += float(v)
        except (TypeError, ValueError):
            continue
    return total


def _estimate_item_cost(item: Dict[str, Any], premissas_area: Dict[str, Any]) -> float:
    if "cost_brl" in item:
        return float(item["cost_brl"])

    faixa = item.get("custo_estimado_brl_range")
    if isinstance(faixa, list) and len(faixa) == 2:
        minimo, maximo = float(faixa[0]), float(faixa[1])
        custo_unit_medio = (minimo + maximo) / 2.0
    else:
        custo_unit_medio = 0.0

    unidade_ref = str(item.get("unidade_ref", "vb")).lower()
    hint = str(item.get("quantidade_formula_hint", "")).strip()

    if unidade_ref == "vb":
        return custo_unit_medio

    if unidade_ref == "m" and hint == "distancia_pavimentacao_m":
        qtd = float(premissas_area.get("distancia_pavimentacao_m", 0) or 0)
        return custo_unit_medio * qtd

    return custo_unit_medio


def _validate_cronograma(crono: Dict[str, Any]) -> None:
    meses = int(crono.get("meses", 0))
    custos = crono.get("distribuicao_custos", [])
    receitas = crono.get("distribuicao_receitas", [])
    if meses <= 0:
        raise ValueError("cronograma_financeiro.meses deve ser > 0")
    if len(custos) != meses or len(receitas) != meses:
        raise ValueError("distribuicao_custos/receitas devem ter tamanho == meses")
    if abs(sum(custos) - 1.0) > 1e-6:
        raise ValueError("distribuicao_custos deve somar 1.0")
    if abs(sum(receitas) - 1.0) > 1e-6:
        raise ValueError("distribuicao_receitas deve somar 1.0")


def aplicar_atlas_ao_orcamento(orcamento_cub: Dict[str, Any], atlas_report: Dict[str, Any]) -> OrcamentoAjustado:
    atlas_report = atlas_report or {}
    if bool(atlas_report.get("viabilidade_bloqueada", False)):
        raise ATLASBlockedException(bloqueios=atlas_report.get("bloqueios", []))

    data = copy.deepcopy(orcamento_cub or {})

    premissas_area = data.setdefault("premissas_area", {})
    premissas_preco = data.setdefault("premissas_preco", {})
    orc_cub = data.setdefault("orcamento_cub", {})
    macro_base = orc_cub.setdefault("macroetapas", {})
    crono = data.setdefault("cronograma_financeiro", {})
    rast = data.setdefault("rastreabilidade", {})

    _validate_cronograma(crono)

    fatores = atlas_report.get("ajustes_custo", {}) or {}
    itens_atlas = copy.deepcopy(atlas_report.get("itens_custo_adicional", []) or [])
    fator_area_util = float(atlas_report.get("fator_area_util", 1.0) or 1.0)

    for macro in ["fundações", "terraplanagem", "infraestrutura", "contenções", "drenagem"]:
        macro_base.setdefault(macro, 0.0)

    macroetapas_base_brl = {k: float(v) for k, v in macro_base.items()}
    custo_macro_base = _sum_dict_values(macroetapas_base_brl)

    custo_terreno_brl = float(premissas_preco.get("custo_terreno_brl", 0.0) or 0.0)
    custo_projetos_licencas_brl = float(premissas_preco.get("custo_projetos_licencas_brl", 0.0) or 0.0)

    macroetapas_ajustadas_brl = {}
    breakdown_ajustes = []
    for macro, valor_base in macroetapas_base_brl.items():
        fator = float(fatores.get(macro, 1.0) or 1.0)
        valor_aj = valor_base * fator
        macroetapas_ajustadas_brl[macro] = round(valor_aj, 2)
        if abs(fator - 1.0) > 1e-9:
            breakdown_ajustes.append({
                "macroetapa": macro,
                "valor_base_brl": round(valor_base, 2),
                "fator_atlas": fator,
                "valor_ajustado_brl": round(valor_aj, 2),
                "impacto_brl": round(valor_aj - valor_base, 2)
            })

    custo_macro_ajustado = _sum_dict_values(macroetapas_ajustadas_brl)

    itens_precificados = []
    total_itens_adicionais = 0.0
    for item in itens_atlas:
        item_p = copy.deepcopy(item)
        est = _estimate_item_cost(item_p, premissas_area)
        item_p["cost_brl_estimado"] = round(est, 2)
        total_itens_adicionais += est
        itens_precificados.append(item_p)

    contingencia_pct = float(premissas_preco.get("contingencia_pct_custo", 0.03) or 0.0)
    custo_contingencia = (custo_macro_ajustado + total_itens_adicionais) * contingencia_pct

    custo_total_base = custo_macro_base + custo_terreno_brl + custo_projetos_licencas_brl
    custo_total_revisado = (
        custo_macro_ajustado
        + total_itens_adicionais
        + custo_contingencia
        + custo_terreno_brl
        + custo_projetos_licencas_brl
    )

    area_computavel_base = float(premissas_area.get("area_computavel_base_m2", 0.0) or 0.0)
    area_vendavel_base = float(premissas_area.get("area_vendavel_base_m2", 0.0) or 0.0)
    preco_venda_m2 = float(premissas_preco.get("preco_venda_m2", 0.0) or 0.0)

    area_computavel_ajustada = area_computavel_base * fator_area_util
    area_vendavel_ajustada = area_vendavel_base * fator_area_util

    vgv_base = area_vendavel_base * preco_venda_m2
    vgv_ajustado = area_vendavel_ajustada * preco_venda_m2

    taxa_com_pct = float(premissas_preco.get("taxa_comercializacao_pct_vgv", 0.04) or 0.0)
    taxa_imp_pct = float(premissas_preco.get("taxa_impostos_pct_vgv", 0.06) or 0.0)

    custo_comercial_base = vgv_base * taxa_com_pct
    custo_impostos_base = vgv_base * taxa_imp_pct
    custo_comercial_aj = vgv_ajustado * taxa_com_pct
    custo_impostos_aj = vgv_ajustado * taxa_imp_pct

    audit_payload = {
        "orcamento_base": {
            "macroetapas": macroetapas_base_brl,
            "premissas_area": {
                "area_computavel_base_m2": area_computavel_base,
                "area_vendavel_base_m2": area_vendavel_base,
            },
            "premissas_preco": {
                "preco_venda_m2": preco_venda_m2,
                "custo_terreno_brl": custo_terreno_brl,
                "custo_projetos_licencas_brl": custo_projetos_licencas_brl,
                "taxa_comercializacao_pct_vgv": taxa_com_pct,
                "taxa_impostos_pct_vgv": taxa_imp_pct,
                "contingencia_pct_custo": contingencia_pct,
            }
        },
        "atlas": {
            "fatores": fatores,
            "fator_area_util": fator_area_util,
            "itens": itens_precificados,
            "regras_aplicadas": atlas_report.get("regras_aplicadas", []),
            "metadata": atlas_report.get("metadata", {})
        },
        "delta_engine_version": rast.get("delta_engine_version", "0.1.0")
    }
    hash_rastreabilidade = _canonical_hash(audit_payload)

    impacto_atlas = {
        "incremento_custo_macro_brl": round(custo_macro_ajustado - custo_macro_base, 2),
        "incremento_itens_adicionais_brl": round(total_itens_adicionais, 2),
        "incremento_contingencia_brl": round(custo_contingencia, 2),
        "delta_vgv_brl": round(vgv_ajustado - vgv_base, 2),
        "fator_area_util": round(fator_area_util, 4),
        "breakdown_ajustes": breakdown_ajustes,
    }

    receita = {
        "area_computavel_base_m2": round(area_computavel_base, 2),
        "area_computavel_ajustada_m2": round(area_computavel_ajustada, 2),
        "area_vendavel_base_m2": round(area_vendavel_base, 2),
        "area_vendavel_ajustada_m2": round(area_vendavel_ajustada, 2),
        "preco_venda_m2": round(preco_venda_m2, 2),
        "vgv_base_brl": round(vgv_base, 2),
        "vgv_ajustado_brl": round(vgv_ajustado, 2),
        "custo_comercial_base_brl": round(custo_comercial_base, 2),
        "custo_impostos_base_brl": round(custo_impostos_base, 2),
        "custo_comercial_ajustado_brl": round(custo_comercial_aj, 2),
        "custo_impostos_ajustado_brl": round(custo_impostos_aj, 2),
    }

    return OrcamentoAjustado(
        custo_total_base_brl=round(custo_total_base, 2),
        custo_total_revisado_brl=round(custo_total_revisado, 2),
        custo_total_itens_adicionais_brl=round(total_itens_adicionais, 2),
        custo_total_contingencia_brl=round(custo_contingencia, 2),
        macroetapas_base_brl={k: round(v, 2) for k, v in macroetapas_base_brl.items()},
        macroetapas_ajustadas_brl=macroetapas_ajustadas_brl,
        fatores_aplicados={k: round(float(v), 4) for k, v in fatores.items()},
        itens_custo_adicional=itens_precificados,
        receita=receita,
        impacto_atlas=impacto_atlas,
        rastreabilidade={
            "hash_rastreabilidade": hash_rastreabilidade,
            "delta_engine_version": rast.get("delta_engine_version", "0.1.0"),
            "atlas_engine_version": atlas_report.get("metadata", {}).get("versao_ruleset"),
            "atlas_ruleset_id": atlas_report.get("metadata", {}).get("ruleset_id"),
            "atlas_regras_aplicadas": atlas_report.get("regras_aplicadas", []),
            "atlas_regras_aplicadas_qtd": len(atlas_report.get("regras_aplicadas", [])),
        }
    )
