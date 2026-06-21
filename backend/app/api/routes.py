from fastapi import APIRouter, Query
from ..data_collector.collector import get_matches, get_recent_form, get_team_info, get_all_teams
from ..data_collector.stats_generator import generate_match_stats
from ..data_collector.team_stats import build_profiles, get_team_profile, get_all_markets, estimate_market
from ..data_collector.players import get_team_roster, distribute_stats
from ..models.ensemble import predict_match, get_feature_importance, get_weights, set_weights
from ..parlay.calculator import calculate_single_parlay, get_safest_parlays

router = APIRouter()
_profiles_built = False


async def _ensure_profiles():
    global _profiles_built
    if _profiles_built:
        return
    data = await get_matches()
    teams = await get_all_teams()
    enriched = []
    for i, m in enumerate(data):
        home_info = teams.get(m["home"], get_team_info(m["home"]))
        away_info = teams.get(m["away"], get_team_info(m["away"]))
        score = m.get("score")
        stats = generate_match_stats(
            home_rank=home_info["rank"],
            away_rank=away_info["rank"],
            home_score=score.get("home") if score else None,
            away_score=score.get("away") if score else None,
            seed_offset=i,
        )
        enriched.append({**m, "stats": stats})
    build_profiles(data, enriched)
    _profiles_built = True


@router.get("/matches")
async def matches():
    data = await get_matches()
    teams = await get_all_teams()
    enriched = []
    for i, m in enumerate(data):
        home_info = teams.get(m["home"], get_team_info(m["home"]))
        away_info = teams.get(m["away"], get_team_info(m["away"]))
        is_finished = m.get("status") == "finished"
        score = m.get("score")
        stats = generate_match_stats(
            home_rank=home_info["rank"],
            away_rank=away_info["rank"],
            home_score=score.get("home") if score else None,
            away_score=score.get("away") if score else None,
            seed_offset=i,
        )
        enriched.append({
            **m,
            "home_rank": home_info["rank"],
            "away_rank": away_info["rank"],
            "home_group": home_info.get("group", home_info.get("group", "?")),
            "away_group": away_info.get("group", away_info.get("group", "?")),
            "home_flag": home_info.get("flag", ""),
            "away_flag": away_info.get("flag", ""),
            "stats": stats,
        })
    return {"matches": enriched}


@router.get("/predictions")
async def predictions():
    data = await get_matches()
    results = []
    for i, m in enumerate(data):
        home_form = get_recent_form(m["home"])
        away_form = get_recent_form(m["away"])
        home_info = get_team_info(m["home"])
        away_info = get_team_info(m["away"])
        pred = predict_match(
            m["home"], m["away"],
            home_form, away_form,
            home_info["rank"], away_info["rank"],
        )
        is_finished = m.get("status") == "finished"
        score = m.get("score")
        stats = generate_match_stats(
            home_rank=home_info["rank"],
            away_rank=away_info["rank"],
            home_score=score.get("home") if score else None,
            away_score=score.get("away") if score else None,
            home_prob=pred["probabilities"]["home"],
            away_prob=pred["probabilities"]["away"],
            seed_offset=i,
        )
        results.append({
            "date": m["date"],
            "group": m["group"],
            **pred,
            "stats": stats,
        })
    return {"predictions": results}


@router.get("/predictions/{team_a}/{team_b}")
async def predict_specific(team_a: str, team_b: str):
    home_form = get_recent_form(team_a)
    away_form = get_recent_form(team_b)
    home_info = get_team_info(team_a)
    away_info = get_team_info(team_b)
    pred = predict_match(
        team_a, team_b,
        home_form, away_form,
        home_info["rank"], away_info["rank"],
    )
    return {"prediction": pred}


@router.get("/markets/{team_a}/{team_b}")
async def match_markets(team_a: str, team_b: str):
    await _ensure_profiles()
    home_info = get_team_info(team_a)
    away_info = get_team_info(team_b)
    markets = get_all_markets(team_a, team_b, home_info["rank"], away_info["rank"])
    return {
        "home_team": team_a,
        "away_team": team_b,
        "home_rank": home_info["rank"],
        "away_rank": away_info["rank"],
        "markets": markets,
    }


@router.get("/predictions/{team_a}/{team_b}/full")
async def full_match_prediction(team_a: str, team_b: str):
    """Complete match prediction with stats, markets, players, and parlay."""
    await _ensure_profiles()
    home_form = get_recent_form(team_a)
    away_form = get_recent_form(team_b)
    home_info = get_team_info(team_a)
    away_info = get_team_info(team_b)

    pred = predict_match(team_a, team_b, home_form, away_form, home_info["rank"], away_info["rank"])

    stats = generate_match_stats(
        home_rank=home_info["rank"], away_rank=away_info["rank"],
        home_prob=pred["probabilities"]["home"], away_prob=pred["probabilities"]["away"],
        seed_offset=0,
    )

    hp = get_team_profile(team_a, home_info["rank"])
    ap = get_team_profile(team_b, away_info["rank"])

    home_players = distribute_stats(
        team_a,
        total_shots=stats["shots_total"]["home"],
        total_sot=stats["shots_on_target"]["home"],
        total_fouls=stats["fouls"]["home"],
        total_yc=stats["yellow_cards"]["home"],
        total_corners=stats["corners"]["home"],
        total_offsides=stats["offsides"]["home"],
        total_saves=stats["saves"]["home"],
    )
    away_players = distribute_stats(
        team_b,
        total_shots=stats["shots_total"]["away"],
        total_sot=stats["shots_on_target"]["away"],
        total_fouls=stats["fouls"]["away"],
        total_yc=stats["yellow_cards"]["away"],
        total_corners=stats["corners"]["away"],
        total_offsides=stats["offsides"]["away"],
        total_saves=stats["saves"]["away"],
    )

    markets = get_all_markets(team_a, team_b, home_info["rank"], away_info["rank"])
    parlay_picks = [mk for mk in markets if mk["probability"] >= 60][:5]
    combined_prob = 1.0
    for p in parlay_picks:
        combined_prob *= p["probability"] / 100
    combined_prob *= 100

    return {
        "match": {
            "home_team": team_a,
            "away_team": team_b,
            "home_rank": home_info["rank"],
            "away_rank": away_info["rank"],
            "home_flag": home_info.get("flag", ""),
            "away_flag": away_info.get("flag", ""),
        },
        "prediction": pred,
        "stats": stats,
        "profiles": {"home": hp, "away": ap},
        "player_stats": {"home": home_players, "away": away_players},
        "markets": markets[:20],
        "suggested_parlay": {
            "picks": parlay_picks,
            "combined_probability": round(combined_prob, 1),
        },
    }


@router.get("/parlay/statistical")
async def statistical_parlay(
    min_prob: float = Query(65.0, ge=40, le=95),
    max_legs: int = Query(3, ge=2, le=5),
):
    """Build a statistical parlay from the safest markets across all matches."""
    await _ensure_profiles()
    data = await get_matches()
    teams = await get_all_teams()
    all_picks = []
    for i, m in enumerate(data):
        home_info = teams.get(m["home"], get_team_info(m["home"]))
        away_info = teams.get(m["away"], get_team_info(m["away"]))
        markets = get_all_markets(m["home"], m["away"], home_info["rank"], away_info["rank"])
        safe = [mk for mk in markets if mk["probability"] >= min_prob and mk["expected_value"] >= -5]
        for mk in safe:
            all_picks.append({
                "match": f"{m['home']} vs {m['away']}",
                "date": m["date"],
                "market": mk["market"],
                "label": mk.get("label", mk["market"]),
                "direction": mk["direction"],
                "stat_type": mk["stat_type"],
                "threshold": mk["threshold"],
                "probability": mk["probability"],
                "expected_total": mk["expected_total"],
                "fair_odds": mk["fair_odds"],
            })

    all_picks.sort(key=lambda x: -x["probability"])
    best = all_picks[:max_legs]

    combined_prob = 1.0
    for p in best:
        combined_prob *= p["probability"] / 100
    combined_prob *= 100

    return {
        "suggestions": best,
        "total_picks_found": len(all_picks),
        "combined_probability": round(combined_prob, 1),
    }


@router.post("/parlay/calculate")
async def parlay_calculate(selections: list[dict]):
    result = calculate_single_parlay(selections)
    return result


@router.get("/parlay/safest")
async def safest_parlays(
    max_picks: int = Query(3, ge=1, le=5),
    min_prob: float = Query(50.0, ge=10, le=90),
):
    data = await get_matches()
    suggestions = get_safest_parlays(data, max_picks=max_picks, min_prob=min_prob)
    return {"suggestions": suggestions}


@router.get("/players/{team_name}")
async def team_players(team_name: str):
    return {"team": team_name, "players": get_team_roster(team_name)}


@router.get("/team/{team_name}")
async def team_info(team_name: str):
    form = get_recent_form(team_name)
    info = get_team_info(team_name)
    await _ensure_profiles()
    profile = get_team_profile(team_name, info.get("rank", 50))
    return {"team": team_name, "form": form, "info": info, "profile": profile}


@router.get("/model/feature-importance")
async def feature_importance():
    return {"features": get_feature_importance()}


@router.get("/model/weights")
async def model_weights():
    from ..models.calibration import evaluate_on_finished_matches, calibrate_weights
    from ..data_collector.collector import get_matches
    matches = await get_matches()
    finished = [m for m in matches if m.get("status") == "finished" and m.get("score")]
    if finished:
        eval_results = evaluate_on_finished_matches(finished)
        calibrated = calibrate_weights(eval_results)
    else:
        eval_results = {}
        calibrated = {}
    return {
        "current_weights": get_weights(),
        "calibrated_weights": calibrated,
        "model_accuracy": eval_results,
    }
