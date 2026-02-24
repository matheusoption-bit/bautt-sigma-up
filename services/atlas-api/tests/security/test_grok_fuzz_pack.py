"""
Grok Fuzz Pack - 30 Real Attack Vectors
Data-driven test suite that validates defense mechanisms against real attack patterns.
No stubs, no fake tests - every case is verified.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from atlas_api.main import app


# Load test cases from JSON
FUZZ_PACK_PATH = Path(__file__).parent / "grok_fuzz_pack.json"
with open(FUZZ_PACK_PATH, "r", encoding="utf-8") as f:
    FUZZ_DATA = json.load(f)


def get_test_cases():
    """Extract test cases from JSON data."""
    return [(tc["id"], tc) for tc in FUZZ_DATA["test_cases"]]


class TestGrokFuzzPack:
    """
    Data-driven test suite for 30 Grok attack vectors.
    Tests are loaded from grok_fuzz_pack.json and validated against real API responses.
    """

    @pytest.fixture(scope="class")
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest.mark.parametrize("test_id,test_case", get_test_cases())
    def test_fuzz_case(self, client, test_id, test_case):
        """
        Execute each fuzz test case and validate response.

        This test:
        1. Sends the payload to /atlas/evaluate
        2. Validates HTTP status code
        3. Validates response structure and values
        4. Checks for specific alerts/blocks as expected
        """
        payload = test_case["payload"]
        expected = test_case["expected"]
        description = test_case["description"]

        # Make request to real API
        response = client.post("/atlas/evaluate", json=payload)

        # Validate status code
        expected_status = expected["status_code"]
        assert response.status_code == expected_status, (
            f"{test_id} - {description}\n"
            f"Expected status {expected_status}, got {response.status_code}\n"
            f"Response: {response.json() if response.status_code != 500 else response.text}"
        )

        # Parse response
        if response.status_code in [200, 409, 422]:
            data = response.json()
        else:
            pytest.fail(f"{test_id} - Unexpected status code: {response.status_code}")

        # Category-specific validations
        category = test_case["category"]

        if category == "insufficient_data":
            self._validate_insufficient_data(test_id, description, data, expected)
        elif category == "gating_bypass":
            self._validate_gating_bypass(test_id, description, data, expected)
        elif category == "cap_overflow":
            self._validate_cap_overflow(test_id, description, data, expected)

    def _validate_insufficient_data(self, test_id, description, data, expected):
        """Validate insufficient data test cases."""
        # For 422 responses, check that coverage warning is present
        if expected.get("has_coverage_warning"):
            # Check if response is error detail or report with metadata
            if "detail" in data:
                # Error response - may have coverage info in detail
                assert "coverage" in str(data).lower() or "campos_criticos" in str(data).lower(), (
                    f"{test_id} - Expected coverage warning in error detail"
                )
            elif "metadata" in data:
                # Report response - check metadata
                metadata = data["metadata"]
                assert "coverage_score" in metadata, (
                    f"{test_id} - Expected coverage_score in metadata"
                )

                # Validate coverage score bounds if specified
                if "min_coverage_score" in expected:
                    assert metadata["coverage_score"] >= expected["min_coverage_score"], (
                        f"{test_id} - Coverage score {metadata['coverage_score']} below minimum {expected['min_coverage_score']}"
                    )

                if "max_coverage_score" in expected:
                    assert metadata["coverage_score"] <= expected["max_coverage_score"], (
                        f"{test_id} - Coverage score {metadata['coverage_score']} above maximum {expected['max_coverage_score']}"
                    )

    def _validate_gating_bypass(self, test_id, description, data, expected):
        """Validate gating bypass test cases."""
        # Check if viabilidade should be blocked
        if "viabilidade_bloqueada" in expected:
            # Navigate the response structure to find viabilidade_bloqueada
            viabilidade_bloqueada = None

            if "viabilidade" in data:
                # Standard report structure
                viabilidade_bloqueada = data["viabilidade"].get("viabilidade_bloqueada")
            elif "viabilidade_bloqueada" in data:
                # Direct field
                viabilidade_bloqueada = data["viabilidade_bloqueada"]

            assert viabilidade_bloqueada is not None, (
                f"{test_id} - Could not find viabilidade_bloqueada in response"
            )

            assert viabilidade_bloqueada == expected["viabilidade_bloqueada"], (
                f"{test_id} - {description}\n"
                f"Expected viabilidade_bloqueada={expected['viabilidade_bloqueada']}, "
                f"got {viabilidade_bloqueada}"
            )

        # Check for specific alert codes
        if "must_have_alert_code" in expected:
            alert_code = expected["must_have_alert_code"]
            alertas = data.get("alertas", [])

            found = any(alert_code in alert.get("code", "") for alert in alertas)
            assert found, (
                f"{test_id} - Expected alert code '{alert_code}' not found.\n"
                f"Available alerts: {[a.get('code') for a in alertas]}"
            )

    def _validate_cap_overflow(self, test_id, description, data, expected):
        """Validate cap overflow test cases."""
        # Check if cost adjustments are present
        if expected.get("has_ajustes_custo"):
            assert "ajustes_custo" in data, (
                f"{test_id} - Expected ajustes_custo in response"
            )

            ajustes_custo = data["ajustes_custo"]
            assert len(ajustes_custo) > 0, (
                f"{test_id} - Expected non-empty ajustes_custo"
            )

            # Check specific macroetapa if specified
            if "macroetapa" in expected:
                macroetapa = expected["macroetapa"]

                # Find the adjustment for this macroetapa
                found_adjustment = None
                for ajuste in ajustes_custo:
                    if ajuste.get("macroetapa") == macroetapa:
                        found_adjustment = ajuste
                        break

                assert found_adjustment is not None, (
                    f"{test_id} - Expected adjustment for macroetapa '{macroetapa}' not found.\n"
                    f"Available macroetapas: {[a.get('macroetapa') for a in ajustes_custo]}"
                )

                # Validate max factor cap
                if "max_fator_ajuste" in expected:
                    max_allowed = expected["max_fator_ajuste"]
                    fator_ajuste = found_adjustment.get("fator_ajuste")

                    assert fator_ajuste is not None, (
                        f"{test_id} - fator_ajuste not found in adjustment"
                    )

                    assert fator_ajuste <= max_allowed, (
                        f"{test_id} - {description}\n"
                        f"Factor {fator_ajuste} exceeds cap {max_allowed} for {macroetapa}"
                    )


# Sanity check: Ensure all 30 tests are loaded
def test_all_30_cases_loaded():
    """Verify that all 30 test cases are loaded from JSON."""
    test_cases = FUZZ_DATA["test_cases"]
    assert len(test_cases) == 30, (
        f"Expected 30 test cases, found {len(test_cases)}"
    )

    # Verify all IDs are unique
    test_ids = [tc["id"] for tc in test_cases]
    assert len(test_ids) == len(set(test_ids)), (
        "Duplicate test IDs found"
    )

    # Verify categories
    categories = set(tc["category"] for tc in test_cases)
    expected_categories = {"insufficient_data", "gating_bypass", "cap_overflow"}
    assert categories == expected_categories, (
        f"Expected categories {expected_categories}, got {categories}"
    )

    # Verify distribution (roughly 10 per category)
    from collections import Counter
    category_counts = Counter(tc["category"] for tc in test_cases)

    assert category_counts["insufficient_data"] == 10, (
        f"Expected 10 insufficient_data tests, got {category_counts['insufficient_data']}"
    )
    assert category_counts["gating_bypass"] == 10, (
        f"Expected 10 gating_bypass tests, got {category_counts['gating_bypass']}"
    )
    assert category_counts["cap_overflow"] == 10, (
        f"Expected 10 cap_overflow tests, got {category_counts['cap_overflow']}"
    )


if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v", "--tb=short"])
