import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.quota import RateLimiter, QuotaService
from app.audit.service import AuditAction


class TestRateLimiter:
    """Unit tests for RateLimiter."""

    @pytest.mark.asyncio
    async def test_rate_limit_allowed_under_limit(self):
        """Test that requests under the limit are allowed."""
        mock_redis = MagicMock()
        pipeline_mock = MagicMock()
        pipeline_mock.execute = AsyncMock()
        pipeline_mock.zremrangebyscore = MagicMock(return_value=pipeline_mock)
        pipeline_mock.zcount = MagicMock(return_value=pipeline_mock)
        pipeline_mock.zadd = MagicMock(return_value=pipeline_mock)
        pipeline_mock.expire = MagicMock(return_value=pipeline_mock)
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # Pipeline returns: [removed_count, count_in_window, add_result, expire_result]
        mock_redis.pipeline.return_value.execute.return_value = [0, 5, 1, True]

        rate_limiter = RateLimiter(mock_redis, limit=10, window_seconds=60)
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await rate_limiter.check_rate_limit(tenant_id, user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_blocked_at_limit(self):
        """Test that requests at the limit are blocked."""
        mock_redis = MagicMock()
        pipeline_mock = MagicMock()
        pipeline_mock.execute = AsyncMock()
        pipeline_mock.zremrangebyscore = MagicMock(return_value=pipeline_mock)
        pipeline_mock.zcount = MagicMock(return_value=pipeline_mock)
        pipeline_mock.zadd = MagicMock(return_value=pipeline_mock)
        pipeline_mock.expire = MagicMock(return_value=pipeline_mock)
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        # count_in_window = 10 (equals limit), so this request is blocked
        mock_redis.pipeline.return_value.execute.return_value = [0, 10, 1, True]

        rate_limiter = RateLimiter(mock_redis, limit=10, window_seconds=60)
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await rate_limiter.check_rate_limit(tenant_id, user_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_redis_failure_fail_open(self):
        """Test that Redis failures result in fail-open (request allowed)."""
        mock_redis = MagicMock()
        mock_redis.pipeline.side_effect = Exception("Redis connection failed")

        rate_limiter = RateLimiter(mock_redis, limit=10, window_seconds=60)
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()

        result = await rate_limiter.check_rate_limit(tenant_id, user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_available(self):
        """Test quota check returns True when quota is available."""
        from app.db.models.tenant import TenantTokenQuota

        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        factory = MagicMock()
        factory.return_value = mock_session

        mock_quota = MagicMock(spec=TenantTokenQuota)
        mock_quota.tenant_id = uuid.uuid4()
        mock_quota.tokens_used = 100
        mock_quota.max_tokens = 1000

        mock_execute = AsyncMock()
        mock_execute.scalar_one_or_none.return_value = mock_quota
        mock_session.execute.return_value = mock_execute

        quota_service = QuotaService(factory)
        result = await quota_service.check_quota(mock_quota.tenant_id, tokens_estimated=50)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_no_quota_row_unlimited(self):
        """Test that no quota row means unlimited quota."""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        factory = MagicMock()
        factory.return_value = mock_session

        mock_execute = AsyncMock()
        mock_execute.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_execute

        quota_service = QuotaService(factory)
        tenant_id = uuid.uuid4()

        result = await quota_service.check_quota(tenant_id, tokens_estimated=999999)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_quota_service_handles_errors_gracefully(self):
        """Test that errors in check_quota are caught and fail-open."""
        factory = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__.side_effect = Exception("DB error")
        factory.return_value = mock_session

        quota_service = QuotaService(factory)
        tenant_id = uuid.uuid4()

        result = await quota_service.check_quota(tenant_id, tokens_estimated=100)

        # Should fail open
        assert result is True

    @pytest.mark.asyncio
    async def test_consume_quota_no_quota_row_silently_returns(self):
        """Test that consume_quota silently returns if no quota row."""
        mock_session = AsyncMock()
        mock_session.__aenter__.return_value = mock_session
        mock_session.__aexit__.return_value = None

        factory = MagicMock()
        factory.return_value = mock_session

        mock_execute = AsyncMock()
        mock_execute.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_execute

        quota_service = QuotaService(factory)
        tenant_id = uuid.uuid4()

        # Should not raise
        await quota_service.consume_quota(tenant_id, tokens_used=100)

        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_consume_quota_handles_errors_gracefully(self):
        """Test that errors in consume_quota don't raise."""
        factory = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__.side_effect = Exception("DB error")
        factory.return_value = mock_session

        quota_service = QuotaService(factory)
        tenant_id = uuid.uuid4()

        # Should not raise
        await quota_service.consume_quota(tenant_id, tokens_used=100)
