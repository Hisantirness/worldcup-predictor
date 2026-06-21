import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class DataCache:
    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data_cache.db")
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                ttl_seconds INTEGER DEFAULT 3600
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS matches_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                tournament TEXT DEFAULT 'WC2026',
                played_at TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_teams
            ON matches_history(home_team, away_team)
        """)
        self._conn.commit()

    def get(self, key: str) -> dict | None:
        row = self._conn.execute(
            "SELECT data, created_at, ttl_seconds FROM cache WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return None
        data_json, created_at_str, ttl = row
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - created_at > timedelta(seconds=ttl):
            self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            self._conn.commit()
            return None
        return json.loads(data_json)

    def set(self, key: str, data: dict, ttl: int = 3600):
        self._conn.execute(
            "INSERT OR REPLACE INTO cache (key, data, created_at, ttl_seconds) VALUES (?, ?, ?, ?)",
            (key, json.dumps(data), _now_str(), ttl),
        )
        self._conn.commit()

    def clear_expired(self):
        now = _now_str()
        self._conn.execute(
            "DELETE FROM cache WHERE datetime(created_at, '+' || CAST(ttl_seconds AS TEXT) || ' seconds') < datetime(?)",
            (now,),
        )
        self._conn.commit()

    def save_match_result(self, home: str, away: str, home_score: int, away_score: int, played_at: str | None = None):
        self._conn.execute(
            "INSERT INTO matches_history (home_team, away_team, home_score, away_score, played_at) VALUES (?, ?, ?, ?, ?)",
            (home, away, home_score, away_score, played_at or _now_str()[:10]),
        )
        self._conn.commit()

    def get_head_to_head(self, team_a: str, team_b: str) -> list[dict]:
        rows = self._conn.execute(
            """SELECT home_team, away_team, home_score, away_score, played_at
               FROM matches_history
               WHERE (home_team = ? AND away_team = ?) OR (home_team = ? AND away_team = ?)
               ORDER BY played_at DESC""",
            (team_a, team_b, team_b, team_a),
        ).fetchall()
        return [
            {"home": r[0], "away": r[1], "home_score": r[2], "away_score": r[3], "date": r[4]}
            for r in rows
        ]

    def get_team_recent_matches(self, team: str, limit: int = 10) -> list[dict]:
        rows = self._conn.execute(
            """SELECT home_team, away_team, home_score, away_score, played_at
               FROM matches_history
               WHERE home_team = ? OR away_team = ?
               ORDER BY played_at DESC LIMIT ?""",
            (team, team, limit),
        ).fetchall()
        return [
            {"home": r[0], "away": r[1], "home_score": r[2], "away_score": r[3], "date": r[4]}
            for r in rows
        ]

    def close(self):
        self._conn.close()
