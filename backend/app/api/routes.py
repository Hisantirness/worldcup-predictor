from fastapi import APIRouter, Query
from ..data_collector.collector import get_matches, get_recent_form, get_team_info, get_all_teams
from ..models.ensemble import predict_match, get_feature_importance
from ..parlay.calculator import calculate_single_parlay, get_safest_parlays

router = APIRouter()


@router.get("/matches")
async def matches():
    data = await get_matches()
    teams = await get_all_teams()
    enriched = []
    for m in data:
        home_info = teams.get(m["home"], get_team_info(m["home"]))
        away_info = teams.get(m["away"], get_team_info(m["away"]))
        enriched.append({
            **m,
            "home_rank": home_info["rank"],
            "away_rank": away_info["rank"],
            "home_group": home_info.get("group", home_info.get("group", "?")),
            "away_group": away_info.get("group", away_info.get("group", "?")),
            "home_flag": home_info.get("flag", ""),
            "away_flag": away_info.get("flag", ""),
        })
    return {"matches": enriched}


@router.get("/predictions")
async def predictions():
    data = await get_matches()
    results = []
    for m in data:
        home_form = get_recent_form(m["home"])
        away_form = get_recent_form(m["away"])
        home_info = get_team_info(m["home"])
        away_info = get_team_info(m["away"])
        pred = predict_match(
            m["home"], m["away"],
            home_form, away_form,
            home_info["rank"], away_info["rank"],
        )
        results.append({
            "date": m["date"],
            "group": m["group"],
            **pred,
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


@router.get("/team/{team_name}")
async def team_info(team_name: str):
    form = get_recent_form(team_name)
    info = get_team_info(team_name)
    return {"team": team_name, "form": form, "info": info}


@router.get("/model/feature-importance")
async def feature_importance():
    return {"features": get_feature_importance()}
