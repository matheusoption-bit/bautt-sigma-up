"""
Hypothesis property-based tests para ATLASEngine.

5 propriedades verificadas com ~200 exemplos cada:
  1. score_fisico sempre entre 0..100
  2. ajustes_custo nunca abaixo de 1.0
  3. cap_maximo nunca ultrapassado
  4. gating bloqueio determinístico com mesmos inputs
  5. fator_area_util entre 0.0 e 1.0
"""
from __future__ import annotations

import json
from pathlib import Path

from hypothesis import given, settings, strategies as st

from atlas_engine.atlas_engine import ATLASEngine

# ---- Carrega ruleset real ----
_RULESET_PATH = (
    Path(__file__).resolve().parents[3]
    / "atlas-engine"
    / "config"
    / "atlas_ruleset_v0.2.json"
)
_RULESET = json.loads(_RULESET_PATH.read_text(encoding="utf-8"))
ENGINE = ATLASEngine(ruleset=_RULESET)

# ---- Estratégias ----
solo_classes = st.sampled_from(
    ["latossolo", "argissolo", "gleissolo", "cambissolo", "solo_hidromorfico", "espodossolo", "desconhecido"]
)
drenagem_vals = st.sampled_from(["boa", "regular", "precaria", "inexistente"])
clusters = st.sampled_from(["BR_DEFAULT", "SC_LITORAL"])


def _build_terrain(
    decliv_media, decliv_max, pct_app, solo, overlaps, deslizamento,
    acesso_pav, dist_pav, esgoto, drenagem,
):
    """Monta dict de métricas a partir de valores gerados."""
    t = {
        "declividade_media_pct": decliv_media,
        "declividade_max_pct": decliv_max,
        "pct_app_area": pct_app,
        "solo_classe": solo,
        "overlaps_area_uniao": overlaps,
        "historico_deslizamento_r4": deslizamento,
        "acesso_pavimentado": acesso_pav,
        "distancia_pavimentacao_m": dist_pav,
        "infra_saneamento": {
            "esgoto_proximo": esgoto,
            "drenagem_superficial": drenagem,
        },
    }
    return t


terrain_strategy = st.fixed_dictionaries({}).flatmap(
    lambda _: st.tuples(
        st.floats(min_value=0, max_value=100),     # decliv_media
        st.floats(min_value=0, max_value=100),      # decliv_max
        st.floats(min_value=0, max_value=100),       # pct_app
        solo_classes,                                 # solo
        st.booleans(),                                # overlaps
        st.booleans(),                                # deslizamento
        st.booleans(),                                # acesso_pav
        st.floats(min_value=0, max_value=2000),       # dist_pav
        st.booleans(),                                # esgoto
        drenagem_vals,                                # drenagem
    ).map(lambda args: _build_terrain(*args))
)


# ---- Propriedades ----

@settings(max_examples=200, deadline=None)
@given(terrain=terrain_strategy, cluster=clusters)
def test_score_fisico_bounds(terrain, cluster):
    """P1 — score_fisico sempre em [0, 100]."""
    report = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    assert 0 <= report["score_fisico"] <= 100


@settings(max_examples=200, deadline=None)
@given(terrain=terrain_strategy, cluster=clusters)
def test_ajustes_custo_never_below_one(terrain, cluster):
    """P2 — Nenhum fator de custo efetivo < 1.0."""
    report = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    for macro, fator in report["ajustes_custo"].items():
        assert fator >= 1.0, f"{macro} com fator {fator} < 1.0"


@settings(max_examples=200, deadline=None)
@given(terrain=terrain_strategy, cluster=clusters)
def test_caps_never_exceeded(terrain, cluster):
    """P3 — Fator efetivo nunca ultrapassa cap_maximo definido no ruleset."""
    report = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    caps = report.get("metadata", {}).get("caps_fator_custo_aplicados", {})
    for macro, fator in report["ajustes_custo"].items():
        cap_cfg = caps.get(macro, {})
        cap_max = cap_cfg.get("cap_maximo")
        if cap_max is not None:
            assert fator <= float(cap_max) + 1e-6, (
                f"{macro}: fator {fator} > cap_maximo {cap_max}"
            )


@settings(max_examples=200, deadline=None)
@given(terrain=terrain_strategy, cluster=clusters)
def test_gating_deterministic(terrain, cluster):
    """P4 — Mesmos inputs sempre geram mesmo resultado de bloqueio."""
    r1 = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    r2 = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    assert r1["viabilidade_bloqueada"] == r2["viabilidade_bloqueada"]
    assert r1["score_fisico"] == r2["score_fisico"]


@settings(max_examples=200, deadline=None)
@given(terrain=terrain_strategy, cluster=clusters)
def test_fator_area_util_bounds(terrain, cluster):
    """P5 — fator_area_util sempre em [0.0, 1.0]."""
    report = ENGINE.evaluate(terrain_metrics=terrain, cluster_regional=cluster, raise_on_block=False)
    assert 0.0 <= report["fator_area_util"] <= 1.0
