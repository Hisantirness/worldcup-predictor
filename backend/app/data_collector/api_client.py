import httpx
from datetime import datetime
from pathlib import Path

API_BASE = "https://worldcup26.ir"

_cache_dir = Path(__file__).parent.parent / ".api_cache"
_cache_dir.mkdir(exist_ok=True)


async def _fetch_json(endpoint: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{API_BASE}/{endpoint}")
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        return None
    return None


async def get_teams() -> list[dict]:
    data = await _fetch_json("get/teams")
    if data and "teams" in data:
        return data["teams"]
    return []


async def get_games() -> list[dict]:
    data = await _fetch_json("get/games")
    if data and "games" in data:
        return data["games"]
    return []


async def get_groups() -> list[dict]:
    data = await _fetch_json("get/groups")
    if data and "groups" in data:
        return data["groups"]
    return []
