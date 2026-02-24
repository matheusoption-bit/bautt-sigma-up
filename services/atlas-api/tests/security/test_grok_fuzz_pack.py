"""
Grok Fuzz Pack — 30 data-driven cases contra a API ATLAS real.

Cada caso é lido de grok_fuzz_pack.json e disparado via TestClient.
Nenhum stub, nenhum assert True cego.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi.testclient import TestClient

from atlas_api.main import app

FUZZ_DATA_PATH = Path(__file__).parent / "grok_fuzz_pack.json"
CLIENT = TestClient(app, raise_server_exceptions=False)


def _load_cases() -> List[Dict[str, Any]]:
    return json.loads(FUZZ_DATA_PATH.read_text(encoding="utf-8"))


CASES = _load_cases()
IDS = [c["id"] for c in CASES]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_fuzz_case(case: Dict[str, Any]):
    """Executa um caso de fuzz contra POST /atlas/evaluate."""
    payload = dict(case["payload"])
    cluster = case.get("cluster_regional", "BR_DEFAULT")
    payload.setdefault("cluster_regional", cluster)

    resp = CLIENT.post("/atlas/evaluate", json=payload)

    # --- status code ---
    assert resp.status_code == case["expect_status"], (
        f"[{case['id']}] esperava {case['expect_status']}, recebeu {resp.status_code}: {resp.text}"
    )

    if resp.status_code != 200:
        return  # nada mais a validar

    data = resp.json()

    # --- coverage (metadata.coverage_score) ---
    if "assert_coverage_below" in case:
        cov = data.get("metadata", {}).get("coverage_score", 1.0)
        assert cov < case["assert_coverage_below"], (
            f"[{case['id']}] coverage {cov} não é < {case['assert_coverage_below']}"
        )

    # --- gating (viabilidade_bloqueada) ---
    if "assert_blocked" in case:
        blocked = data.get("viabilidade_bloqueada", False)
        assert blocked == case["assert_blocked"], (
            f"[{case['id']}] viabilidade_bloqueada={blocked}, esperava={case['assert_blocked']}"
        )

    # --- regra aplicada ---
    if "assert_rule_applied" in case:
        applied = data.get("regras_aplicadas", [])
        assert case["assert_rule_applied"] in applied, (
            f"[{case['id']}] regra {case['assert_rule_applied']} não está em {applied}"
        )

    # --- cap aplicado (macroetapa) ---
    if "assert_cap_applied" in case:
        macro = case["assert_cap_applied"]
        caps_events = data.get("metadata", {}).get("cap_events", [])
        breakdown = data.get("breakdown_ajustes", [])
        cap_hit = any(e.get("macroetapa") == macro for e in caps_events) or \
                  any(b.get("macroetapa") == macro and b.get("cap_aplicado") for b in breakdown)
        assert cap_hit, (
            f"[{case['id']}] cap não aplicado para macroetapa '{macro}'"
        )

    # --- score bounds ---
    score = data.get("score_fisico", 0)
    if "assert_score_above" in case:
        assert score >= case["assert_score_above"], (
            f"[{case['id']}] score_fisico={score}, esperava >= {case['assert_score_above']}"
        )
    if "assert_score_below" in case:
        assert score <= case["assert_score_below"], (
            f"[{case['id']}] score_fisico={score}, esperava <= {case['assert_score_below']}"
        )
