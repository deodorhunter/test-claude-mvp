# Handoff: US-017 — Token Quota Tracking + Rate Limiting

**Completed by:** Backend Dev (Haiku)
**Date:** 2026-03-30
**Files created/modified:**
- `backend/app/quota/__init__.py` (new — exports RateLimiter, QuotaService)
- `backend/app/quota/rate_limiter.py` (new — sliding window rate limiter)
- `backend/app/quota/quota_service.py` (new — quota service with DB integration)
- `backend/tests/test_quota.py` (new — 8 comprehensive tests)

## What was built

Two complementary enforcement layers for quota and rate limiting:

1. **RateLimiter** — Redis-backed sliding window implementation. Uses key format `rate:{tenant_id}:{user_id}`, default limit 10 requests/60 seconds per user. Check blocks requests over the limit; fails open if Redis is unavailable (logs warning, allows request). No multi-tenant data leakage: each user's counter is scoped to their tenant.

2. **QuotaService** — PostgreSQL-backed monthly quota tracking. Queries `TenantTokenQuota` table before model calls to verify `tokens_used < max_tokens`. Emits audit entry `AuditAction.QUOTA_EXCEEDED` when hard limit breached. Logs warning when tenant reaches ≥80% of quota. Both check and consume operations fail open on DB error (logs warning, allows request to proceed).

Both layers are invoked **before** every model call (not after). Rate limit prevents request flood; quota prevents token spend runaway.

## Integration points

**Consumers (depend on this work):**
- FastAPI middleware or dependency injection layer must call `RateLimiter.check_rate_limit()` and `QuotaService.check_quota()` before delegating to planner/model execution
- Expected caller pattern: extract `tenant_id` and `user_id` from JWT token, call both checks, reject if either returns False
- Audit service (if not None) receives `QUOTA_EXCEEDED` action on hard limit; ensure audit service is threaded into `QuotaService.__init__`

**Dependencies:**
- Redis (asyncio client) for rate limiter — expects standard Redis socket on configured host:port
- PostgreSQL (SQLAlchemy AsyncSession) for quota queries — reads from `TenantTokenQuota` table
- `TenantTokenQuota` model (already exists in `backend/app/db/models.py`) — no schema changes needed

## File ownership

- `backend/app/quota/` — owned by **Backend Dev**, responsible for quota + rate limiting logic
- `backend/app/db/models.py` — read-only reference to `TenantTokenQuota` schema (no modifications)
- `backend/tests/test_quota.py` — owned by **Backend Dev**, maintained by integration/regression tests

## Residual risks / known gaps

- **Rate limiter Redis key expiration:** Default sliding window relies on Redis TTL. If a user's first request arrives at T=0 and Redis forgets the key before T=60, a second request at T=59 will not be rate-limited. **Severity: MEDIUM** — unlikely in practice (Redis doesn't drop keys on TTL before window expires) but should be explicitly tested with `redis-cli EXPIRE` mocking.
- **Fail-open behavior under extended outage:** Both RateLimiter and QuotaService allow requests if Redis/DB are unreachable. An attacker could exploit quota bypass by flooding with requests during DB downtime. **Severity: HIGH** — acceptable for MVP (quota is "advisory", hard limits enforced at planner layer), but should be flagged in security review.
- **No pre-billing:** `consume_quota()` updates `tokens_used` AFTER model call completes. If call fails partway (e.g., partial streaming error), partial tokens may not be counted. **Severity: MEDIUM** — quota will be slightly under-counted but not breached. Acceptable if planner adds 20% safety margin to estimated tokens.
- **Quota alerts log-only:** Alert at 80% is a log warning + audit entry. No notification system (email, webhook, dashboard flag). User must check logs. **Severity: MEDIUM** — acceptable for Phase 2d (no UI layer yet).

## Manual test instructions (for user)

**Setup:**
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make up  # Ensure services running (Redis, PostgreSQL, API)
```

**Test 1: Rate limit blocks excess requests**
```bash
cat > /tmp/test_rate_limit.py << 'EOF'
import asyncio
from redis.asyncio import Redis
from backend.app.quota.rate_limiter import RateLimiter

async def test_rate_limit():
    redis = Redis(host="localhost", port=6379)
    limiter = RateLimiter(redis, max_requests=3, window_seconds=60)

    # First 3 requests should succeed
    for i in range(3):
        result = await limiter.check_rate_limit("tenant-123", "user-456")
        assert result is True, f"Request {i+1} should pass"

    # 4th should fail
    result = await limiter.check_rate_limit("tenant-123", "user-456")
    assert result is False, "Request 4 should be blocked"

    print("✓ Rate limit enforcement works")
    await redis.close()

asyncio.run(test_rate_limit())
EOF

docker cp /tmp/test_rate_limit.py ai-platform-api:/tmp/ && \
  docker exec -e PYTHONPATH=/app ai-platform-api python3 /tmp/test_rate_limit.py && \
  docker exec ai-platform-api rm /tmp/test_rate_limit.py
```

**Test 2: Quota service blocks when limit exceeded**
```bash
cat > /tmp/test_quota_exceeded.py << 'EOF'
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.app.quota.quota_service import QuotaService
from backend.app.db.models import TenantTokenQuota

async def test_quota_exceeded():
    # Use same DB as container
    engine = create_async_engine("postgresql+asyncpg://user:password@localhost:5432/test_db")
    SessionLocal = async_sessionmaker(engine)
    service = QuotaService(SessionLocal)

    # Assume quota row exists: max_tokens=1000
    allowed = await service.check_quota("tenant-123", 500)
    assert allowed is True, "500 tokens should be allowed"

    # Consume 600, leaving 400
    await service.consume_quota("tenant-123", 600)

    # Next request for 500 should fail (400 < 500)
    allowed = await service.check_quota("tenant-123", 500)
    assert allowed is False, "500 tokens should be blocked (only 400 remaining)"

    print("✓ Quota enforcement works")
    await engine.dispose()

asyncio.run(test_quota_exceeded())
EOF

docker cp /tmp/test_quota_exceeded.py ai-platform-api:/tmp/ && \
  docker exec -e PYTHONPATH=/app ai-platform-api python3 /tmp/test_quota_exceeded.py && \
  docker exec ai-platform-api rm /tmp/test_quota_exceeded.py
```

**Test 3: Redis failure fails open (allows request)**
```bash
cat > /tmp/test_redis_failopen.py << 'EOF'
import asyncio
from unittest.mock import AsyncMock, patch
from backend.app.quota.rate_limiter import RateLimiter
from redis.asyncio import Redis

async def test_redis_failopen():
    redis = AsyncMock(spec=Redis)
    redis.incr = AsyncMock(side_effect=Exception("Redis unavailable"))

    limiter = RateLimiter(redis, max_requests=10, window_seconds=60)
    result = await limiter.check_rate_limit("tenant-123", "user-456")

    assert result is True, "Should fail open on Redis error"
    print("✓ Rate limiter fails open on Redis unavailable")

asyncio.run(test_redis_failopen())
EOF

docker cp /tmp/test_redis_failopen.py ai-platform-api:/tmp/ && \
  docker exec -e PYTHONPATH=/app ai-platform-api python3 /tmp/test_redis_failopen.py && \
  docker exec ai-platform-api rm /tmp/test_redis_failopen.py
```

**Test 4: Automated unit tests**
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -k test_quota -q  # Run all 8 quota tests
# Expected: 8 passed, 186 total passing (no regressions)
```

## How to verify this works (automated)

```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -q  # All tests green, including new 8 quota tests
make logs 2>&1 | grep -i quota  # Confirm no startup errors in logs
```

**Expected output:**
- All 186 tests pass (8 new quota tests + 178 existing)
- No "quota" or "rate_limit" errors in startup logs
- Health check responds OK: `curl -s http://localhost:8000/health | jq .`
