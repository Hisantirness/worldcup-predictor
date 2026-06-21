import httpx
from datetime import datetime, timedelta
from ..config import API_FOOTBALL_KEY, API_FOOTBALL_URL, FOOTBALL_DATA_KEY, FOOTBALL_DATA_URL

WORLD_CUP_TEAMS = {
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

RECENT_MATCHES = {}

SAMPLE_MATCHES = [
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


async def fetch_from_api_football(endpoint: str, params: dict | None = None):
    if not API_FOOTBALL_KEY:
        return None
    async with httpx.AsyncClient() as client:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        resp = await client.get(f"{API_FOOTBALL_URL}/{endpoint}", headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json()
    return None


async def fetch_from_football_data(endpoint: str):
    if not FOOTBALL_DATA_KEY:
        return None
    async with httpx.AsyncClient() as client:
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        resp = await client.get(f"{FOOTBALL_DATA_URL}/{endpoint}", headers=headers)
        if resp.status_code == 200:
            return resp.json()
    return None


async def get_matches():
    data = await fetch_from_football_data("competitions/WC/matches")
    if data and "matches" in data:
        return _parse_football_data_matches(data["matches"])
    return SAMPLE_MATCHES


def _parse_football_data_matches(matches: list) -> list:
    parsed = []
    for m in matches:
        parsed.append({
            "home": m.get("homeTeam", {}).get("name", "TBD"),
            "away": m.get("awayTeam", {}).get("name", "TBD"),
            "date": m.get("utcDate", "")[:10],
            "group": m.get("group", "Unknown"),
            "status": m.get("status", "SCHEDULED"),
            "score": {
                "home": m.get("score", {}).get("fullTime", {}).get("home"),
                "away": m.get("score", {}).get("fullTime", {}).get("away"),
            },
        })
    return parsed


def get_team_info(team_name: str) -> dict:
    return WORLD_CUP_TEAMS.get(team_name, {"rank": 50, "group": "Unknown"})


def get_recent_form(team: str) -> dict:
    return {
        "avg_goals_scored": round(_random_between(0.5, 2.5), 2),
        "avg_goals_conceded": round(_random_between(0.3, 2.0), 2),
        "wins_last_5": _random_int(1, 4),
        "draws_last_5": _random_int(0, 2),
        "losses_last_5": _random_int(0, 3),
        "btts_percentage": round(_random_between(30, 70), 1),
        "over_25_percentage": round(_random_between(40, 75), 1),
    }


def _random_between(a: float, b: float) -> float:
    import random
    return a + (b - a) * random.random()


def _random_int(a: int, b: int) -> int:
    import random
    return random.randint(a, b)
