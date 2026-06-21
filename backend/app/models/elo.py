class EloPredictor:
    INITIAL_RATING = 1500
    K_FACTOR = 32

    def __init__(self):
        self.ratings = {}

    def get_rating(self, team: str, rank: int = 50) -> int:
        if team not in self.ratings:
            self.ratings[team] = self.INITIAL_RATING + (50 - rank) * 5
        return self.ratings[team]

    def predict(self, home: str, away: str, home_rank: int, away_rank: int) -> dict:
        rating_home = self.get_rating(home, home_rank)
        rating_away = self.get_rating(away, away_rank)

        home_advantage = 50
        expected_home = 1 / (1 + 10 ** ((rating_away - rating_home - home_advantage) / 400))
        expected_away = 1 / (1 + 10 ** ((rating_home + home_advantage - rating_away) / 400))

        raw_draw = 1 - expected_home - expected_away
        draw_adj = 0.22 + (abs(rating_home - rating_away) / 4000)

        draw_prob = raw_draw * (1 - draw_adj) + 0.22 * draw_adj
        remaining = 1 - draw_prob
        home_prob = expected_home / (expected_home + expected_away) * remaining
        away_prob = remaining - home_prob

        return {
            "home": round(home_prob * 100, 1),
            "draw": round(draw_prob * 100, 1),
            "away": round(away_prob * 100, 1),
        }

    def update_rating(self, team: str, opponent: str, score_home: int, score_away: int):
        is_home = True
        rating_team = self.ratings.get(team, self.INITIAL_RATING)
        rating_opp = self.ratings.get(opponent, self.INITIAL_RATING)
        expected = 1 / (1 + 10 ** ((rating_opp - rating_team - 50) / 400)) if is_home else 1 / (1 + 10 ** ((rating_opp + 50 - rating_team) / 400))

        if score_home > score_away:
            actual = 1.0
        elif score_home == score_away:
            actual = 0.5
        else:
            actual = 0.0

        self.ratings[team] = rating_team + self.K_FACTOR * (actual - expected)


elo = EloPredictor()
