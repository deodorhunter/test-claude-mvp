"""
Auth tests — JWT unit tests, get_current_user dependency, plone-login endpoint.

No running PostgreSQL or Plone instance required:
  - Plone HTTP calls mocked with respx
  - DB session mocked with unittest.mock.AsyncMock
  - AuditService mocked via FastAPI dependency_overrides
"""
import uuid
import pytest
import respx
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport, Response as HttpxResponse
from jose import jwt, JWTError

from app.auth.jwt import create_access_token, create_refresh_token, verify_token, ALGORITHM
from app.config import get_settings


# ──────────────────────────────────────────────────────────────────────────────
# JWT unit tests — no HTTP, no DB
# ──────────────────────────────────────────────────────────────────────────────

def test_create_access_token_contains_required_claims():
    settings = get_settings()
    token = create_access_token({"sub": "user-1", "tenant_id": "tenant-1", "roles": ["Member"]})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "user-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["iss"] == "ai-platform"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token_type_claim():
    settings = get_settings()
    token = create_refresh_token({"sub": "user-1", "tenant_id": "tenant-1"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "refresh"


def test_verify_token_rejects_wrong_type():
    """A refresh token must not be accepted as an access token."""
    refresh_token = create_refresh_token({"sub": "u", "tenant_id": "t"})
    with pytest.raises(JWTError):
        verify_token(refresh_token, token_type="access")


def test_verify_token_accepts_refresh_token_when_type_matches():
    """verify_token with token_type='refresh' must accept a valid refresh token."""
    refresh_token = create_refresh_token({"sub": "u", "tenant_id": "t"})
    payload = verify_token(refresh_token, token_type="refresh")
    assert payload["type"] == "refresh"
    assert payload["sub"] == "u"


def test_verify_token_rejects_tampered_signature():
    token = create_access_token({"sub": "u", "tenant_id": "t"})
    tampered = token[:-4] + "XXXX"
    with pytest.raises(JWTError):
        verify_token(tampered)


def test_verify_token_rejects_wrong_issuer():
    """Token issued by a different service must be rejected."""
    settings = get_settings()
    bad_token = jwt.encode(
        {
            "sub": "u",
            "iss": "attacker",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(JWTError):
        verify_token(bad_token)


def test_verify_token_rejects_expired_token():
    """An expired token must raise JWTError regardless of other claims."""
    settings = get_settings()
    expired_token = jwt.encode(
        {
            "sub": "u",
            "tenant_id": "t",
            "iss": "ai-platform",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(JWTError):
        verify_token(expired_token)


# ──────────────────────────────────────────────────────────────────────────────
# get_current_user dependency tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_current_user_with_valid_cookie():
    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": ["Member"],
        "plone_user": "alice",
    })

    from app.auth.dependencies import get_current_user
    result = await get_current_user(ai_platform_token=token)
    assert str(result.id) == user_id
    assert str(result.tenant_id) == tenant_id
    assert result.roles == ["Member"]
    assert result.plone_username == "alice"


@pytest.mark.asyncio
async def test_get_current_user_raises_401_with_no_cookie():
    from app.auth.dependencies import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(ai_platform_token=None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_with_expired_token():
    """Expired token must be rejected."""
    settings = get_settings()
    expired_token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "roles": [],
            "plone_user": "u",
            "iss": "ai-platform",
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    from app.auth.dependencies import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(ai_platform_token=expired_token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_with_garbage_token():
    from app.auth.dependencies import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(ai_platform_token="not.a.jwt")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_with_missing_sub():
    """Token with no 'sub' claim must be rejected even if sig is valid."""
    settings = get_settings()
    token_no_sub = jwt.encode(
        {
            "tenant_id": str(uuid.uuid4()),
            "roles": [],
            "plone_user": "u",
            "iss": "ai-platform",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    from app.auth.dependencies import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(ai_platform_token=token_no_sub)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_raises_401_with_missing_tenant_id():
    """Token with no 'tenant_id' claim must be rejected."""
    settings = get_settings()
    token_no_tenant = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "roles": [],
            "plone_user": "u",
            "iss": "ai-platform",
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    from app.auth.dependencies import get_current_user
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(ai_platform_token=token_no_tenant)
    assert exc_info.value.status_code == 401


# ──────────────────────────────────────────────────────────────────────────────
# plone-login endpoint tests (mocked Plone + DB)
# ──────────────────────────────────────────────────────────────────────────────

def _make_app_with_mocks(mock_db_session, mock_audit):
    """
    Create a test FastAPI app with DB and AuditService mocked.

    The lifespan is bypassed by not using it: create_app() is called and
    dependencies are overridden before the first request. We also patch
    audit.service._audit_service directly so that the non-Depends call in
    middleware.py (get_audit_service()) does not raise RuntimeError.
    """
    from app.main import create_app
    from app.db.base import get_db
    from app.audit.service import get_audit_service

    app = create_app()

    # Override DB session dependency
    async def override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    # Override audit service dependency (used by the plone-login router via Depends)
    app.dependency_overrides[get_audit_service] = lambda: mock_audit

    return app


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_success(test_tenant_id, test_user_id, mock_audit_service):
    """Valid Plone token returns httpOnly cookies and 200."""
    from sqlalchemy import select
    from app.db.models.user import User

    # Mock Plone response
    respx.get("http://localhost:8080/@users/@current").mock(
        return_value=HttpxResponse(200, json={
            "username": "alice",
            "id": "alice",
            "roles": ["Member"],
        })
    )

    # Mock DB: first query returns None (user not found), then refresh sets attrs
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # user doesn't exist yet

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    def _mock_refresh(user_obj):
        # Simulate DB assigning an id and tenant_id after insert
        user_obj.id = test_user_id
        user_obj.tenant_id = test_tenant_id

    mock_db.refresh = AsyncMock(side_effect=_mock_refresh)

    app = _make_app_with_mocks(mock_db, mock_audit_service)

    # Patch module-level _audit_service for the non-Depends call path
    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "valid-plone-token",
                "tenant_id": str(test_tenant_id),
            })

    assert resp.status_code == 200
    assert "ai_platform_token" in resp.cookies
    assert "ai_platform_refresh" in resp.cookies


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_invalid_token_returns_401(test_tenant_id, mock_audit_service):
    """Plone rejects the token → platform returns 401, no cookies set."""
    respx.get("http://localhost:8080/@users/@current").mock(
        return_value=HttpxResponse(401)
    )
    mock_db = AsyncMock()
    app = _make_app_with_mocks(mock_db, mock_audit_service)

    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "bad-token",
                "tenant_id": str(test_tenant_id),
            })

    assert resp.status_code == 401
    assert "ai_platform_token" not in resp.cookies


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_plone_unreachable_returns_503(test_tenant_id, mock_audit_service):
    """Plone connection refused → platform returns 503."""
    import httpx as httpx_module
    respx.get("http://localhost:8080/@users/@current").mock(
        side_effect=httpx_module.ConnectError("Connection refused")
    )
    mock_db = AsyncMock()
    app = _make_app_with_mocks(mock_db, mock_audit_service)

    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "any-token",
                "tenant_id": str(test_tenant_id),
            })

    assert resp.status_code == 503


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_plone_timeout_returns_503(test_tenant_id, mock_audit_service):
    """Plone timeout → platform returns 503 (TimeoutException branch)."""
    import httpx as httpx_module
    respx.get("http://localhost:8080/@users/@current").mock(
        side_effect=httpx_module.TimeoutException("Timed out")
    )
    mock_db = AsyncMock()
    app = _make_app_with_mocks(mock_db, mock_audit_service)

    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "any-token",
                "tenant_id": str(test_tenant_id),
            })

    assert resp.status_code == 503


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_audit_logged_on_failure(test_tenant_id, mock_audit_service):
    """Login failure must trigger an audit log entry with action 'login_failure'."""
    respx.get("http://localhost:8080/@users/@current").mock(
        return_value=HttpxResponse(401)
    )
    mock_db = AsyncMock()
    app = _make_app_with_mocks(mock_db, mock_audit_service)

    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "bad",
                "tenant_id": str(test_tenant_id),
            })

    mock_audit_service.log.assert_called()
    # Verify the action argument contains "login_failure"
    call_args = mock_audit_service.log.call_args
    first_positional_or_keyword = (
        call_args.args[0] if call_args.args else call_args.kwargs.get("action", "")
    )
    assert "login_failure" in str(first_positional_or_keyword)


@pytest.mark.asyncio
@respx.mock
async def test_plone_login_audit_logged_on_success(test_tenant_id, test_user_id, mock_audit_service):
    """Successful login must trigger an audit log entry with action 'login_success'."""
    respx.get("http://localhost:8080/@users/@current").mock(
        return_value=HttpxResponse(200, json={
            "username": "bob",
            "id": "bob",
            "roles": ["Manager"],
        })
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    def _mock_refresh(user_obj):
        user_obj.id = test_user_id
        user_obj.tenant_id = test_tenant_id

    mock_db.refresh = AsyncMock(side_effect=_mock_refresh)

    app = _make_app_with_mocks(mock_db, mock_audit_service)

    with patch("app.audit.service._audit_service", mock_audit_service):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/v1/auth/plone-login", json={
                "plone_token": "valid-token",
                "tenant_id": str(test_tenant_id),
            })

    assert resp.status_code == 200
    mock_audit_service.log.assert_called()
    # At least one call should be login_success
    all_calls_str = str(mock_audit_service.log.call_args_list)
    assert "login_success" in all_calls_str
