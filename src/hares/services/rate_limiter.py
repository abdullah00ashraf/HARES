import logging
from dataclasses import dataclass
import redis
from hares.core.config import get_settings

logger = logging.getLogger("hares.services.rate_limiter")


@dataclass
class RateLimitResult:
    is_allowed: bool
    current_count: int
    max_allowed: int
    reset_seconds: int


class RedisTokenBucketRateLimiter:
    """
    Atomic Token-Bucket / Sliding Window Rate Limiter (NFR-1.3).
    Limits queries per citizen hash (default: 5 queries / 3600 seconds)
    to defend against adversarial oracle probing and template optimization.
    """

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        settings = get_settings()
        self._max_queries = settings.RATE_LIMIT_QUERIES_PER_HOUR
        self._window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
        if redis_client is not None:
            self._redis = redis_client
        else:
            self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    _LUA_RATE_LIMIT_SCRIPT = """
    local current = redis.call('INCR', KEYS[1])
    if current == 1 then
        redis.call('EXPIRE', KEYS[1], ARGV[1])
    end
    local ttl = redis.call('TTL', KEYS[1])
    return {current, ttl}
    """

    def check_and_increment(self, citizen_user_hash: str) -> RateLimitResult:
        """
        Atomically increments the submission count for the given citizen hash
        via a single Lua script evaluation (AUDIT-OBS-07) and returns rate limit evaluation.
        """
        key = f"rl:citizen:{citizen_user_hash.strip().lower()}"
        try:
            # Atomic single-roundtrip evaluation via Lua script
            try:
                res = self._redis.eval(self._LUA_RATE_LIMIT_SCRIPT, 1, key, self._window_seconds)
                if isinstance(res, (list, tuple)) and len(res) >= 2:
                    count = int(res[0])
                    ttl = int(res[1])
                else:
                    count = int(res)
                    ttl = self._window_seconds
            except (redis.ResponseError, AttributeError):
                # Graceful fallback for mock Redis clients lacking Lua engine
                count = self._redis.incr(key)
                if count == 1:
                    self._redis.expire(key, self._window_seconds)
                ttl = self._redis.ttl(key)

            reset_seconds = ttl if ttl > 0 else self._window_seconds
            is_allowed = count <= self._max_queries

            return RateLimitResult(
                is_allowed=is_allowed,
                current_count=count,
                max_allowed=self._max_queries,
                reset_seconds=reset_seconds,
            )
        except redis.RedisError as exc:
            logger.error("Redis connection error during rate limiting check: %s", str(exc), exc_info=True)
            # Fail open for emergency citizen triage if Redis is down, but log warning
            return RateLimitResult(
                is_allowed=True,
                current_count=1,
                max_allowed=self._max_queries,
                reset_seconds=self._window_seconds,
            )

    def reset_limit(self, citizen_user_hash: str) -> None:
        """Clears rate limit key for testing or administrative resets."""
        key = f"rl:citizen:{citizen_user_hash.strip().lower()}"
        try:
            self._redis.delete(key)
        except redis.RedisError as exc:
            logger.error("Failed to delete rate limit key: %s", str(exc))
