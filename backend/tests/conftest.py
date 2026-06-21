import pytest

SAMPLE_HOME_FORM = {
    "avg_goals_scored": 2.1,
    "avg_goals_conceded": 0.8,
    "wins_last_5": 4,
    "draws_last_5": 0,
    "losses_last_5": 1,
    "btts_percentage": 45.0,
    "over_25_percentage": 60.0,
}

SAMPLE_AWAY_FORM = {
    "avg_goals_scored": 1.3,
    "avg_goals_conceded": 1.5,
    "wins_last_5": 2,
    "draws_last_5": 2,
    "losses_last_5": 1,
    "btts_percentage": 55.0,
    "over_25_percentage": 50.0,
}

SAMPLE_WEAK_HOME = {
    "avg_goals_scored": 0.5,
    "avg_goals_conceded": 2.5,
    "wins_last_5": 0,
    "draws_last_5": 1,
    "losses_last_5": 4,
    "btts_percentage": 30.0,
    "over_25_percentage": 40.0,
}

SAMPLE_STRONG_AWAY = {
    "avg_goals_scored": 2.8,
    "avg_goals_conceded": 0.4,
    "wins_last_5": 5,
    "draws_last_5": 0,
    "losses_last_5": 0,
    "btts_percentage": 35.0,
    "over_25_percentage": 55.0,
}


@pytest.fixture
def home_form():
    return dict(SAMPLE_HOME_FORM)


@pytest.fixture
def away_form():
    return dict(SAMPLE_AWAY_FORM)


@pytest.fixture
def weak_home():
    return dict(SAMPLE_WEAK_HOME)


@pytest.fixture
def strong_away():
    return dict(SAMPLE_STRONG_AWAY)


@pytest.fixture
def sample_selections():
    return [
        {"home": "Argentina", "away": "Italy", "pick": "1", "odds": 2.10},
        {"home": "Brazil", "away": "Uruguay", "pick": "1", "odds": 1.80},
    ]


@pytest.fixture
def sample_matches():
    from app.data_collector.collector import SAMPLE_MATCHES
    return list(SAMPLE_MATCHES)
