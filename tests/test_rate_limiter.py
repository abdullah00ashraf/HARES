from unittest.mock import MagicMock
import pytest
import redis
from hares.services.rate_limiter import RedisTokenBucketRateLimiter


class MockRedis:
    """In-memory mock of Redis key-value operations for testing rate limiting."""

    def __init__(self):
        self._store: dict[str, int] = {}
        self._ttls: dict[str, int] = {}

    def incr(self, key: str) -> int:
        val = self._store.get(key, 0) + 1
        self._store[key] = val
        return val

    def expire(self, key: str, seconds: int) -> bool:
        self._ttls[key] = seconds
        return True

    def ttl(self, key: str) -> int:
        return self._ttls.get(key, 3600)

    def delete(self, key: str) -> int:
        deleted = 1 if key in self._store else 0
        self._store.pop(key, None)
        self._ttls.pop(key, None)
        return deleted


def test_rate_limiter_allow_under_threshold():
    """Verifies that queries within the limit (<=5/hour) are permitted."""
    mock_redis = MockRedis()
    limiter = RedisTokenBucketRateLimiter(redis_client=mock_redis)
    citizen_hash = "test_user_hash_12345"

    for i in range(1, 6):
        res = limiter.check_and_increment(citizen_hash)
        assert res.is_allowed is True
        assert res.current_count == i
        assert res.max_allowed == 5


def test_rate_limiter_reject_over_threshold():
    """Verifies that the 6th query is throttled."""
    mock_redis = MockRedis()
    limiter = RedisTokenBucketRateLimiter(redis_client=mock_redis)
    citizen_hash = "test_user_hash_12345"

    for _ in range(5):
        limiter.check_and_increment(citizen_hash)

    # 6th query exceeds the limit
    blocked_res = limiter.check_and_increment(citizen_hash)
    assert blocked_res.is_allowed is False
    assert blocked_res.current_count == 6


def test_rate_limiter_reset():
    """Verifies that resetting a user clears the count."""
    mock_redis = MockRedis()
    limiter = RedisTokenBucketRateLimiter(redis_client=mock_redis)
    citizen_hash = "test_user_hash_12345"

    for _ in range(5):
        limiter.check_and_increment(citizen_hash)

    limiter.reset_limit(citizen_hash)
    fresh_res = limiter.check_and_increment(citizen_hash)
    assert fresh_res.is_allowed is True
    assert fresh_res.current_count == 1


def test_rate_limiter_redis_error_fallback():
    """Verifies fail-open behavior if Redis throws an exception."""
    mock_redis = MagicMock()
    mock_redis.incr.side_effect = redis.RedisError("Connection reset")

    limiter = RedisTokenBucketRateLimiter(redis_client=mock_redis)
    res = limiter.check_and_increment("hash_error_case")

    assert res.is_allowed is True
    assert res.current_count == 1
