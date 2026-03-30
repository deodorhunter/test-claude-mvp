import logging
import uuid
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-backed sliding window rate limiter with tenant+user scoping."""

    def __init__(
        self,
        redis_client: Redis,
        limit: int = 10,
        window_seconds: int = 60,
    ):
        """
        Initialize the rate limiter.

        Args:
            redis_client: Async Redis client (redis.asyncio.Redis)
            limit: Max requests per window (default: 10)
            window_seconds: Window duration in seconds (default: 60)
        """
        self.redis = redis_client
        self.limit = limit
        self.window_seconds = window_seconds

    async def check_rate_limit(
        self, tenant_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Uses Redis sorted set (ZSET) with sliding window:
        - Key: rate:{tenant_id}:{user_id}
        - Members: request timestamps (score = current_time_ms)
        - Window: requests from (now - window_seconds) to now

        Returns:
            True if request is allowed, False if limit exceeded.
            On Redis failure: logs warning and returns True (fail-open).
        """
        key = f"rate:{tenant_id}:{user_id}"
        try:
            import time
            now_ms = int(time.time() * 1000)
            window_start_ms = now_ms - (self.window_seconds * 1000)

            # Atomic pipeline: remove old entries + count recent ones + add new one
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start_ms)
            pipe.zcount(key, window_start_ms, now_ms)
            pipe.zadd(key, {str(now_ms): now_ms})
            pipe.expire(key, self.window_seconds + 1)
            results = await pipe.execute()

            # results[1] = count of requests in current window (before adding this one)
            request_count_in_window = results[1]
            if request_count_in_window >= self.limit:
                logger.debug(
                    "Rate limit exceeded for tenant=%s user=%s (count=%d limit=%d)",
                    tenant_id,
                    user_id,
                    request_count_in_window,
                    self.limit,
                )
                return False

            return True

        except Exception as exc:
            # Fail-open: allow request on Redis failure for availability
            logger.warning(
                "Rate limit check failed (tenant=%s user=%s): %s. Allowing request.",
                tenant_id,
                user_id,
                exc,
            )
            return True
