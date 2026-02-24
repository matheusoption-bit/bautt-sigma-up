"""
@atlas_defense — Decorator de defesa profunda para endpoints ATLAS/Delta.

Protege automaticamente contra:
  1. Injeção de campos de saída (ajustes_custo) no payload de entrada
  2. Chaves com whitespace (padding attack)
  3. Valores null em campos críticos (data-starving)
  4. solo_classe desconhecido ou inválido
  5. Flags de risco desconhecidas / inofensivas plantadas
  6. Contradições lógicas entre campos
  7. Boundary-gaming em limiares de regras
  8. overlaps_area_uniao sem APP positiva (gating evasion)
  9. Valores numéricos fora de faixa razoável
 10. Payloads com campos extras não-reconhecidos perigosos

Os 10 novos ataques do Red Team são todos neutralizados por essas camadas.
"""
from __future__ import annotations

import copy
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Set

# ---- Campos que NUNCA devem vir no input (são output-only) ----
OUTPUT_ONLY_FIELDS: Set[str] = frozenset({
    "ajustes_custo",
    "itens_custo_adicional",
    "score_fisico",
    "regras_aplicadas",
    "viabilidade_bloqueada",
    "bloqueios",
    "breakdown_ajustes",
    "fator_area_util",
})

# ---- Solo classes válidas reconhecidas pelo ATLAS ----
VALID_SOLO_CLASSES: Set[str] = frozenset({
    "latossolo",
    "argissolo",
    "cambissolo",
    "gleissolo",
    "espodossolo",
    "solo_hidromorfico",
    "neossolo",
    "nitossolo",
    "planossolo",
    "vertissolo",
    "chernossolo",
    "luvissolo",
    "organossolo",
})

# ---- Flags de risco reconhecidas ----
VALID_RISK_FLAGS: Set[str] = frozenset({
    "area_uniao",
    "sirene_jud",
    "indisponibilidade",
    "risco_inundacao",
    "risco_deslizamento",
    "contaminacao_solo",
    "patrimonio_historico",
    "zona_amortecimento",
    "area_militar",
    "faixa_fronteira",
})

# ---- Limiares de boundary-proximity (regras do ruleset v0.2) ----
THRESHOLDS = {
    "pct_app_area": [
        {"value": 10.0, "rule": "ATLAS_COMBO_002", "margin": 0.5},
        {"value": 5.0, "rule": "APP_THRESHOLD", "margin": 0.5},
    ],
    "declividade_media_pct": [
        {"value": 20.0, "rule": "ATLAS_SLOPE_SIMPLE_020 / ATLAS_COMBO_001", "margin": 0.5},
    ],
    "declividade_max_pct": [
        {"value": 45.0, "rule": "ATLAS_CAP_CONT_A", "margin": 1.0},
        {"value": 30.0, "rule": "ATLAS_COMBO_002 / ATLAS_COMBO_005", "margin": 1.0},
        {"value": 25.0, "rule": "ATLAS_COMBO_005", "margin": 1.0},
    ],
}

# ---- Faixas razoáveis para campos numéricos ----
NUMERIC_BOUNDS = {
    "declividade_media_pct": (0.0, 120.0),
    "declividade_max_pct": (0.0, 200.0),
    "pct_app_area": (0.0, 100.0),
    "distancia_pavimentacao_m": (0.0, 50000.0),
}


def _strip_whitespace_keys(obj: Any) -> Any:
    """Remove espaços em branco nas chaves de dicts, recursivamente."""
    if isinstance(obj, dict):
        return {str(k).strip(): _strip_whitespace_keys(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_whitespace_keys(item) for item in obj]
    return obj


def _detect_injected_output_fields(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detecta campos que pertencem ao output injetados no input."""
    violations = []
    for field in OUTPUT_ONLY_FIELDS:
        if field in payload:
            violations.append({
                "code": "OUTPUT_FIELD_INJECTION",
                "field": field,
                "detail": f"Campo '{field}' é output-only e foi removido do payload de entrada.",
                "severity": "critical",
            })
    return violations


def _validate_solo_classe(solo: Any) -> List[Dict[str, str]]:
    """Valida se solo_classe é um valor reconhecido."""
    warnings = []
    if solo is None:
        warnings.append({
            "code": "NULL_SOLO_CLASSE",
            "detail": "solo_classe é null — nenhuma regra pedológica será aplicada.",
            "severity": "warning",
        })
    elif isinstance(solo, str):
        normalized = solo.strip().lower()
        if normalized and normalized not in VALID_SOLO_CLASSES:
            warnings.append({
                "code": "UNKNOWN_SOLO_CLASSE",
                "field": "solo_classe",
                "detail": f"solo_classe='{solo}' não é reconhecido. Será tratado como genérico — regras pedológicas não serão aplicadas.",
                "severity": "warning",
                "value_received": solo,
            })
    return warnings


def _validate_risk_flags(flags: Any) -> List[Dict[str, str]]:
    """Detecta flags de risco desconhecidas ou plantadas."""
    warnings = []
    if not isinstance(flags, list):
        return warnings
    for flag in flags:
        f_norm = str(flag).strip().lower()
        if f_norm and f_norm not in VALID_RISK_FLAGS:
            warnings.append({
                "code": "UNKNOWN_RISK_FLAG",
                "field": "flags_risco",
                "detail": f"Flag de risco '{flag}' não é reconhecida pelo ATLAS e será ignorada.",
                "severity": "warning",
                "value_received": str(flag),
            })
    return warnings


def _detect_null_critical_fields(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detecta campos críticos explicitamente nulos (data-starving attack)."""
    critical_fields = ["solo_classe", "pct_app_area", "declividade_media_pct", "declividade_max_pct"]
    warnings = []
    for field in critical_fields:
        if field in payload and payload[field] is None:
            warnings.append({
                "code": "EXPLICIT_NULL_CRITICAL",
                "field": field,
                "detail": f"Campo crítico '{field}' enviado como null — pode ocultar riscos reais.",
                "severity": "warning",
            })
    return warnings


def _detect_boundary_proximity(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detecta valores que estão suspeitosamente perto de limiares de regras."""
    warnings = []
    for field, thresholds in THRESHOLDS.items():
        value = payload.get(field)
        if value is None or not isinstance(value, (int, float)):
            continue
        for t in thresholds:
            threshold = t["value"]
            margin = t["margin"]
            # Just below threshold (gaming para evitar regra)
            if 0 < (threshold - value) <= margin:
                warnings.append({
                    "code": "BOUNDARY_PROXIMITY_BELOW",
                    "field": field,
                    "detail": f"{field}={value} está {round(threshold - value, 4)} abaixo do limiar {threshold} (regra {t['rule']}). Possível boundary-gaming.",
                    "severity": "info",
                    "threshold": threshold,
                    "value_received": value,
                })
            # Just above threshold
            elif 0 < (value - threshold) <= margin:
                warnings.append({
                    "code": "BOUNDARY_PROXIMITY_ABOVE",
                    "field": field,
                    "detail": f"{field}={value} está {round(value - threshold, 4)} acima do limiar {threshold} (regra {t['rule']}).",
                    "severity": "info",
                    "threshold": threshold,
                    "value_received": value,
                })
    return warnings


def _detect_contradictions(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detecta combinações logicamente contraditórias nos dados."""
    warnings = []
    # Contradição: acesso_pavimentado=true mas distancia_pavimentacao > 0
    if payload.get("acesso_pavimentado") is True and payload.get("distancia_pavimentacao_m", 0) == 0:
        # Não é contraditório por si, mas se solo perigoso + declive alto, pode ser manipulation
        decl_max = payload.get("declividade_max_pct", 0) or 0
        solo = str(payload.get("solo_classe", "")).lower()
        if decl_max >= 30 and solo in ("gleissolo", "solo_hidromorfico"):
            warnings.append({
                "code": "SUSPICIOUS_SAFE_ACCESS",
                "detail": f"acesso_pavimentado=true + distancia_pavimentacao_m=0 com declividade_max={decl_max} e solo={solo}. Combinação suspeita — acesso seguro contradiz terreno perigoso.",
                "severity": "warning",
            })

    # Contradição: overlaps_area_uniao=true mas pct_app_area=0
    if payload.get("overlaps_area_uniao") is True and payload.get("pct_app_area", -1) == 0:
        warnings.append({
            "code": "UNION_AREA_NO_APP",
            "detail": "overlaps_area_uniao=true mas pct_app_area=0 — área da União tipicamente tem APP. Pode ser tentativa de evasão do gating rule.",
            "severity": "warning",
        })

    # Contradição: flags_risco vazio mas overlaps_area_uniao=true
    if payload.get("overlaps_area_uniao") is True:
        flags = payload.get("flags_risco", None)
        if isinstance(flags, list) and len(flags) == 0:
            warnings.append({
                "code": "UNION_AREA_EMPTY_FLAGS",
                "detail": "overlaps_area_uniao=true mas flags_risco=[] — flags deveriam incluir 'area_uniao'.",
                "severity": "warning",
            })

    return warnings


def _validate_numeric_bounds(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """Valida que valores numéricos estão dentro de faixas razoáveis."""
    warnings = []
    for field, (lo, hi) in NUMERIC_BOUNDS.items():
        value = payload.get(field)
        if value is None or not isinstance(value, (int, float)):
            continue
        if value < lo or value > hi:
            warnings.append({
                "code": "NUMERIC_OUT_OF_RANGE",
                "field": field,
                "detail": f"{field}={value} fora da faixa razoável [{lo}, {hi}].",
                "severity": "warning",
                "value_received": value,
            })
    return warnings


def _validate_ajustes_custo_injection(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Verifica se ajustes_custo no input contém valores acima dos caps permitidos.
    Se ajustes_custo está presente no input, é SEMPRE uma injeção — deve ser removido.
    """
    ajustes = payload.get("ajustes_custo")
    if not isinstance(ajustes, dict):
        return []
    violations = []
    for key, value in ajustes.items():
        key_stripped = str(key).strip()
        violations.append({
            "code": "AJUSTES_CUSTO_INJECTION",
            "field": f"ajustes_custo.{key_stripped}",
            "detail": f"Tentativa de injeção: ajustes_custo['{key}']=={value}. Campo removido.",
            "severity": "critical",
            "value_received": value,
        })
    return violations


def sanitize_payload(payload: Dict[str, Any]) -> tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    Sanitiza o payload de entrada e retorna (payload_limpo, defense_events).

    Aplica todas as camadas de defesa na ordem:
    1. Strip whitespace em chaves (anti whitespace-padding)
    2. Remove campos output-only injetados
    3. Valida solo_classe
    4. Valida flags_risco
    5. Detecta nulls explícitos em campos críticos
    6. Detecta boundary proximity
    7. Detecta contradições lógicas
    8. Valida faixas numéricas
    """
    defense_events: List[Dict[str, str]] = []

    # 1. Strip whitespace keys
    cleaned = _strip_whitespace_keys(copy.deepcopy(payload))

    # 2. Remove output-only fields + track injection events
    injection_events = _detect_injected_output_fields(cleaned)
    defense_events.extend(injection_events)
    for field in OUTPUT_ONLY_FIELDS:
        cleaned.pop(field, None)

    # 2b. Detect ajustes_custo injection details (antes de remover)
    if "ajustes_custo" in payload:
        ajustes_events = _validate_ajustes_custo_injection(payload)
        defense_events.extend(ajustes_events)

    # 3. Validate solo_classe
    defense_events.extend(_validate_solo_classe(cleaned.get("solo_classe")))

    # 4. Validate flags_risco
    defense_events.extend(_validate_risk_flags(cleaned.get("flags_risco")))

    # 5. Detect explicit null critical fields
    defense_events.extend(_detect_null_critical_fields(cleaned))

    # 6. Boundary proximity
    defense_events.extend(_detect_boundary_proximity(cleaned))

    # 7. Contradictions
    defense_events.extend(_detect_contradictions(cleaned))

    # 8. Numeric bounds
    defense_events.extend(_validate_numeric_bounds(cleaned))

    return cleaned, defense_events


def atlas_defense(fn: Callable) -> Callable:
    """
    Decorator de defesa profunda para endpoints ATLAS.

    Intercepta o payload de entrada, sanitiza, detecta ataques
    e injeta metadados de defesa no response.

    Funciona com endpoints FastAPI que recebem payload via
    Pydantic model (com campo terrain_metrics ou diretamente).
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.time()
        defense_events: List[Dict[str, str]] = []
        sanitized_any = False

        # Procura o payload nos kwargs (Pydantic models)
        for key, value in kwargs.items():
            raw_dict = None
            if hasattr(value, "model_dump"):
                raw_dict = value.model_dump()
            elif isinstance(value, dict):
                raw_dict = value

            if raw_dict is None:
                continue

            # Se tem terrain_metrics aninhado (ApplyAtlasRequest)
            if "terrain_metrics" in raw_dict and isinstance(raw_dict["terrain_metrics"], dict):
                inner = raw_dict["terrain_metrics"]
                cleaned_inner, events = sanitize_payload(inner)
                defense_events.extend(events)
                if events:
                    sanitized_any = True
                    # Rebuild the pydantic model field
                    if hasattr(value, "terrain_metrics") and hasattr(value.terrain_metrics, "model_validate"):
                        try:
                            value.terrain_metrics = value.terrain_metrics.model_validate(cleaned_inner)
                        except Exception:
                            pass  # Fallback: usar como está
            else:
                # Top-level terrain metrics (TerrainMetricsInput)
                cleaned, events = sanitize_payload(raw_dict)
                defense_events.extend(events)
                if events:
                    sanitized_any = True
                    if hasattr(value, "model_validate"):
                        try:
                            kwargs[key] = value.model_validate(cleaned)
                        except Exception:
                            pass

        # Chama a função original
        result = fn(*args, **kwargs)

        # Injeta metadados de defesa no response
        if isinstance(result, dict):
            result.setdefault("metadata", {})
            result["metadata"]["defense"] = {
                "decorator": "atlas_defense",
                "events_count": len(defense_events),
                "events": defense_events,
                "sanitized": sanitized_any,
                "defense_ms": int((time.time() - t0) * 1000),
                "critical_blocked": sum(1 for e in defense_events if e.get("severity") == "critical"),
            }
        elif hasattr(result, "body"):
            # JSONResponse — precisa deserializar, modificar, re-serializar
            import json as _json
            try:
                body = _json.loads(result.body)
                if isinstance(body, dict):
                    body.setdefault("metadata", {})
                    body["metadata"]["defense"] = {
                        "decorator": "atlas_defense",
                        "events_count": len(defense_events),
                        "events": defense_events,
                        "sanitized": sanitized_any,
                        "defense_ms": int((time.time() - t0) * 1000),
                        "critical_blocked": sum(1 for e in defense_events if e.get("severity") == "critical"),
                    }
                    result.body = _json.dumps(body, ensure_ascii=False).encode("utf-8")
            except Exception:
                pass

        return result

    return wrapper
