import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


class TestAPIEndpoints:
    def test_get_matches_returns_200(self):
        response = client.get("/api/v1/matches")
        assert response.status_code == 200
        data = response.json()
        assert "matches" in data
        assert len(data["matches"]) > 0

    def test_get_matches_structure(self):
        response = client.get("/api/v1/matches")
        data = response.json()
        match = data["matches"][0]
        assert "home" in match
        assert "away" in match
        assert "date" in match
        assert "group" in match
        assert "home_rank" in match
        assert "away_rank" in match

    def test_get_predictions_returns_200(self):
        response = client.get("/api/v1/predictions")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0

    def test_get_predictions_structure(self):
        response = client.get("/api/v1/predictions")
        data = response.json()
        pred = data["predictions"][0]
        assert "home_team" in pred
        assert "away_team" in pred
        assert "probabilities" in pred
        assert "btts_probability" in pred
        assert "over_25_probability" in pred
        assert "safest_pick" in pred
        assert "confidence" in pred
        assert "model_details" in pred

    def test_get_predictions_probabilities_sum(self):
        response = client.get("/api/v1/predictions")
        data = response.json()
        for pred in data["predictions"]:
            probs = pred["probabilities"]
            total = probs["home"] + probs["draw"] + probs["away"]
            assert abs(total - 100.0) < 2.0

    def test_predict_specific_match_200(self):
        response = client.get("/api/v1/predictions/Argentina/Brazil")
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert data["prediction"]["home_team"] == "Argentina"
        assert data["prediction"]["away_team"] == "Brazil"

    def test_predict_with_unknown_team_returns_valid(self):
        response = client.get("/api/v1/predictions/UnknownTeam/OtherTeam")
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data

    def test_get_team_info_200(self):
        response = client.get("/api/v1/team/Argentina")
        assert response.status_code == 200
        data = response.json()
        assert data["team"] == "Argentina"
        assert "form" in data
        assert "info" in data

    def test_get_unknown_team_info(self):
        response = client.get("/api/v1/team/NonExistent")
        assert response.status_code == 200

    def test_parlay_calculate_post_200(self):
        selections = [
            {"home": "Argentina", "away": "Italy", "pick": "1", "odds": 2.10},
            {"home": "Brazil", "away": "Uruguay", "pick": "X", "odds": 3.40},
        ]
        response = client.post("/api/v1/parlay/calculate", json=selections)
        assert response.status_code == 200
        data = response.json()
        assert "combined_probability" in data
        assert "selections" in data
        assert len(data["selections"]) == 2

    def test_parlay_calculate_single_pick(self):
        selections = [
            {"home": "Argentina", "away": "Italy", "pick": "1"},
        ]
        response = client.post("/api/v1/parlay/calculate", json=selections)
        assert response.status_code == 200
        data = response.json()
        assert data["selections"][0]["pick"] == "1"

    def test_safest_parlays_returns_200(self):
        response = client.get("/api/v1/parlay/safest?max_picks=2&min_prob=40")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_safest_parlays_default_params(self):
        response = client.get("/api/v1/parlay/safest")
        assert response.status_code == 200

    def test_safest_parlays_high_threshold_returns_empty(self):
        response = client.get("/api/v1/parlay/safest?max_picks=3&min_prob=90")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) == 0

    def test_cors_headers_present(self):
        response = client.options(
            "/api/v1/matches",
            headers={"Origin": "http://localhost:5500"},
        )
        assert "access-control-allow-origin" in response.headers
