import pytest
from app.models.elo import EloPredictor

pytestmark = pytest.mark.unit


class TestEloPredictor:
    def setup_method(self):
        self.predictor = EloPredictor()

    def test_initial_rating_default(self):
        rating = self.predictor.get_rating("NewTeam")
        assert rating == 1500

    def test_initial_rating_with_rank(self):
        rating = self.predictor.get_rating("TopTeam", rank=1)
        assert rating > 1500
        rating2 = self.predictor.get_rating("WeakTeam", rank=100)
        assert rating2 < rating

    def test_predict_returns_valid_structure(self):
        result = self.predictor.predict("Argentina", "Brazil", 1, 5)
        assert "home" in result
        assert "draw" in result
        assert "away" in result

    def test_probabilities_sum_to_100(self):
        result = self.predictor.predict("A", "B", 10, 10)
        total = result["home"] + result["draw"] + result["away"]
        assert abs(total - 100.0) < 1.0

    def test_home_advantage_given_to_home_team(self):
        result = self.predictor.predict("A", "B", 50, 50)
        assert result["home"] > result["away"]

    def test_strong_ranked_team_favored(self):
        result = self.predictor.predict("Strong", "Weak", 1, 100)
        assert result["home"] > result["away"]

    def test_update_rating_winner_increases(self):
        initial = self.predictor.get_rating("A", 50)
        self.predictor.update_rating("A", "B", 3, 0)
        assert self.predictor.ratings["A"] > initial

    def test_update_rating_loser_decreases(self):
        opp_initial = self.predictor.get_rating("B", 50)
        self.predictor.update_rating("A", "B", 0, 3)
        assert self.predictor.ratings["B"] < opp_initial + 50

    def test_draw_causes_small_change(self):
        rating_a = self.predictor.get_rating("A", 50)
        self.predictor.update_rating("A", "B", 1, 1)
        assert abs(self.predictor.ratings["A"] - rating_a) <= 32

    def test_get_rating_is_consistent(self):
        r1 = self.predictor.get_rating("X", 30)
        r2 = self.predictor.get_rating("X", 30)
        assert r1 == r2

    def test_predict_all_equal_teams(self):
        result = self.predictor.predict("Equal1", "Equal2", 50, 50)
        assert result["home"] > result["away"]
        assert result["draw"] >= 4
