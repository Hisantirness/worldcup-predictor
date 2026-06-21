from ..models.ensemble import predict_match, basic_stats
from ..data_collector.collector import get_recent_form, get_team_info


def calculate_single_parlay(selections: list[dict]) -> dict:
    combined_prob = 100.0
    total_expected_value = 0.0
    details = []

    for sel in selections:
        home = sel.get("home")
        away = sel.get("away")
        pick = sel.get("pick")
        odds = sel.get("odds")

        home_form = get_recent_form(home)
        away_form = get_recent_form(away)
        home_info = get_team_info(home)
        away_info = get_team_info(away)

        prediction = predict_match(
            home, away,
            home_form, away_form,
            home_info["rank"], away_info["rank"]
        )

        pick_mapping = {"1": "home", "X": "draw", "2": "away"}
        prob_key = pick_mapping.get(pick, "home")
        selection_prob = prediction["probabilities"][prob_key] / 100

        fair_odds = 1 / selection_prob if selection_prob > 0 else 1000

        combined_prob *= selection_prob
        if odds:
            total_expected_value += (odds / fair_odds - 1)

        details.append({
            "match": f"{home} vs {away}",
            "pick": pick,
            "probability": round(selection_prob * 100, 1),
            "fair_odds": round(fair_odds, 2),
            "provided_odds": odds,
        })

    return {
        "selections": details,
        "combined_probability": round(combined_prob * 100, 2),
        "expected_value": round(total_expected_value / len(selections) * 100, 1) if details else 0,
        "risk_level": _get_risk_level(combined_prob * 100),
    }


def get_safest_parlays(matches: list[dict], max_picks: int = 3, min_prob: float = 50.0) -> list[dict]:
    predictions = []
    for m in matches:
        home_form = get_recent_form(m["home"])
        away_form = get_recent_form(m["away"])
        home_info = get_team_info(m["home"])
        away_info = get_team_info(m["away"])

        pred = predict_match(
            m["home"], m["away"],
            home_form, away_form,
            home_info["rank"], away_info["rank"]
        )
        predictions.append(pred)

    safe_picks = []
    for p in predictions:
        pick = p["safest_pick"]
        prob_key = {"1": "home", "X": "draw", "2": "away"}[pick]
        prob = p["probabilities"][prob_key]

        if prob >= min_prob:
            safe_picks.append({
                "match": f"{p['home_team']} vs {p['away_team']}",
                "pick": pick,
                "probability": prob,
                "prediction": p,
            })

    safe_picks.sort(key=lambda x: x["probability"], reverse=True)

    suggestions = []
    for n in range(1, min(max_picks, len(safe_picks)) + 1):
        import itertools
        for combo in itertools.combinations(safe_picks[:max_picks + 2], n):
            combined_prob = 1.0
            for pick in combo:
                combined_prob *= pick["probability"] / 100

            suggestions.append({
                "parlay_size": n,
                "selections": [s["match"] + " → " + {"1": "Local", "X": "Empate", "2": "Visitante"}[s["pick"]] for s in combo],
                "combined_probability": round(combined_prob * 100, 2),
                "risk": _get_risk_level(combined_prob * 100),
            })

    suggestions.sort(key=lambda x: x["combined_probability"], reverse=True)
    return suggestions[:10]


def _get_risk_level(probability: float) -> str:
    if probability >= 50:
        return "Bajo"
    elif probability >= 30:
        return "Medio"
    elif probability >= 15:
        return "Alto"
    return "Muy Alto"
