import math


class PoissonPredictor:
    def predict(self, home_form: dict, away_form: dict) -> dict:
        lambda_home = 0.5 * (home_form["avg_goals_scored"] + away_form["avg_goals_conceded"])
        lambda_away = 0.5 * (away_form["avg_goals_scored"] + home_form["avg_goals_conceded"])

        lambda_home = max(0.3, min(lambda_home, 3.5))
        lambda_away = max(0.2, min(lambda_away, 3.0))

        max_goals = 6
        grid = [[0.0] * (max_goals + 1) for _ in range(max_goals + 1)]

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                grid[i][j] = self._poisson(i, lambda_home) * self._poisson(j, lambda_away)

        home_prob = 0.0
        draw_prob = 0.0
        away_prob = 0.0
        over_25_prob = 0.0

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = grid[i][j]
                if i > j:
                    home_prob += p
                elif i == j:
                    draw_prob += p
                else:
                    away_prob += p
                if i + j > 2:
                    over_25_prob += p

        total = home_prob + draw_prob + away_prob
        if total > 0:
            home_prob = home_prob / total * 100
            draw_prob = draw_prob / total * 100
            away_prob = away_prob / total * 100

        btts_prob = 0.0
        for i in range(1, max_goals + 1):
            for j in range(1, max_goals + 1):
                btts_prob += grid[i][j]
        btts_prob *= 100

        return {
            "home": round(home_prob, 1),
            "draw": round(draw_prob, 1),
            "away": round(away_prob, 1),
            "over_25": round(over_25_prob * 100, 1),
            "btts": round(btts_prob, 1),
        }

    @staticmethod
    def _poisson(k: int, lam: float) -> float:
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return (lam ** k) * math.exp(-lam) / math.factorial(k)
