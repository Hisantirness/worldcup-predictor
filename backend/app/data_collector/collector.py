import hashlib
from datetime import datetime, timedelta

from . import api_client
from ..config import API_FOOTBALL_KEY, API_FOOTBALL_URL, FOOTBALL_DATA_KEY, FOOTBALL_DATA_URL

FALLBACK_TEAMS = {
    "Argentina": {"rank": 1, "group": "A"},
    "Brazil": {"rank": 5, "group": "B"},
    "England": {"rank": 4, "group": "C"},
    "France": {"rank": 2, "group": "D"},
    "Germany": {"rank": 16, "group": "E"},
    "Spain": {"rank": 8, "group": "F"},
    "Portugal": {"rank": 6, "group": "G"},
    "Netherlands": {"rank": 7, "group": "H"},
    "Italy": {"rank": 10, "group": "A"},
    "Uruguay": {"rank": 11, "group": "B"},
    "Mexico": {"rank": 14, "group": "C"},
    "USA": {"rank": 13, "group": "D"},
    "Canada": {"rank": 40, "group": "E"},
    "Japan": {"rank": 18, "group": "F"},
    "South Korea": {"rank": 23, "group": "G"},
    "Australia": {"rank": 27, "group": "H"},
    "Senegal": {"rank": 20, "group": "A"},
    "Morocco": {"rank": 12, "group": "B"},
    "Nigeria": {"rank": 30, "group": "C"},
    "Cameroon": {"rank": 42, "group": "D"},
    "Colombia": {"rank": 15, "group": "E"},
    "Ecuador": {"rank": 28, "group": "F"},
    "Chile": {"rank": 45, "group": "G"},
    "Peru": {"rank": 35, "group": "H"},
    "Croatia": {"rank": 9, "group": "A"},
    "Denmark": {"rank": 19, "group": "B"},
    "Switzerland": {"rank": 17, "group": "C"},
    "Serbia": {"rank": 29, "group": "D"},
    "Poland": {"rank": 22, "group": "E"},
    "Austria": {"rank": 25, "group": "F"},
    "Ukraine": {"rank": 24, "group": "G"},
    "Sweden": {"rank": 21, "group": "H"},
}

SAMPLE_MATCHES = FALLBACK_MATCHES = [
    {"home": "Argentina", "away": "Italy", "date": "2026-06-21", "group": "A"},
    {"home": "Mexico", "away": "Senegal", "date": "2026-06-21", "group": "A"},
    {"home": "Brazil", "away": "Uruguay", "date": "2026-06-22", "group": "B"},
    {"home": "Morocco", "away": "Denmark", "date": "2026-06-22", "group": "B"},
    {"home": "England", "away": "USA", "date": "2026-06-22", "group": "C"},
    {"home": "Nigeria", "away": "Switzerland", "date": "2026-06-22", "group": "C"},
    {"home": "France", "away": "Cameroon", "date": "2026-06-23", "group": "D"},
    {"home": "Serbia", "away": "Germany", "date": "2026-06-23", "group": "E"},
    {"home": "Spain", "away": "Japan", "date": "2026-06-23", "group": "F"},
    {"home": "Portugal", "away": "South Korea", "date": "2026-06-24", "group": "G"},
    {"home": "Netherlands", "away": "Peru", "date": "2026-06-24", "group": "H"},
    {"home": "Ecuador", "away": "Austria", "date": "2026-06-24", "group": "F"},
    {"home": "Croatia", "away": "Argentina", "date": "2026-06-25", "group": "A"},
    {"home": "Chile", "away": "Sweden", "date": "2026-06-25", "group": "G"},
    {"home": "Poland", "away": "Colombia", "date": "2026-06-25", "group": "E"},
    {"home": "Canada", "away": "Australia", "date": "2026-06-26", "group": "H"},
]

RANK_BY_FIFA_CODE = {
    "ARG": 1, "FRA": 2, "ENG": 4, "BRA": 5, "POR": 6, "NED": 7, "ESP": 8,
    "CRO": 9, "ITA": 10, "URU": 11, "MAR": 12, "USA": 13, "MEX": 14,
    "COL": 15, "GER": 16, "SUI": 17, "JPN": 18, "DEN": 19, "SEN": 20,
    "SWE": 21, "POL": 22, "KOR": 23, "UKR": 24, "AUT": 25, "AUS": 27,
    "ECU": 28, "SRB": 29, "NGA": 30, "KSA": 31, "RSA": 32, "NOR": 33,
    "IRN": 34, "PER": 35, "ALG": 36, "TUN": 37, "EGY": 38, "CMR": 42,
    "CAN": 40, "CIV": 41, "GHA": 43, "PAR": 44, "CHI": 45, "BIH": 46,
    "PAN": 47, "CZE": 48, "IRQ": 49, "JOR": 50, "UZB": 51, "COD": 52,
    "CPV": 53, "CUW": 54, "NZL": 55, "HAI": 56, "TUR": 57, "SCO": 58,
}

WORLD_CUP_TEAMS: dict[str, dict] = {}
API_TEAMS_BY_NAME: dict[str, dict] = {}
_loaded = False


async def _ensure_loaded():
    global _loaded, WORLD_CUP_TEAMS, API_TEAMS_BY_NAME
    if _loaded:
        return
    api_teams = await api_client.get_teams()
    if api_teams:
        for t in api_teams:
            name = t["name_en"]
            code = t.get("fifa_code", "")
            API_TEAMS_BY_NAME[name] = t
            WORLD_CUP_TEAMS[name] = {
                "rank": RANK_BY_FIFA_CODE.get(code, 50),
                "group": t.get("groups", "?"),
                "flag": t.get("flag", ""),
                "fifa_code": code,
            }
        await build_finished_games_cache()
        _loaded = True
    if not WORLD_CUP_TEAMS:
        WORLD_CUP_TEAMS.update(FALLBACK_TEAMS)
        _loaded = True


async def get_all_teams() -> dict[str, dict]:
    await _ensure_loaded()
    return dict(WORLD_CUP_TEAMS)


async def get_matches() -> list[dict]:
    await _ensure_loaded()
    api_games = await api_client.get_games()
    if api_games:
        return _parse_games(api_games)
    return FALLBACK_MATCHES


def _parse_games(games: list[dict]) -> list[dict]:
    parsed = []
    for g in games:
        if g.get("type") not in ("group", "r32", "r16", "qf", "sf", "final", "third"):
            continue
        home = g.get("home_team_name_en") or ""
        away = g.get("away_team_name_en") or ""
        if not home or not away:
            continue
        local_date = g.get("local_date", "")
        finished = g.get("finished", "").upper() == "TRUE"
        entry = {
            "home": home,
            "away": away,
            "date": local_date[:10] if local_date else "",
            "group": g.get("group", "?"),
            "status": "finished" if finished else ("live" if g.get("time_elapsed", "").lower() not in ("finished", "notstarted") else "scheduled"),
            "stage": g.get("type", "group"),
            "matchday": g.get("matchday"),
        }
        if finished:
            try:
                hs = int(g.get("home_score", 0) or 0)
                aws = int(g.get("away_score", 0) or 0)
                entry["score"] = {"home": hs, "away": aws}
            except (ValueError, TypeError):
                pass
        parsed.append(entry)
    return parsed


def get_team_info(team_name: str) -> dict:
    return WORLD_CUP_TEAMS.get(team_name, {"rank": 50, "group": "Unknown"})


def get_recent_form(team: str) -> dict:
    finished = _FINISHED_GAMES_CACHE.get(team, [])
    if finished:
        total_goals_for = sum(g["home_goals"] if g["is_home"] else g["away_goals"] for g in finished)
        total_goals_against = sum(g["away_goals"] if g["is_home"] else g["home_goals"] for g in finished)
        n = len(finished)
        wins = sum(1 for g in finished if g["won"])
        draws = sum(1 for g in finished if not g["won"] and not g["lost"])
        losses = sum(1 for g in finished if g["lost"])
        btts_count = sum(1 for g in finished if g["btts"])
        over25_count = sum(1 for g in finished if g["total_goals"] > 2.5)
        return {
            "avg_goals_scored": round(total_goals_for / n, 2) if n else 1.0,
            "avg_goals_conceded": round(total_goals_against / n, 2) if n else 1.0,
            "wins_last_5": min(wins, 5),
            "draws_last_5": min(draws, 5),
            "losses_last_5": min(losses, 5),
            "btts_percentage": round(btts_count / n * 100, 1) if n else 50.0,
            "over_25_percentage": round(over25_count / n * 100, 1) if n else 50.0,
        }
    seed = _deterministic_seed(team)
    return {
        "avg_goals_scored": round(0.5 + 2.0 * ((seed * 7) % 1), 2),
        "avg_goals_conceded": round(0.3 + 1.7 * ((seed * 13) % 1), 2),
        "wins_last_5": int(1 + 4 * ((seed * 11) % 1)),
        "draws_last_5": int(2 * ((seed * 17) % 1)),
        "losses_last_5": int(3 * ((seed * 19) % 1)),
        "btts_percentage": round(30 + 40 * ((seed * 23) % 1), 1),
        "over_25_percentage": round(40 + 35 * ((seed * 29) % 1), 1),
    }


_FINISHED_GAMES_CACHE: dict[str, list[dict]] = {}


async def build_finished_games_cache():
    global _FINISHED_GAMES_CACHE
    api_games = await api_client.get_games()
    if not api_games:
        return
    by_team: dict[str, list[dict]] = {}
    for g in api_games:
        if g.get("finished", "").upper() != "TRUE":
            continue
        home = g.get("home_team_name_en", "")
        away = g.get("away_team_name_en", "")
        try:
            hs = int(g.get("home_score", 0) or 0)
            aws = int(g.get("away_score", 0) or 0)
        except (ValueError, TypeError):
            continue
        for team, is_home in [(home, True), (away, False)]:
            goals_for = hs if is_home else aws
            goals_against = aws if is_home else hs
            by_team.setdefault(team, []).append({
                "is_home": is_home,
                "home_goals": hs,
                "away_goals": aws,
                "total_goals": hs + aws,
                "won": goals_for > goals_against,
                "lost": goals_for < goals_against,
                "btts": hs > 0 and aws > 0,
            })
    _FINISHED_GAMES_CACHE = by_team


def _deterministic_seed(team: str) -> float:
    hash_bytes = hashlib.md5(team.encode()).digest()
    return int.from_bytes(hash_bytes[:4], "little") / (2**32)
