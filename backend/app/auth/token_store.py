"""
Refresh Token Store — Redis-backed JTI blacklist for refresh token rotation.

Security model:
- Each refresh token carries a unique JTI (UUID) claim.
- On /refresh: old JTI is checked for prior use; if already used → 401 (replay attack).
- After issuing new tokens: old JTI is written to Redis with TTL matching token expiry.
- TTL ensures Redis does not accumulate stale entries beyond the token's natural lifetime.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import redis.asyncio as aioredis

from ..config import get_settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Module-level singleton, initialized during app lifespan
_redis_client: aioredis.Redis | None = None


def init_redis(client: aioredis.Redis) -> None:
    """Called during app lifespan startup to inject the Redis client."""
    global _redis_client
    _redis_client = client


def get_redis_client() -> aioredis.Redis:
    """Return the module-level Redis client. Raises if not initialized."""
    if _redis_client is None:
        raise RuntimeError(
            "Redis client not initialized. Call init_redis() in app lifespan."
        )
    return _redis_client


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency that returns the Redis client."""
    return get_redis_client()


class RefreshTokenStore:
    """
    Redis-backed JTI blacklist for refresh token rotation.

    Each entry is stored as:
        key:   refresh:used:<jti>
        value: "1"
        TTL:   matching the remaining lifetime of the refresh token

    The TTL ensures that once a refresh token would have expired naturally,
    its JTI entry is also evicted, preventing unbounded Redis growth.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    async def mark_used(self, jti: str, ttl_seconds: int) -> None:
        """
        Mark a JTI as used (i.e. the corresponding refresh token is invalidated).

        Args:
            jti:         The JWT ID claim from the refresh token.
            ttl_seconds: Seconds until the key expires from Redis. Should match
                         the remaining lifetime of the refresh token so that
                         Redis entries are automatically cleaned up.
        """
        await self._redis.setex(f"refresh:used:{jti}", ttl_seconds, "1")
        logger.debug("Refresh JTI marked as used: %s (ttl=%ds)", jti, ttl_seconds)

    async def is_used(self, jti: str) -> bool:
        """
        Check whether a JTI has already been used (i.e. the token is revoked).

        Returns:
            True if the JTI exists in the blacklist (token is revoked / replayed).
            False if the JTI is not present (token is still valid for one use).
        """
        result = await self._redis.exists(f"refresh:used:{jti}")
        return result > 0
