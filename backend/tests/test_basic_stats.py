import pytest
from app.models.basic_stats import BasicStatsPredictor

pytestmark = pytest.mark.unit


class TestBasicStatsPredictor:
    def setup_method(self):
        self.predictor = BasicStatsPredictor()

    def test_predict_returns_valid_probabilities(self, home_form, away_form):
        result = self.predictor.predict(
            "Argentina", "Brazil",
            home_form, away_form,
            1, 5,
        )
        assert "home" in result
        assert "draw" in result
        assert "away" in result
        total = result["home"] + result["draw"] + result["away"]
        assert abs(total - 100.0) < 1.0
        assert all(0 <= v <= 100 for v in result.values())

    def test_strong_home_beats_weak_away(self, home_form, away_form):
        result = self.predictor.predict(
            "Argentina", "San Marino",
            home_form, away_form,
            1, 200,
        )
        assert result["home"] > result["away"]

    def test_weak_home_loses_to_strong_away(self, weak_home, strong_away):
        result = self.predictor.predict(
            "San Marino", "Brazil",
            weak_home, strong_away,
            200, 5,
        )
        assert result["away"] > result["home"]

    def test_equal_teams_give_reasonable_draw(self):
        equal_form = {
            "avg_goals_scored": 1.5,
            "avg_goals_conceded": 1.0,
            "wins_last_5": 2,
            "draws_last_5": 1,
            "losses_last_5": 2,
            "btts_percentage": 50.0,
            "over_25_percentage": 50.0,
        }
        result = self.predictor.predict(
            "TeamA", "TeamB",
            equal_form, equal_form,
            30, 30,
        )
        assert abs(result["home"] - result["away"]) < 15

    def test_predict_btts_returns_average(self, home_form, away_form):
        result = self.predictor.predict_btts(home_form, away_form)
        expected = (45.0 + 55.0) / 2
        assert result == expected

    def test_predict_over_25_returns_reasonable_value(self, home_form, away_form):
        result = self.predictor.predict_over_25(home_form, away_form)
        assert 20 <= result <= 95

    def test_draw_probability_increases_with_draws(self, home_form, away_form):
        home_form["draws_last_5"] = 5
        away_form["draws_last_5"] = 4
        result_high = self.predictor.predict(
            "A", "B", home_form, away_form, 10, 10,
        )
        home_form["draws_last_5"] = 0
        away_form["draws_last_5"] = 0
        result_low = self.predictor.predict(
            "A", "B", home_form, away_form, 10, 10,
        )
        assert result_high["draw"] > result_low["draw"]

    def test_zero_strength_returns_equal_probs(self):
        zero_form = {
            "avg_goals_scored": 0,
            "avg_goals_conceded": 0,
            "wins_last_5": 0,
            "draws_last_5": 0,
            "losses_last_5": 5,
            "btts_percentage": 0,
            "over_25_percentage": 0,
        }
        result = self.predictor.predict(
            "A", "B", zero_form, zero_form, 0, 0,
        )
        assert abs(result["home"] - result["away"]) < 5
