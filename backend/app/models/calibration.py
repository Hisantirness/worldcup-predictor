from .basic_stats import BasicStatsPredictor
from .poisson import PoissonPredictor
from .elo import elo
from .random_forest import RandomForestPredictor

basic_stats = BasicStatsPredictor()
poisson = PoissonPredictor()
random_forest = RandomForestPredictor()

DEFAULT_WEIGHTS = {
    "basic_stats": 0.20,
    "poisson": 0.30,
    "elo": 0.25,
    "random_forest": 0.25,
}


def _actual_outcome(home_score: int, away_score: int) -> str:
    if home_score > away_score:
        return "1"
    if home_score == away_score:
        return "X"
    return "2"


def _predicted_outcome(probs: dict) -> str:
    return max([("1", probs["home"]), ("X", probs["draw"]), ("2", probs["away"])], key=lambda x: x[1])[0]


def _brier_score(probs: dict, actual: str) -> float:
    actual_map = {"1": 0, "X": 1, "2": 2}
    idx = actual_map[actual]
    preds = [probs["home"] / 100, probs["draw"] / 100, probs["away"] / 100]
    return sum((p - (1 if i == idx else 0)) ** 2 for i, p in enumerate(preds))


def evaluate_on_finished_matches(finished_matches: list[dict]) -> dict:
    models = {
        "basic_stats": basic_stats.predict,
        "poisson": lambda h, a, hf, af, hr, ar: poisson.predict(hf, af),
        "elo": lambda h, a, hf, af, hr, ar: elo.predict(h, a, hr, ar),
        "random_forest": lambda h, a, hf, af, hr, ar: random_forest.predict(hf, af, hr, ar),
    }
    if not random_forest.is_trained:
        random_forest.train()

    results = {name: {"correct": 0, "brier": 0.0, "total": 0} for name in models}

    for m in finished_matches:
        home = m.get("home", "")
        away = m.get("away", "")
        score = m.get("score", {})
        hs = score.get("home") if isinstance(score, dict) else None
        aws = score.get("away") if isinstance(score, dict) else None
        if not home or not away or hs is None or aws is None:
            continue
        actual = _actual_outcome(hs, aws)

        from ..data_collector.collector import get_recent_form, get_team_info
        hf = get_recent_form(home)
        af = get_recent_form(away)
        hi = get_team_info(home)
        ai = get_team_info(away)

        for name, pred_fn in models.items():
            probs = pred_fn(home, away, hf, af, hi["rank"], ai["rank"])
            pred = _predicted_outcome(probs)
            brier = _brier_score(probs, actual)
            results[name]["total"] += 1
            if pred == actual:
                results[name]["correct"] += 1
            results[name]["brier"] += brier

    for name in results:
        t = results[name]["total"]
        if t > 0:
            results[name]["accuracy"] = round(results[name]["correct"] / t * 100, 1)
            results[name]["avg_brier"] = round(results[name]["brier"] / t, 4)
        else:
            results[name]["accuracy"] = 0.0
            results[name]["avg_brier"] = 1.0

    return results


def calibrate_weights(evaluation: dict) -> dict:
    weights = {}
    total_inv_brier = 0
    inv_brier_map = {}
    for name, data in evaluation.items():
        ib = 1.0 / max(data["avg_brier"], 0.01)
        inv_brier_map[name] = ib
        total_inv_brier += ib

    if total_inv_brier > 0:
        for name in evaluation:
            weights[name] = round(inv_brier_map[name] / total_inv_brier, 4)
    else:
        weights = dict(DEFAULT_WEIGHTS)

    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        weights = {k: round(v / total, 4) for k, v in weights.items()}

    return weights
