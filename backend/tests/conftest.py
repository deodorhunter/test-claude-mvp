import os
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock

# ---------------------------------------------------------------------------
# Patch settings BEFORE any app module is imported so that pydantic-settings
# does not fail trying to read missing env vars.
# ---------------------------------------------------------------------------

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("PLONE_BASE_URL", "http://localhost:8080")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")

# Clear the lru_cache so the patched env vars are picked up if any earlier
# import already cached a Settings instance.
from app.config import get_settings  # noqa: E402
get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_tenant_id():
    return uuid.uuid4()


@pytest.fixture
def test_user_id():
    return uuid.uuid4()


@pytest.fixture
def other_tenant_id():
    """A different tenant — for cross-tenant isolation tests."""
    return uuid.uuid4()


@pytest.fixture
def mock_audit_service():
    """Mock AuditService so tests don't need a DB for audit writes."""
    service = MagicMock()
    service.log = AsyncMock()
    return service
