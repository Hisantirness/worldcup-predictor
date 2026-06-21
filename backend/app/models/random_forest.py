import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from typing import Optional


def _generate_synthetic_data(n_samples: int = 5000):
    np.random.seed(42)
    X = []
    y = []

    for _ in range(n_samples):
        home_rank = np.random.randint(1, 100)
        away_rank = np.random.randint(1, 100)
        home_goals_scored = np.random.uniform(0.3, 3.0)
        home_goals_conceded = np.random.uniform(0.2, 2.5)
        away_goals_scored = np.random.uniform(0.3, 3.0)
        away_goals_conceded = np.random.uniform(0.2, 2.5)
        home_wins = np.random.randint(0, 6)
        away_wins = np.random.randint(0, 6)
        home_draws = np.random.randint(0, 3)
        away_draws = np.random.randint(0, 3)

        rank_diff = away_rank - home_rank
        goal_diff = (home_goals_scored - home_goals_conceded) - (away_goals_scored - away_goals_conceded)
        home_strength = home_goals_scored * 0.3 + home_wins * 0.1 + max(0, (50 - home_rank) / 50) * 0.4
        away_strength = away_goals_scored * 0.3 + away_wins * 0.1 + max(0, (50 - away_rank) / 50) * 0.4

        features = [
            home_rank, away_rank,
            home_goals_scored, home_goals_conceded,
            away_goals_scored, away_goals_conceded,
            home_wins, away_wins,
            home_draws, away_draws,
            rank_diff, goal_diff,
            home_strength, away_strength,
            home_strength - away_strength,
        ]
        X.append(features)

        strength_ratio = home_strength / (home_strength + away_strength + 0.01)
        rand = np.random.random()
        home_adj = strength_ratio * (1 - 0.22) + 0.4 * 0.22
        away_adj = (1 - strength_ratio) * (1 - 0.22) + 0.3 * 0.22
        draw_adj = 0.22

        if rand < home_adj:
            y.append(0)
        elif rand < home_adj + draw_adj:
            y.append(1)
        else:
            y.append(2)

    return np.array(X), np.array(y)


class RandomForestPredictor:
    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self._trained = False

    def train(self, X: Optional[np.ndarray] = None, y: Optional[np.ndarray] = None):
        synthetic = X is None or y is None
        if synthetic:
            X, y = _generate_synthetic_data(n_samples=2000)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        self.model = RandomForestClassifier(
            n_estimators=100 if synthetic else 200,
            max_depth=10 if synthetic else 15,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled, y)
        self._trained = True

    def _ensure_trained(self):
        if not self._trained:
            self.train()

    def _build_features(self, home_form: dict, away_form: dict, home_rank: int, away_rank: int) -> np.ndarray:
        features = [
            home_rank, away_rank,
            home_form["avg_goals_scored"], home_form["avg_goals_conceded"],
            away_form["avg_goals_scored"], away_form["avg_goals_conceded"],
            home_form["wins_last_5"], away_form["wins_last_5"],
            home_form["draws_last_5"], away_form["draws_last_5"],
            away_rank - home_rank,
            (home_form["avg_goals_scored"] - home_form["avg_goals_conceded"]) -
            (away_form["avg_goals_scored"] - away_form["avg_goals_conceded"]),
            home_form["avg_goals_scored"] * 0.3 + home_form["wins_last_5"] * 0.1 + max(0, (50 - home_rank) / 50) * 0.4,
            away_form["avg_goals_scored"] * 0.3 + away_form["wins_last_5"] * 0.1 + max(0, (50 - away_rank) / 50) * 0.4,
            (home_form["avg_goals_scored"] * 0.3 + home_form["wins_last_5"] * 0.1 + max(0, (50 - home_rank) / 50) * 0.4) -
            (away_form["avg_goals_scored"] * 0.3 + away_form["wins_last_5"] * 0.1 + max(0, (50 - away_rank) / 50) * 0.4),
        ]
        return np.array([features])

    def predict(self, home_form: dict, away_form: dict, home_rank: int, away_rank: int) -> dict:
        self._ensure_trained()
        features = self._build_features(home_form, away_form, home_rank, away_rank)
        features_scaled = self.scaler.transform(features)
        probs = self.model.predict_proba(features_scaled)[0]

        return {
            "home": round(float(probs[0]) * 100, 1),
            "draw": round(float(probs[1]) * 100, 1),
            "away": round(float(probs[2]) * 100, 1),
        }

    @property
    def is_trained(self) -> bool:
        return self._trained

    def get_feature_importance(self) -> list[dict]:
        if not self._trained or self.model is None:
            return []
        feature_names = [
            "home_rank", "away_rank",
            "home_goals_scored", "home_goals_conceded",
            "away_goals_scored", "away_goals_conceded",
            "home_wins", "away_wins",
            "home_draws", "away_draws",
            "rank_diff", "goal_diff",
            "home_strength", "away_strength",
            "strength_diff",
        ]
        importances = self.model.feature_importances_
        sorted_idx = np.argsort(importances)[::-1]
        return [
            {"feature": feature_names[i], "importance": round(float(importances[i]), 4)}
            for i in sorted_idx
        ]
