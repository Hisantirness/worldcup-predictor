import pytest
from app.models.poisson import PoissonPredictor

pytestmark = pytest.mark.unit


class TestPoissonPredictor:
    def setup_method(self):
        self.predictor = PoissonPredictor()

    def test_predict_returns_valid_structure(self, home_form, away_form):
        result = self.predictor.predict(home_form, away_form)
        assert "home" in result
        assert "draw" in result
        assert "away" in result
        assert "over_25" in result
        assert "btts" in result

    def test_probabilities_sum_to_100(self, home_form, away_form):
        result = self.predictor.predict(home_form, away_form)
        total = result["home"] + result["draw"] + result["away"]
        assert abs(total - 100.0) < 1.0

    def test_strong_home_favored(self, home_form, away_form):
        home_form["avg_goals_scored"] = 3.0
        home_form["avg_goals_conceded"] = 0.2
        result = self.predictor.predict(home_form, away_form)
        assert result["home"] > result["draw"]
        assert result["home"] > result["away"]

    def test_strong_away_favored(self, home_form, away_form):
        away_form["avg_goals_scored"] = 3.5
        away_form["avg_goals_conceded"] = 0.1
        home_form["avg_goals_scored"] = 0.3
        home_form["avg_goals_conceded"] = 3.0
        result = self.predictor.predict(home_form, away_form)
        assert result["away"] > result["draw"]
        assert result["away"] > result["home"]

    def test_btts_probability_boundaries(self, home_form, away_form):
        result = self.predictor.predict(home_form, away_form)
        assert 0 <= result["btts"] <= 100

    def test_over_25_probability_boundaries(self, home_form, away_form):
        result = self.predictor.predict(home_form, away_form)
        assert 0 <= result["over_25"] <= 100

    def test_low_scoring_match_low_over25(self):
        low_form = {
            "avg_goals_scored": 0.3,
            "avg_goals_conceded": 0.2,
            "wins_last_5": 1, "draws_last_5": 3, "losses_last_5": 1,
            "btts_percentage": 10, "over_25_percentage": 10,
        }
        result = self.predictor.predict(low_form, low_form)
        assert result["over_25"] < 50

    def test_high_scoring_match_high_over25(self):
        high_form = {
            "avg_goals_scored": 3.0,
            "avg_goals_conceded": 2.5,
            "wins_last_5": 3, "draws_last_5": 1, "losses_last_5": 1,
            "btts_percentage": 80, "over_25_percentage": 80,
        }
        result = self.predictor.predict(high_form, high_form)
        assert result["over_25"] > 50

    def test_poisson_function_zero_lambda(self):
        prob = self.predictor._poisson(0, 0)
        assert prob == 1.0
        prob = self.predictor._poisson(1, 0)
        assert prob == 0.0

    def test_poisson_function_valid_probability(self):
        prob = self.predictor._poisson(2, 1.5)
        assert 0 < prob < 1
