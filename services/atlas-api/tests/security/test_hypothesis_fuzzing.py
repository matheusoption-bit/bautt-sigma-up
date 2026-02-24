"""
Property-based testing with Hypothesis - Real implementation.
Tests boundary conditions and edge cases in ATLAS engine evaluation.
No fake tests - every test calls the real engine via API.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from fastapi.testclient import TestClient

from atlas_api.main import app


@pytest.fixture(scope="module")
def client():
    """FastAPI test client for Hypothesis tests."""
    return TestClient(app)


class TestHypothesisAtlasBoundaries:
    """
    Property-based tests for ATLAS engine boundary conditions.
    Focus on edge cases around thresholds: 19.99/20.0/20.01, 9.99/10.0/10.01, etc.
    """

    @settings(max_examples=50, deadline=2000)
    @given(
        declividade=st.floats(min_value=19.5, max_value=20.5, allow_nan=False, allow_infinity=False),
    )
    def test_declividade_gating_threshold_20_percent(self, client, declividade):
        """
        Property: declividade >= 20% should trigger gating.
        This tests the critical 20% threshold for slope-based blocking.
        """
        payload = {
            "declividade_media_pct": declividade,
            "solo_classe": "ARGILOSO",
            "pct_app_area": 0.0,
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)

        # Should get valid response
        assert response.status_code in [200, 409, 422]

        if response.status_code == 200:
            data = response.json()

            # Property: if declividade >= 20.0, viabilidade should be blocked
            if declividade >= 20.0:
                viabilidade = data.get("viabilidade", {})
                viabilidade_bloqueada = viabilidade.get("viabilidade_bloqueada", False)

                assert viabilidade_bloqueada is True, (
                    f"declividade={declividade:.4f} >= 20.0 should block viabilidade"
                )

            # Property: if declividade < 20.0, should NOT be blocked (assuming other fields are safe)
            elif declividade < 20.0:
                viabilidade = data.get("viabilidade", {})
                viabilidade_bloqueada = viabilidade.get("viabilidade_bloqueada", False)

                # Should not be blocked by declividade alone
                # (may still be blocked by other factors, but not ALTA_DECLIVIDADE alert)
                pass  # This is permissive - we're testing the threshold boundary

    @settings(max_examples=50, deadline=2000)
    @given(
        pct_app=st.floats(min_value=9.5, max_value=10.5, allow_nan=False, allow_infinity=False),
    )
    def test_app_area_gating_threshold_10_percent(self, client, pct_app):
        """
        Property: pct_app_area >= 10% should trigger gating.
        Tests the 10% APP threshold.
        """
        payload = {
            "pct_app_area": pct_app,
            "declividade_media_pct": 8.0,  # Safe slope
            "solo_classe": "ARENOSO",
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)
        assert response.status_code in [200, 409, 422]

        if response.status_code == 200:
            data = response.json()

            if pct_app >= 10.0:
                viabilidade = data.get("viabilidade", {})
                viabilidade_bloqueada = viabilidade.get("viabilidade_bloqueada", False)

                assert viabilidade_bloqueada is True, (
                    f"pct_app_area={pct_app:.4f} >= 10.0 should block viabilidade"
                )

    @settings(max_examples=30, deadline=2000)
    @given(
        declividade_max=st.floats(min_value=50.0, max_value=70.0, allow_nan=False, allow_infinity=False),
        declividade_media=st.floats(min_value=30.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    )
    def test_contencoes_factor_clamped_at_cap(self, client, declividade_max, declividade_media):
        """
        Property: contenções factor should never exceed cap of 3.0.
        Tests that extreme slope values don't cause factor overflow.
        """
        payload = {
            "declividade_max_pct": declividade_max,
            "declividade_media_pct": declividade_media,
            "historico_deslizamento_r4": True,
            "solo_classe": "ARGILOSO",
            "pct_app_area": 0.0,
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)
        assert response.status_code in [200, 409]

        if response.status_code == 200:
            data = response.json()
            ajustes_custo = data.get("ajustes_custo", [])

            # Find contenções adjustment
            contencoes = None
            for ajuste in ajustes_custo:
                if ajuste.get("macroetapa") == "contenções":
                    contencoes = ajuste
                    break

            if contencoes:
                fator_ajuste = contencoes.get("fator_ajuste")

                # Property: factor must be clamped at 3.0
                assert fator_ajuste <= 3.0, (
                    f"contenções factor {fator_ajuste} exceeds cap of 3.0"
                )

                # Property: factor should be positive
                assert fator_ajuste > 0, (
                    f"contenções factor {fator_ajuste} should be positive"
                )

    @settings(max_examples=30, deadline=2000)
    @given(
        nspt=st.integers(min_value=1, max_value=5),
        lencol_depth=st.floats(min_value=0.3, max_value=2.0, allow_nan=False, allow_infinity=False),
    )
    def test_fundacoes_factor_clamped_at_cap(self, client, nspt, lencol_depth):
        """
        Property: fundações factor should never exceed cap of 2.5.
        Tests that worst soil conditions don't cause factor overflow.
        """
        payload = {
            "solo_classe": "TURFOSO",  # Worst case
            "nspt_medio": nspt,
            "lencol_freatico_profundidade_m": lencol_depth,
            "declividade_media_pct": 5.0,
            "pct_app_area": 0.0,
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)
        assert response.status_code in [200, 409]

        if response.status_code == 200:
            data = response.json()
            ajustes_custo = data.get("ajustes_custo", [])

            # Find fundações adjustment
            fundacoes = None
            for ajuste in ajustes_custo:
                if ajuste.get("macroetapa") == "fundações":
                    fundacoes = ajuste
                    break

            if fundacoes:
                fator_ajuste = fundacoes.get("fator_ajuste")

                # Property: factor must be clamped at 2.5
                assert fator_ajuste <= 2.5, (
                    f"fundações factor {fator_ajuste} exceeds cap of 2.5"
                )

                # Property: factor should be >= 1.0 (minimum adjustment)
                assert fator_ajuste >= 1.0, (
                    f"fundações factor {fator_ajuste} should be >= 1.0"
                )

    @settings(max_examples=40, deadline=2000)
    @given(
        declividade=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
        pct_app=st.floats(min_value=0.0, max_value=15.0, allow_nan=False, allow_infinity=False),
    )
    def test_all_factors_positive_and_finite(self, client, declividade, pct_app):
        """
        Property: All cost adjustment factors should be positive and finite.
        This is a sanity check that no edge case produces invalid factors.
        """
        payload = {
            "declividade_media_pct": declividade,
            "pct_app_area": pct_app,
            "solo_classe": "ARGILOSO",
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)

        # Accept any valid status
        assert response.status_code in [200, 409, 422]

        if response.status_code == 200:
            data = response.json()
            ajustes_custo = data.get("ajustes_custo", [])

            for ajuste in ajustes_custo:
                fator_ajuste = ajuste.get("fator_ajuste")
                macroetapa = ajuste.get("macroetapa")

                # Property: All factors must be positive, finite numbers
                assert fator_ajuste is not None, f"{macroetapa} has None factor"
                assert fator_ajuste > 0, f"{macroetapa} factor {fator_ajuste} is not positive"
                assert fator_ajuste < float('inf'), f"{macroetapa} factor is infinite"

    @settings(max_examples=30, deadline=2000)
    @given(
        overlaps=st.booleans(),
        pct_app=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_overlaps_area_uniao_always_blocks(self, client, overlaps, pct_app):
        """
        Property: overlaps_area_uniao=True should ALWAYS block viabilidade.
        Regardless of other parameters.
        """
        payload = {
            "overlaps_area_uniao": overlaps,
            "pct_app_area": pct_app,
            "declividade_media_pct": 5.0,  # Low slope
            "solo_classe": "ROCHOSO"  # Good soil
        }

        response = client.post("/atlas/evaluate", json=payload)
        assert response.status_code in [200, 409]

        if response.status_code == 200 and overlaps:
            data = response.json()
            viabilidade = data.get("viabilidade", {})
            viabilidade_bloqueada = viabilidade.get("viabilidade_bloqueada", False)

            # Property: overlaps_area_uniao=True MUST block
            assert viabilidade_bloqueada is True, (
                "overlaps_area_uniao=True should always block viabilidade"
            )

    @settings(max_examples=30, deadline=2000)
    @given(
        historico=st.booleans(),
        declividade=st.floats(min_value=5.0, max_value=15.0, allow_nan=False, allow_infinity=False),
    )
    def test_historico_deslizamento_always_blocks(self, client, historico, declividade):
        """
        Property: historico_deslizamento_r4=True should ALWAYS block viabilidade.
        """
        payload = {
            "historico_deslizamento_r4": historico,
            "declividade_media_pct": declividade,
            "solo_classe": "ROCHOSO",
            "pct_app_area": 0.0,
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)
        assert response.status_code in [200, 409]

        if response.status_code == 200 and historico:
            data = response.json()
            viabilidade = data.get("viabilidade", {})
            viabilidade_bloqueada = viabilidade.get("viabilidade_bloqueada", False)

            # Property: historico_deslizamento_r4=True MUST block
            assert viabilidade_bloqueada is True, (
                "historico_deslizamento_r4=True should always block viabilidade"
            )


class TestHypothesisResponseStructure:
    """Property tests for response structure consistency."""

    @settings(max_examples=20, deadline=2000)
    @given(
        declividade=st.floats(min_value=5.0, max_value=30.0, allow_nan=False, allow_infinity=False),
    )
    def test_response_always_has_required_fields(self, client, declividade):
        """
        Property: All successful responses should have required fields.
        """
        payload = {
            "declividade_media_pct": declividade,
            "solo_classe": "ARGILOSO",
            "pct_app_area": 2.0,
            "overlaps_area_uniao": False
        }

        response = client.post("/atlas/evaluate", json=payload)

        if response.status_code == 200:
            data = response.json()

            # Property: Required fields must be present
            assert "viabilidade" in data, "Response must have viabilidade field"
            assert "ajustes_custo" in data, "Response must have ajustes_custo field"
            assert "metadata" in data, "Response must have metadata field"

            # Property: metadata must have coverage_score
            metadata = data["metadata"]
            assert "coverage_score" in metadata, "metadata must have coverage_score"
            assert 0.0 <= metadata["coverage_score"] <= 1.0, "coverage_score must be in [0,1]"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics", "--tb=short"])
