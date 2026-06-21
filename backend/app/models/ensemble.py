from .basic_stats import BasicStatsPredictor
from .poisson import PoissonPredictor
from .elo import EloPredictor

basic_stats = BasicStatsPredictor()
poisson = PoissonPredictor()
elo = EloPredictor()

WEIGHTS = {
    "basic_stats": 0.30,
    "poisson": 0.40,
    "elo": 0.30,
}


def predict_match(home: str, away: str, home_form: dict, away_form: dict,
                  home_rank: int, away_rank: int) -> dict:
    bs = basic_stats.predict(home, away, home_form, away_form, home_rank, away_rank)
    ps = poisson.predict(home_form, away_form)
    el = elo.predict(home, away, home_rank, away_rank)

    home_prob = (bs["home"] * WEIGHTS["basic_stats"]
                 + ps["home"] * WEIGHTS["poisson"]
                 + el["home"] * WEIGHTS["elo"])
    draw_prob = (bs["draw"] * WEIGHTS["basic_stats"]
                 + ps["draw"] * WEIGHTS["poisson"]
                 + el["draw"] * WEIGHTS["elo"])
    away_prob = (bs["away"] * WEIGHTS["basic_stats"]
                 + ps["away"] * WEIGHTS["poisson"]
                 + el["away"] * WEIGHTS["elo"])

    total = home_prob + draw_prob + away_prob
    home_prob = home_prob / total * 100
    draw_prob = draw_prob / total * 100
    away_prob = away_prob / total * 100

    btts = (
        basic_stats.predict_btts(home_form, away_form) * WEIGHTS["basic_stats"]
        + ps["btts"] * WEIGHTS["poisson"]
        + bs.predict_btts(home_form, away_form) * WEIGHTS["elo"]
    )

    over_25 = (
        basic_stats.predict_over_25(home_form, away_form) * WEIGHTS["basic_stats"]
        + ps["over_25"] * WEIGHTS["poisson"]
        + basic_stats.predict_over_25(home_form, away_form) * WEIGHTS["elo"]
    )

    pick, confidence = _get_safest_pick(home_prob, draw_prob, away_prob)

    return {
        "home_team": home,
        "away_team": away,
        "probabilities": {
            "home": round(home_prob, 1),
            "draw": round(draw_prob, 1),
            "away": round(away_prob, 1),
        },
        "btts_probability": round(btts, 1),
        "over_25_probability": round(over_25, 1),
        "safest_pick": pick,
        "confidence": round(confidence, 1),
        "model_details": {
            "basic_stats": bs,
            "poisson": {"home": ps["home"], "draw": ps["draw"], "away": ps["away"]},
            "elo": el,
        },
    }


def _get_safest_pick(home: float, draw: float, away: float) -> tuple:
    picks = [("1", home), ("X", draw), ("2", away)]
    safest = max(picks, key=lambda x: x[1])
    return safest[0], safest[1]
