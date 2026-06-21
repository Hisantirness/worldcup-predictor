"""Per-team statistical profiles built from finished matches."""

from math import exp, factorial

TEAM_PROFILES: dict[str, dict] = {}
_HAS_REAL_DATA: set[str] = set()


def _poisson_prob(k: float, lam: float) -> float:
    """P(X = k) for Poisson(lambda)."""
    return (lam ** k) * exp(-lam) / factorial(int(k))


def _poisson_cum(lam: float, threshold: float, above: bool = True) -> float:
    """P(X > threshold) or P(X <= threshold) for Poisson(lambda)."""
    total = 0.0
    if above:
        for k in range(int(threshold) + 1, 30):
            total += _poisson_prob(float(k), lam)
    else:
        for k in range(0, int(threshold) + 1):
            total += _poisson_prob(float(k), lam)
    return min(max(total, 0.0), 1.0)


def _strength(rank: int) -> float:
    return max(0.15, min(0.95, 1.0 - (rank - 1) / 60))


def build_profiles(matches: list[dict], all_matches_stats: list[dict]):
    """Build per-team profiles from finished match stats.

    matches: raw match list from collector (has score, status, teams).
    all_matches_stats: match entries that already have generated 'stats' dicts.
    """
    global _HAS_REAL_DATA
    accum: dict[str, dict] = {}

    for m, s in zip(matches, all_matches_stats):
        if m.get("status") != "finished":
            continue
        stats = s.get("stats")
        if not stats:
            continue
        home = m["home"]
        away = m["away"]
        for team, prefix in [(home, "home"), (away, "away")]:
            acc = accum.setdefault(team, {
                "games": 0,
                "corners_for": 0, "corners_against": 0,
                "yc_for": 0, "yc_against": 0,
                "shots_for": 0, "shots_against": 0,
                "sot_for": 0, "sot_against": 0,
                "fouls_for": 0, "fouls_against": 0,
                "possession": 0,
                "goals_for": 0, "goals_against": 0,
            })
            acc["games"] += 1
            acc["corners_for"] += stats["corners"][prefix]
            acc["corners_against"] += stats["corners"]["away" if prefix == "home" else "home"]
            acc["yc_for"] += stats["yellow_cards"][prefix]
            acc["yc_against"] += stats["yellow_cards"]["away" if prefix == "home" else "home"]
            acc["shots_for"] += stats["shots_total"][prefix]
            acc["shots_against"] += stats["shots_total"]["away" if prefix == "home" else "home"]
            acc["sot_for"] += stats["shots_on_target"][prefix]
            acc["sot_against"] += stats["shots_on_target"]["away" if prefix == "home" else "home"]
            acc["fouls_for"] += stats["fouls"][prefix]
            acc["fouls_against"] += stats["fouls"]["away" if prefix == "home" else "home"]
            acc["possession"] += stats["possession"][prefix]

            score = m.get("score", {})
            if prefix == "home":
                acc["goals_for"] += score.get("home", 0) if score else 0
                acc["goals_against"] += score.get("away", 0) if score else 0
            else:
                acc["goals_for"] += score.get("away", 0) if score else 0
                acc["goals_against"] += score.get("home", 0) if score else 0

    for team, acc in accum.items():
        n = acc["games"]
        TEAM_PROFILES[team] = {
            "games_played": n,
            "avg_corners_for": round(acc["corners_for"] / n, 1),
            "avg_corners_against": round(acc["corners_against"] / n, 1),
            "avg_yc_for": round(acc["yc_for"] / n, 1),
            "avg_yc_against": round(acc["yc_against"] / n, 1),
            "avg_shots_for": round(acc["shots_for"] / n, 1),
            "avg_shots_against": round(acc["shots_against"] / n, 1),
            "avg_sot_for": round(acc["sot_for"] / n, 1),
            "avg_sot_against": round(acc["sot_against"] / n, 1),
            "avg_fouls_for": round(acc["fouls_for"] / n, 1),
            "avg_fouls_against": round(acc["fouls_against"] / n, 1),
            "avg_possession": round(acc["possession"] / n, 1),
            "avg_goals_for": round(acc["goals_for"] / n, 2),
            "avg_goals_against": round(acc["goals_against"] / n, 2),
        }
        _HAS_REAL_DATA.add(team)

    for acc_data in accum.values():
        pass


def get_team_profile(team: str, rank: int = 50) -> dict:
    if team in TEAM_PROFILES:
        return TEAM_PROFILES[team]

    str_factor = _strength(rank)
    weak_factor = 1.0 - str_factor
    return {
        "games_played": 0,
        "avg_corners_for": round(3.0 + str_factor * 4, 1),
        "avg_corners_against": round(3.0 + weak_factor * 3, 1),
        "avg_yc_for": round(1.0 + weak_factor * 2, 1),
        "avg_yc_against": round(1.0 + str_factor * 2, 1),
        "avg_shots_for": round(8 + str_factor * 8, 1),
        "avg_shots_against": round(6 + weak_factor * 8, 1),
        "avg_sot_for": round(3 + str_factor * 4, 1),
        "avg_sot_against": round(2 + weak_factor * 3, 1),
        "avg_fouls_for": round(8 + weak_factor * 4, 1),
        "avg_fouls_against": round(8 + str_factor * 3, 1),
        "avg_possession": round(40 + str_factor * 20, 1),
        "avg_goals_for": round(0.5 + str_factor * 2.0, 2),
        "avg_goals_against": round(0.3 + weak_factor * 2.0, 2),
    }


def estimate_market(market: str, home_team: str, away_team: str,
                    home_rank: int, away_rank: int) -> dict:
    """Estimate probability for a given market on a match.

    Market format examples:
    - "corners_over_8.5" / "corners_under_8.5"
    - "corners_over_9.5"
    - "yc_over_4.5" / "yc_under_4.5"
    - "shots_over_20.5"
    - "sot_over_8.5"
    """
    hp = get_team_profile(home_team, home_rank)
    ap = get_team_profile(away_team, away_rank)

    parts = market.split("_")
    stat_type = parts[0]
    direction = parts[1]
    threshold = float(parts[2])

    if stat_type == "corners":
        exp_home = (hp["avg_corners_for"] + ap["avg_corners_against"]) / 2
        exp_away = (ap["avg_corners_for"] + hp["avg_corners_against"]) / 2
    elif stat_type == "yc":
        exp_home = (hp["avg_yc_for"] + ap["avg_yc_against"]) / 2
        exp_away = (ap["avg_yc_for"] + hp["avg_yc_against"]) / 2
    elif stat_type == "shots":
        exp_home = (hp["avg_shots_for"] + ap["avg_shots_against"]) / 2
        exp_away = (ap["avg_shots_for"] + hp["avg_shots_against"]) / 2
    elif stat_type == "sot":
        exp_home = (hp["avg_sot_for"] + ap["avg_sot_against"]) / 2
        exp_away = (ap["avg_sot_for"] + hp["avg_sot_against"]) / 2
    elif stat_type == "fouls":
        exp_home = (hp["avg_fouls_for"] + ap["avg_fouls_against"]) / 2
        exp_away = (ap["avg_fouls_for"] + hp["avg_fouls_against"]) / 2
    elif stat_type == "goals":
        exp_home = (hp["avg_goals_for"] + ap["avg_goals_against"]) / 2
        exp_away = (ap["avg_goals_for"] + hp["avg_goals_against"]) / 2
    else:
        return {"market": market, "probability": 50.0, "expected_value": 0.0}

    total_exp = exp_home + exp_away

    if direction == "over":
        prob = _poisson_cum(total_exp, threshold, above=True) * 100
    else:
        prob = _poisson_cum(total_exp, threshold, above=False) * 100

    prob = max(1.0, min(99.0, prob))

    fair_odds = round(100 / prob, 2) if prob > 0 else 999
    fair_implied = 100 / fair_odds if fair_odds > 0 else 0
    ev = round(prob - fair_implied, 1)

    label_map = {
        "corners": "Córners",
        "yc": "T. Amarillas",
        "shots": "Tiros",
        "sot": "Tiros al arco",
        "fouls": "Faltas",
        "goals": "Goles",
    }
    stat_label = label_map.get(stat_type, stat_type)
    dir_label = "Más de" if direction == "over" else "Menos de"
    thresh_label = str(int(threshold)) if threshold == int(threshold) else str(threshold)

    return {
        "market": market,
        "label": f"{dir_label} {thresh_label} {stat_label}",
        "direction": direction,
        "stat_type": stat_type,
        "threshold": threshold,
        "expected_total": round(total_exp, 1),
        "probability": round(prob, 1),
        "fair_odds": fair_odds,
        "expected_value": ev,
    }


def get_all_markets(home_team: str, away_team: str,
                    home_rank: int, away_rank: int) -> list[dict]:
    """Return all available markets with probabilities for a match."""
    markets = []
    thresholds = {
        "corners": [7.5, 8.5, 9.5, 10.5, 11.5],
        "yc": [3.5, 4.5, 5.5, 6.5],
        "shots": [18.5, 20.5, 22.5, 24.5],
        "sot": [6.5, 7.5, 8.5, 9.5],
        "fouls": [16.5, 18.5, 20.5, 22.5],
        "goals": [1.5, 2.5, 3.5, 4.5],
    }
    for stat_type, threshs in thresholds.items():
        for t in threshs:
            over = estimate_market(f"{stat_type}_over_{t}", home_team, away_team, home_rank, away_rank)
            under = estimate_market(f"{stat_type}_under_{t}", home_team, away_team, home_rank, away_rank)
            # Only include non-trivial markets (prob between 10% and 90%)
            if 10 <= over["probability"] <= 90:
                markets.append(over)
            if 10 <= under["probability"] <= 90:
                markets.append(under)
    return sorted(markets, key=lambda x: -x["probability"])
