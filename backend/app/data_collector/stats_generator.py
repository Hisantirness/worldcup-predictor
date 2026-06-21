import hashlib
import random
from math import sqrt


def _seed(team_a: str, team_b: str) -> float:
    h = hashlib.md5(f"{team_a}:{team_b}".encode()).digest()
    return int.from_bytes(h[:4], "little") / (2 ** 32)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _strength(rank: int) -> float:
    return _clamp(1.0 - (rank - 1) / 60, 0.15, 0.95)


def generate_match_stats(
    home_rank: int,
    away_rank: int,
    home_score: int | None = None,
    away_score: int | None = None,
    home_prob: float | None = None,
    away_prob: float | None = None,
    seed_offset: int = 0,
) -> dict:
    s = _seed(str(home_rank), str(away_rank)) + seed_offset * 0.1
    rng = random.Random(s)

    h_str = _strength(home_rank)
    a_str = _strength(away_rank)
    total_str = h_str + a_str
    h_pct = h_str / total_str
    a_pct = a_str / total_str

    total_goals = 0
    if home_score is not None and away_score is not None:
        total_goals = home_score + away_score

    goal_factor = 1.0 + total_goals * 0.15

    pos_h = _clamp(50 + (h_pct - 0.5) * 30 + rng.uniform(-3, 3), 35, 70)
    pos_a = 100 - pos_h

    base_shots_h = 10 + h_str * 6
    base_shots_a = 8 + (1 - a_str) * 4
    shots_h = int(_clamp(base_shots_h * goal_factor + rng.uniform(-3, 3), 4, 30))
    shots_a = int(_clamp(base_shots_a * goal_factor + rng.uniform(-3, 3), 3, 25))

    sot_pct_h = 0.30 + h_pct * 0.15 + rng.uniform(-0.05, 0.05)
    sot_pct_a = 0.28 + (1 - a_pct) * 0.10 + rng.uniform(-0.05, 0.05)
    sot_h = int(_clamp(shots_h * sot_pct_h, 1, 15))
    sot_a = int(_clamp(shots_a * sot_pct_a, 1, 12))

    base_fouls = 10 + (1 - max(h_str, a_str)) * 6
    foul_h = int(_clamp(base_fouls * (1 - h_pct * 0.4) + rng.uniform(-2, 2), 4, 22))
    foul_a = int(_clamp(base_fouls * (1 - a_pct * 0.4) + rng.uniform(-2, 2), 4, 22))

    yc_h = int(_clamp(foul_h * (0.12 + rng.uniform(-0.03, 0.03)), 0, 6))
    yc_a = int(_clamp(foul_a * (0.12 + rng.uniform(-0.03, 0.03)), 0, 6))
    rc_h = 1 if rng.random() < 0.04 else 0
    rc_a = 1 if rng.random() < 0.06 else 0

    corners_h = int(_clamp(shots_h * (0.25 + h_pct * 0.1) + rng.uniform(-1, 1), 1, 12))
    corners_a = int(_clamp(shots_a * (0.20 + (1 - a_pct) * 0.1) + rng.uniform(-1, 1), 0, 10))

    offside_h = int(_clamp(2 + (1 - h_str) * 3 + rng.uniform(-1, 1), 0, 8))
    offside_a = int(_clamp(2 + (1 - a_str) * 3 + rng.uniform(-1, 1), 0, 8))

    saves_h = int(_clamp(sot_a * (0.4 + rng.uniform(-0.1, 0.1)), 0, 10))
    saves_a = int(_clamp(sot_h * (0.4 + rng.uniform(-0.1, 0.1)), 0, 10))

    return {
        "possession": {"home": round(pos_h, 1), "away": round(pos_a, 1)},
        "shots_total": {"home": shots_h, "away": shots_a},
        "shots_on_target": {"home": sot_h, "away": sot_a},
        "shots_off_target": {"home": shots_h - sot_h, "away": shots_a - sot_a},
        "fouls": {"home": foul_h, "away": foul_a},
        "yellow_cards": {"home": yc_h, "away": yc_a},
        "red_cards": {"home": rc_h, "away": rc_a},
        "corners": {"home": corners_h, "away": corners_a},
        "offsides": {"home": offside_h, "away": offside_a},
        "saves": {"home": saves_h, "away": saves_a},
    }
