from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from atlas_api.schemas import ApplyAtlasRequest, ATLASReportResponse, DeltaApplyResponse, TerrainMetricsInput

# ---- imports dos engines (instalados via pip install -e .) ----
from atlas_engine.atlas_engine import ATLASEngine, ATLASBlockedException
from delta_engine.integration_contract import aplicar_atlas_ao_orcamento

# ---- carregamento do ruleset ----
# Caminho para o ruleset canônico do atlas-engine
# parents[0]=atlas_api, [1]=src, [2]=atlas-api, [3]=services
RULESET_PATH = (Path(__file__).resolve().parents[3] / "atlas-engine" / "config" / "atlas_ruleset_v0.2.json")

def _load_ruleset() -> Dict[str, Any]:
    # Prefer config JSON if present, else minimal fallback
    if RULESET_PATH.exists():
        import json
        return json.loads(RULESET_PATH.read_text(encoding="utf-8"))
    return {"version": "0.2.0", "metadata": {"name": "ATLAS_RULESET"}}

ENGINE = ATLASEngine(ruleset=_load_ruleset())

app = FastAPI(title="Bautt ATLAS API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time())}

@app.get("/atlas/ruleset/version")
def ruleset_version():
    # atlas-engine stores fingerprint internally; expose best-effort
    meta = {"ruleset_version": ENGINE.ruleset.get("version"), "ruleset_name": (ENGINE.ruleset.get("metadata") or {}).get("name")}
    try:
        meta["ruleset_fingerprint"] = getattr(ENGINE, "_ruleset_fingerprint", None)
    except Exception:
        meta["ruleset_fingerprint"] = None
    return meta

@app.post("/atlas/evaluate", response_model=ATLASReportResponse)
def atlas_evaluate(payload: TerrainMetricsInput):
    t0 = time.time()
    terrain = payload.terrain_metrics_dict()

    # In API, default is not to raise on block (shadow-friendly)
    report = ENGINE.evaluate(
        terrain_metrics=terrain,
        cluster_regional=payload.cluster_regional,
        raise_on_block=False,
    )

    # Telemetry: coverage score for critical fields (addresses FM-008)
    crit_fields = payload.critical_fields
    missing = [f for f in crit_fields if payload.get_by_path(terrain, f) is None]
    coverage = 1.0 - (len(missing) / len(crit_fields)) if crit_fields else 1.0

    report.setdefault("metadata", {})
    report["metadata"].update({
        "tempo_evaluate_ms": int((time.time() - t0) * 1000),
        "coverage_score": round(coverage, 4),
        "campos_criticos_ausentes": missing,
        "validation_warnings": payload.validation_warnings,
    })
    return report

@app.post("/delta/apply-atlas", response_model=DeltaApplyResponse)
def delta_apply_atlas(req: ApplyAtlasRequest):
    terrain = req.terrain_metrics.terrain_metrics_dict()
    report = ENGINE.evaluate(
        terrain_metrics=terrain,
        cluster_regional=req.cluster_regional,
        raise_on_block=False,
    )

    if report.get("viabilidade_bloqueada"):
        return JSONResponse(
            status_code=409,
            content={
                "error": {"code": "409_GATING", "detail": "Viabilidade bloqueada pelo ATLAS", "bloqueios": report.get("bloqueios", [])},
                "atlas_report": report,
            },
        )

    try:
        out = aplicar_atlas_ao_orcamento(req.orcamento_base, report).to_dict()
    except ATLASBlockedException as e:
        raise HTTPException(status_code=409, detail={"code": "409_GATING", "bloqueios": getattr(e, "bloqueios", [])})
    except Exception as e:
        raise HTTPException(status_code=422, detail={"code": "422_DELTA_ERROR", "detail": str(e)})

    return {"atlas_report": report, "orcamento_ajustado": out}
