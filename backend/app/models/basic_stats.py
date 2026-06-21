class BasicStatsPredictor:
    def predict(self, home: str, away: str, home_form: dict, away_form: dict,
                home_rank: int, away_rank: int) -> dict:
        home_strength = (home_form["avg_goals_scored"] * 0.3
                         + home_form["wins_last_5"] * 0.05
                         + max(0, (50 - home_rank) / 50) * 0.4
                         + (1 - home_form["avg_goals_conceded"] / 3) * 0.25)

        away_strength = (away_form["avg_goals_scored"] * 0.3
                         + away_form["wins_last_5"] * 0.05
                         + max(0, (50 - away_rank) / 50) * 0.4
                         + (1 - away_form["avg_goals_conceded"] / 3) * 0.25)

        total = home_strength + away_strength
        if total == 0:
            return {"home": 33.3, "draw": 33.3, "away": 33.3}

        raw_home = home_strength / total
        raw_away = away_strength / total
        raw_draw = 1 - raw_home - raw_away

        draw_base = 0.20 + (home_form["draws_last_5"] + away_form["draws_last_5"]) * 0.02
        draw_prob = max(draw_base, raw_draw * 0.3)

        remaining = 1 - draw_prob
        home_prob = raw_home / (raw_home + raw_away) * remaining if (raw_home + raw_away) > 0 else 0.5
        away_prob = remaining - home_prob

        return {
            "home": round(home_prob * 100, 1),
            "draw": round(draw_prob * 100, 1),
            "away": round(away_prob * 100, 1),
        }

    def predict_btts(self, home_form: dict, away_form: dict) -> float:
        avg = (home_form["btts_percentage"] + away_form["btts_percentage"]) / 2
        return round(avg, 1)

    def predict_over_25(self, home_form: dict, away_form: dict) -> float:
        home_goals = home_form["avg_goals_scored"] + away_form["avg_goals_conceded"]
        away_goals = away_form["avg_goals_scored"] + home_form["avg_goals_conceded"]
        total_expected = home_goals + away_goals
        prob = min(95, max(20, (total_expected / 4) * 70))
        return round(prob, 1)
