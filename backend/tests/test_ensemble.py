import pytest
import math
from app.models.ensemble import predict_match, basic_stats, poisson, elo

pytestmark = pytest.mark.unit


class TestEnsemble:
    def test_predict_match_returns_all_fields(self, home_form, away_form):
        result = predict_match("Argentina", "Brazil", home_form, away_form, 1, 5)
        assert result["home_team"] == "Argentina"
        assert result["away_team"] == "Brazil"
        assert "probabilities" in result
        assert "btts_probability" in result
        assert "over_25_probability" in result
        assert "safest_pick" in result
        assert "confidence" in result
        assert "model_details" in result

    def test_probabilities_sum_to_100(self, home_form, away_form):
        result = predict_match("A", "B", home_form, away_form, 10, 10)
        probs = result["probabilities"]
        total = probs["home"] + probs["draw"] + probs["away"]
        assert abs(total - 100.0) < 1.0

    def test_model_details_contains_all_models(self, home_form, away_form):
        result = predict_match("A", "B", home_form, away_form, 10, 10)
        assert "basic_stats" in result["model_details"]
        assert "poisson" in result["model_details"]
        assert "elo" in result["model_details"]

    def test_confidence_is_strongest_probability(self, home_form, away_form):
        result = predict_match("Argentina", "Weak", home_form, away_form, 1, 100)
        probs = result["probabilities"]
        max_prob = max(probs["home"], probs["draw"], probs["away"])
        assert result["confidence"] == max_prob

    def test_safest_pick_matches_highest_prob(self, home_form, away_form):
        result = predict_match("A", "B", home_form, away_form, 10, 10)
        probs = result["probabilities"]
        pick_map = {"1": "home", "X": "draw", "2": "away"}
        picked_prob = probs[pick_map[result["safest_pick"]]]
        max_prob = max(probs["home"], probs["draw"], probs["away"])
        assert picked_prob == max_prob

    def test_strong_home_favored(self, home_form, away_form):
        result = predict_match("Strong", "Weak", home_form, away_form, 1, 100)
        assert result["probabilities"]["home"] > result["probabilities"]["away"]

    def test_btts_boundaries(self, home_form, away_form):
        result = predict_match("A", "B", home_form, away_form, 10, 10)
        assert 0 <= result["btts_probability"] <= 100

    def test_over25_boundaries(self, home_form, away_form):
        result = predict_match("A", "B", home_form, away_form, 10, 10)
        assert 0 <= result["over_25_probability"] <= 100

    def test_ensemble_is_deterministic(self, home_form, away_form):
        r1 = predict_match("A", "B", home_form, away_form, 10, 10)
        r2 = predict_match("A", "B", home_form, away_form, 10, 10)
        assert r1["probabilities"] == r2["probabilities"]

    @pytest.mark.parametrize("home_rank,away_rank,expected_favored,tolerance", [
        (1, 50, "home", 5),
        (50, 1, "away", 25),
        (10, 10, "home", 5),
    ])
    def test_ranking_affects_predictions(self, home_form, away_form, home_rank, away_rank, expected_favored, tolerance):
        result = predict_match("A", "B", home_form, away_form, home_rank, away_rank)
        if expected_favored == "home":
            assert result["probabilities"]["home"] >= result["probabilities"]["away"] - tolerance
        else:
            assert result["probabilities"]["away"] >= result["probabilities"]["home"] - tolerance
