import pytest
import tempfile
import os
from app.data_collector.cache import DataCache

pytestmark = pytest.mark.unit


@pytest.fixture
def cache():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    dc = DataCache(tmp.name)
    yield dc
    dc.close()
    try:
        os.unlink(tmp.name)
    except PermissionError:
        import gc; gc.collect()
        try:
            os.unlink(tmp.name)
        except PermissionError:
            pass


class TestDataCache:
    def test_set_and_get(self, cache):
        cache.set("test_key", {"value": 42})
        result = cache.get("test_key")
        assert result == {"value": 42}

    def test_get_missing_key(self, cache):
        result = cache.get("nonexistent")
        assert result is None

    def test_overwrite_key(self, cache):
        cache.set("key", {"v1": 1})
        cache.set("key", {"v2": 2})
        result = cache.get("key")
        assert result == {"v2": 2}

    def test_ttl_expired(self, cache):
        cache.set("expires_soon", {"data": "test"}, ttl=0)
        import time
        time.sleep(0.1)
        result = cache.get("expires_soon")
        assert result is None

    def test_save_and_get_match_result(self, cache):
        cache.save_match_result("Argentina", "Brazil", 3, 1, "2026-06-21")
        h2h = cache.get_head_to_head("Argentina", "Brazil")
        assert len(h2h) == 1
        assert h2h[0]["home_score"] == 3
        assert h2h[0]["away_score"] == 1

    def test_head_to_head_both_directions(self, cache):
        cache.save_match_result("Argentina", "Brazil", 2, 0, "2026-06-21")
        h2h = cache.get_head_to_head("Brazil", "Argentina")
        assert len(h2h) == 1

    def test_team_recent_matches(self, cache):
        cache.save_match_result("Argentina", "Brazil", 1, 0, "2026-06-21")
        cache.save_match_result("Uruguay", "Argentina", 2, 2, "2026-06-25")
        matches = cache.get_team_recent_matches("Argentina")
        assert len(matches) == 2

    def test_team_recent_limit(self, cache):
        for i in range(5):
            cache.save_match_result(f"Team{i}", "Argentina", 1, 0, f"2026-06-{21+i}")
        matches = cache.get_team_recent_matches("Argentina", limit=3)
        assert len(matches) == 3

    def test_clear_expired(self, cache):
        cache.set("will_expire", {"a": 1}, ttl=0)
        cache.set("will_stay", {"b": 2}, ttl=3600)
        import time
        time.sleep(0.1)
        cache.clear_expired()
        assert cache.get("will_expire") is None
        assert cache.get("will_stay") == {"b": 2}

    def test_multiple_head_to_head_ordered(self, cache):
        cache.save_match_result("A", "B", 1, 0, "2026-06-25")
        cache.save_match_result("A", "B", 0, 2, "2026-06-21")
        results = cache.get_head_to_head("A", "B")
        assert len(results) == 2
        assert results[0]["date"] > results[1]["date"]
