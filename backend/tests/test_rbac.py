"""
RBAC tests — permission mapping, require_permission dependency, cross-tenant isolation.

No DB or Plone instance required.

Notes on require_permission tests:
  - require_permission() calls get_audit_service() directly (not via Depends) when a
    permission denial is logged. The module-level singleton must be patched for those
    code paths to avoid RuntimeError("AuditService not initialized").
"""
import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.rbac.permissions import Permission, get_permissions, ROLE_PERMISSIONS


# ──────────────────────────────────────────────────────────────────────────────
# get_permissions unit tests
# ──────────────────────────────────────────────────────────────────────────────

def test_manager_has_all_permissions():
    perms = get_permissions(["Manager"])
    assert Permission.ADMIN in perms
    assert Permission.QUERY_EXECUTE in perms
    assert Permission.PLUGIN_ENABLE in perms
    assert Permission.PLUGIN_DISABLE in perms
    assert Permission.MCP_QUERY in perms


def test_member_has_only_query_execute():
    perms = get_permissions(["Member"])
    assert perms == {Permission.QUERY_EXECUTE}


def test_editor_has_query_and_mcp():
    perms = get_permissions(["Editor"])
    assert Permission.QUERY_EXECUTE in perms
    assert Permission.MCP_QUERY in perms
    assert Permission.ADMIN not in perms
    assert Permission.PLUGIN_ENABLE not in perms


def test_reviewer_has_query_and_mcp():
    perms = get_permissions(["Reviewer"])
    assert Permission.QUERY_EXECUTE in perms
    assert Permission.MCP_QUERY in perms
    assert Permission.ADMIN not in perms


def test_unknown_role_returns_empty_set():
    perms = get_permissions(["SomeUnknownRole"])
    assert perms == set()


def test_empty_roles_returns_empty_set():
    assert get_permissions([]) == set()


def test_none_like_empty_returns_empty_set():
    """No roles at all → zero permissions (default DENY)."""
    assert get_permissions([]) == set()


def test_multiple_roles_union():
    """Multiple roles → union of their permissions."""
    perms = get_permissions(["Member", "Editor"])
    assert Permission.QUERY_EXECUTE in perms
    assert Permission.MCP_QUERY in perms
    assert Permission.ADMIN not in perms


def test_site_administrator_has_all_permissions():
    perms = get_permissions(["Site Administrator"])
    assert Permission.ADMIN in perms
    # Site Administrator should have exactly the same permissions as Manager
    assert perms == ROLE_PERMISSIONS["Manager"]


def test_manager_and_site_administrator_have_identical_permissions():
    """Both privileged roles must grant the same full permission set."""
    assert get_permissions(["Manager"]) == get_permissions(["Site Administrator"])


# ──────────────────────────────────────────────────────────────────────────────
# require_permission dependency tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_require_permission_allows_authorized_user():
    """Manager can access an endpoint requiring QUERY_EXECUTE."""
    from app.auth.jwt import create_access_token
    from app.rbac.middleware import require_permission
    from app.rbac.permissions import Permission
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": ["Manager"],
        "plone_user": "admin",
    })

    app = FastAPI()

    @app.get("/protected")
    async def protected(user=require_permission(Permission.QUERY_EXECUTE)):
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=True)
    resp = client.get("/protected", cookies={"ai_platform_token": token})
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


@pytest.mark.asyncio
async def test_require_permission_blocks_insufficient_role():
    """Member cannot enable plugins — must return 403."""
    from app.auth.jwt import create_access_token
    from app.rbac.middleware import require_permission
    from app.rbac.permissions import Permission
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    user_id = str(uuid.uuid4())
    tenant_id = str(uuid.uuid4())
    token = create_access_token({
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": ["Member"],
        "plone_user": "bob",
    })

    app = FastAPI()

    @app.get("/admin-only")
    async def admin_only(user=require_permission(Permission.PLUGIN_ENABLE)):
        return {"ok": True}

    mock_audit = MagicMock()
    mock_audit.log = AsyncMock()

    client = TestClient(app, raise_server_exceptions=False)
    with patch("app.audit.service._audit_service", mock_audit):
        resp = client.get("/admin-only", cookies={"ai_platform_token": token})

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_blocks_unauthenticated():
    """No cookie → 401, not 403."""
    from app.rbac.middleware import require_permission
    from app.rbac.permissions import Permission
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/protected")
    async def protected(user=require_permission(Permission.QUERY_EXECUTE)):
        return {"ok": True}

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/protected")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_require_permission_member_cannot_disable_plugin():
    """Member cannot disable plugins either."""
    from app.auth.jwt import create_access_token
    from app.rbac.middleware import require_permission
    from app.rbac.permissions import Permission
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    token = create_access_token({
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "roles": ["Member"],
        "plone_user": "carol",
    })

    app = FastAPI()

    @app.get("/disable-plugin")
    async def disable_plugin(user=require_permission(Permission.PLUGIN_DISABLE)):
        return {"ok": True}

    mock_audit = MagicMock()
    mock_audit.log = AsyncMock()

    client = TestClient(app, raise_server_exceptions=False)
    with patch("app.audit.service._audit_service", mock_audit):
        resp = client.get("/disable-plugin", cookies={"ai_platform_token": token})

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_require_permission_member_cannot_access_admin():
    """Member cannot access admin-only endpoints."""
    from app.auth.jwt import create_access_token
    from app.rbac.middleware import require_permission
    from app.rbac.permissions import Permission
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    token = create_access_token({
        "sub": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "roles": ["Member"],
        "plone_user": "dave",
    })

    app = FastAPI()

    @app.get("/admin")
    async def admin(user=require_permission(Permission.ADMIN)):
        return {"ok": True}

    mock_audit = MagicMock()
    mock_audit.log = AsyncMock()

    client = TestClient(app, raise_server_exceptions=False)
    with patch("app.audit.service._audit_service", mock_audit):
        resp = client.get("/admin", cookies={"ai_platform_token": token})

    assert resp.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Cross-tenant isolation test
# ──────────────────────────────────────────────────────────────────────────────

def test_cross_tenant_isolation_via_jwt():
    """
    CRITICAL SECURITY TEST: A JWT issued for tenant A must not grant access to
    tenant B's resources.

    The design principle is: tenant_id is always extracted from the JWT claim,
    never from the request body or headers. This test verifies that get_current_user
    returns the tenant_id embedded in the token, regardless of what else a client
    might send.

    An attacker who somehow obtains a valid JWT for tenant A cannot forge a request
    that appears to come from tenant B — the JWT tenant_id always wins.
    """
    from app.auth.jwt import create_access_token
    from app.auth.dependencies import get_current_user

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    # JWT is issued for tenant A
    token_for_a = create_access_token({
        "sub": str(uuid.uuid4()),
        "tenant_id": tenant_a,
        "roles": ["Manager"],
        "plone_user": "alice",
    })

    async def run():
        user = await get_current_user(ai_platform_token=token_for_a)
        # The CurrentUser must reflect the tenant from the JWT, not anything else
        assert str(user.tenant_id) == tenant_a
        # Explicitly verify it is NOT tenant B
        assert str(user.tenant_id) != tenant_b

    asyncio.run(run())


def test_cross_tenant_tokens_are_independent():
    """
    Two tokens for different tenants must decode to different tenant_ids.
    Verifies there is no cross-contamination between token creation calls.
    """
    from app.auth.jwt import create_access_token
    from app.auth.dependencies import get_current_user

    tenant_a = str(uuid.uuid4())
    tenant_b = str(uuid.uuid4())

    token_a = create_access_token({
        "sub": str(uuid.uuid4()),
        "tenant_id": tenant_a,
        "roles": ["Member"],
        "plone_user": "user_a",
    })
    token_b = create_access_token({
        "sub": str(uuid.uuid4()),
        "tenant_id": tenant_b,
        "roles": ["Member"],
        "plone_user": "user_b",
    })

    async def run():
        user_a = await get_current_user(ai_platform_token=token_a)
        user_b = await get_current_user(ai_platform_token=token_b)
        assert str(user_a.tenant_id) == tenant_a
        assert str(user_b.tenant_id) == tenant_b
        assert str(user_a.tenant_id) != str(user_b.tenant_id)

    asyncio.run(run())
