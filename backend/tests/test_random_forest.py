import pytest
import numpy as np
from app.models.random_forest import RandomForestPredictor

pytestmark = pytest.mark.unit


class TestRandomForestPredictor:
    def setup_method(self):
        self.predictor = RandomForestPredictor()

    def test_initial_not_trained(self):
        assert not self.predictor.is_trained

    def test_train_with_default_data(self):
        self.predictor.train()
        assert self.predictor.is_trained
        assert self.predictor.model is not None
        assert self.predictor.scaler is not None

    def test_predict_returns_valid_structure(self, home_form, away_form):
        self.predictor.train()
        result = self.predictor.predict(home_form, away_form, 10, 20)
        assert "home" in result
        assert "draw" in result
        assert "away" in result

    def test_probabilities_sum_to_100(self, home_form, away_form):
        self.predictor.train()
        result = self.predictor.predict(home_form, away_form, 10, 20)
        total = result["home"] + result["draw"] + result["away"]
        assert abs(total - 100.0) < 1.0

    def test_strong_home_beats_weak_away(self, home_form, away_form):
        self.predictor.train()
        result = self.predictor.predict(home_form, away_form, 1, 100)
        assert result["home"] >= result["away"]

    def test_weak_home_loses_to_strong_away(self, weak_home, strong_away):
        self.predictor.train()
        result = self.predictor.predict(weak_home, strong_away, 100, 1)
        assert result["away"] >= result["home"]

    def test_get_feature_importance_returns_list(self):
        self.predictor.train()
        importance = self.predictor.get_feature_importance()
        assert len(importance) > 0
        assert "feature" in importance[0]
        assert "importance" in importance[0]

    def test_feature_importance_sorted(self):
        self.predictor.train()
        importance = self.predictor.get_feature_importance()
        values = [item["importance"] for item in importance]
        assert all(values[i] >= values[i + 1] for i in range(len(values) - 1))

    def test_auto_train_on_first_predict(self, home_form, away_form):
        assert not self.predictor.is_trained
        result = self.predictor.predict(home_form, away_form, 10, 10)
        assert self.predictor.is_trained
        assert "home" in result

    def test_deterministic_predictions(self, home_form, away_form):
        self.predictor.train()
        result1 = self.predictor.predict(home_form, away_form, 15, 15)
        result2 = self.predictor.predict(home_form, away_form, 15, 15)
        assert result1 == result2

    def test_custom_training_data(self):
        n = 100
        X = np.random.rand(n, 15)
        y = np.random.randint(0, 3, n)
        self.predictor.train(X, y)
        assert self.predictor.is_trained

    def test_predict_all_outcomes_possible(self, home_form, away_form):
        self.predictor.train()
        weak = {
            "avg_goals_scored": 0.1,
            "avg_goals_conceded": 4.0,
            "wins_last_5": 0,
            "draws_last_5": 0,
            "losses_last_5": 5,
            "btts_percentage": 10,
            "over_25_percentage": 30,
        }
        result = self.predictor.predict(weak, home_form, 200, 1)
        assert 0 < result["home"] < 100
        assert 0 < result["draw"] < 100
        assert 0 < result["away"] < 100
