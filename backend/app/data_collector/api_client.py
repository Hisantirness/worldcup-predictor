import httpx
import ssl
from datetime import datetime
from pathlib import Path

API_BASE = "https://worldcup26.ir"

_cache_dir = Path(__file__).parent.parent / ".api_cache"
_cache_dir.mkdir(exist_ok=True)

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


async def _fetch_json(endpoint: str) -> dict | None:
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=20.0, verify=_ssl_ctx) as client:
                resp = await client.get(f"{API_BASE}/{endpoint}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            if attempt == 1:
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
