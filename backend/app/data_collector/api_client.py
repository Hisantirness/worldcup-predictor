import asyncio
import subprocess
import json
import ssl
import urllib.request
from pathlib import Path
from datetime import datetime
from functools import partial

API_BASE = "https://worldcup26.ir"
FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"

_cache_dir = Path(__file__).parent / "_data_cache"
_cache_dir.mkdir(exist_ok=True)

FOOTBALL_DATA_KEY = None


def set_api_key(key: str):
    global FOOTBALL_DATA_KEY
    FOOTBALL_DATA_KEY = key


def _cached_path(endpoint: str) -> Path:
    safe = endpoint.replace("/", "_").replace("?", "_")
    return _cache_dir / f"{safe}.json"


def _load_cache(endpoint: str) -> dict | None:
    path = _cached_path(endpoint)
    if path.exists():
        age = datetime.now().timestamp() - path.stat().st_mtime
        if age < 86400:
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _save_cache(endpoint: str, data: dict):
    _cached_path(endpoint).write_text(json.dumps(data), encoding="utf-8")


def _fetch_json_peak(url: str, headers: list[str] | None = None) -> dict | None:
    cmd = ["curl.exe", "-s", "--connect-timeout", "8", "--max-time", "15"]
    if headers:
        for h in headers:
            cmd += ["-H", h]
    cmd.append(url)
    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=False, timeout=20)
            body = result.stdout
            if len(body) > 100:
                return json.loads(body.decode("utf-8"))
        except Exception:
            pass
        import time
        time.sleep(3)
    return None


async def get_teams() -> list[dict]:
    if FOOTBALL_DATA_KEY:
        return await _get_football_data_teams()

    cached = _load_cache("teams")
    if cached and "teams" in cached:
        return cached["teams"]

    data = await asyncio.to_thread(_fetch_json_peak, f"{API_BASE}/get/teams")
    if data and "teams" in data:
        _save_cache("teams", data)
        return data["teams"]
    return []


async def get_games() -> list[dict]:
    if FOOTBALL_DATA_KEY:
        return await _get_football_data_games()

    cached = _load_cache("games")
    if cached and "games" in cached:
        return cached["games"]

    data = await asyncio.to_thread(_fetch_json_peak, f"{API_BASE}/get/games")
    if data and "games" in data:
        _save_cache("games", data)
        return data["games"]
    return []


async def get_groups() -> list[dict]:
    if FOOTBALL_DATA_KEY:
        return await _get_football_data_groups()

    cached = _load_cache("groups")
    if cached and "groups" in cached:
        return cached["groups"]

    data = await asyncio.to_thread(_fetch_json_peak, f"{API_BASE}/get/groups")
    if data and "groups" in data:
        _save_cache("groups", data)
        return data["groups"]
    return []


async def _get_football_data_teams() -> list[dict]:
    cached = _load_cache("fd_teams")
    if cached and "teams" in cached:
        return cached["teams"]

    headers = [f"X-Auth-Token: {FOOTBALL_DATA_KEY}"]
    data = await asyncio.to_thread(
        _fetch_json_peak,
        f"{FOOTBALL_DATA_BASE}/competitions/2000/teams",
        headers,
    )
    if data and "teams" in data:
        group_map = {}
        matches_data = await asyncio.to_thread(
            _fetch_json_peak,
            f"{FOOTBALL_DATA_BASE}/competitions/2000/matches",
            [f"X-Auth-Token: {FOOTBALL_DATA_KEY}"],
        )
        if matches_data and "matches" in matches_data:
            for m in matches_data["matches"]:
                grp = m.get("group", "").replace("GROUP_", "") if m.get("group") else ""
                if not grp:
                    continue
                for side in ("homeTeam", "awayTeam"):
                    tid = m.get(side, {}).get("id")
                    if tid:
                        group_map[tid] = grp
        teams = []
        for t in data["teams"]:
            tid = t.get("id")
            teams.append({
                "name_en": t.get("name") or t.get("shortName", ""),
                "flag": t.get("crest", ""),
                "fifa_code": t.get("tla", ""),
                "groups": group_map.get(tid, ""),
            })
        result = {"teams": teams}
        _save_cache("fd_teams", result)
        return teams
    return []


async def _get_football_data_games() -> list[dict]:
    cached = _load_cache("fd_games")
    if cached and "games" in cached:
        return cached["games"]

    headers = [f"X-Auth-Token: {FOOTBALL_DATA_KEY}"]
    data = await asyncio.to_thread(
        _fetch_json_peak,
        f"{FOOTBALL_DATA_BASE}/competitions/2000/matches",
        headers,
    )
    if data and "matches" in data:
        games = []
        stage_map = {
            "GROUP_STAGE": "group",
            "LAST_16": "r16",
            "QUARTER_FINALS": "qf",
            "SEMI_FINALS": "sf",
            "FINAL": "final",
            "THIRD_PLACE": "third",
            "PLAYOFF_FOR_THIRD_PLACE": "third",
            "ROUND_16": "r16",
        }
        for m in data["matches"]:
            home = m.get("homeTeam", {})
            away = m.get("awayTeam", {})
            score = m.get("score", {})
            full_time = score.get("fullTime", {}) if score else {}
            status = m.get("status", "")
            finished = status == "FINISHED"
            utc = m.get("utcDate", "")
            games.append({
                "home_team_name_en": home.get("name", ""),
                "away_team_name_en": away.get("name", ""),
                "home_score": str(full_time.get("home", "0")) if finished else "0",
                "away_score": str(full_time.get("away", "0")) if finished else "0",
                "finished": "TRUE" if finished else "FALSE",
                "local_date": utc[:10] if utc else "",
                "group": m.get("group", "").replace("GROUP_", "") if m.get("group") else "",
                "type": stage_map.get(m.get("stage", ""), m.get("stage", "group").lower()),
                "matchday": m.get("matchday"),
                "time_elapsed": "finished" if finished else "notstarted",
            })
        result = {"games": games}
        _save_cache("fd_games", result)
        return games
    return []


async def _get_football_data_groups() -> list[dict]:
    return []
