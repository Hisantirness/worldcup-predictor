import pytest
from app.parlay.calculator import calculate_single_parlay, get_safest_parlays, _get_risk_level
from app.data_collector.collector import SAMPLE_MATCHES

pytestmark = pytest.mark.unit


class TestParlayCalculator:
    def test_calculate_single_parlay_returns_structure(self, sample_selections):
        result = calculate_single_parlay(sample_selections)
        assert "selections" in result
        assert "combined_probability" in result
        assert "expected_value" in result
        assert "risk_level" in result

    def test_combined_probability_less_than_individual(self, sample_selections):
        result = calculate_single_parlay(sample_selections)
        for sel in result["selections"]:
            assert result["combined_probability"] < sel["probability"]

    def test_combined_probability_decreases_with_more_picks(self, sample_selections):
        one_pick = calculate_single_parlay([sample_selections[0]])
        two_picks = calculate_single_parlay(sample_selections)
        assert two_picks["combined_probability"] < one_pick["combined_probability"]

    def test_risk_level_bajo_for_high_prob(self):
        assert _get_risk_level(60) == "Bajo"

    def test_risk_level_medio_for_medium_prob(self):
        assert _get_risk_level(40) == "Medio"

    def test_risk_level_alto_for_low_prob(self):
        assert _get_risk_level(20) == "Alto"

    def test_risk_level_muy_alto_for_very_low_prob(self):
        assert _get_risk_level(5) == "Muy Alto"

    def test_risk_level_boundary_50(self):
        assert _get_risk_level(50) == "Bajo"

    def test_risk_level_boundary_30(self):
        assert _get_risk_level(30) == "Medio"

    def test_risk_level_boundary_15(self):
        assert _get_risk_level(15) == "Alto"

    def test_get_safest_parlays_returns_list(self, sample_matches):
        results = get_safest_parlays(sample_matches, max_picks=2, min_prob=40)
        assert isinstance(results, list)
        if results:
            assert "parlay_size" in results[0]
            assert "combined_probability" in results[0]
            assert "risk" in results[0]
            assert "selections" in results[0]

    def test_get_safest_parlays_sorted_by_probability(self, sample_matches):
        results = get_safest_parlays(sample_matches, max_picks=2, min_prob=30)
        for i in range(len(results) - 1):
            assert results[i]["combined_probability"] >= results[i + 1]["combined_probability"]

    def test_get_safest_parlays_respects_min_prob(self, sample_matches):
        results = get_safest_parlays(sample_matches, max_picks=2, min_prob=90)
        assert len(results) == 0

    def test_calculate_with_single_selection(self, sample_selections):
        result = calculate_single_parlay([sample_selections[0]])
        assert len(result["selections"]) == 1

    def test_expected_value_calculation(self, sample_selections):
        result = calculate_single_parlay(sample_selections)
        assert isinstance(result["expected_value"], float)
