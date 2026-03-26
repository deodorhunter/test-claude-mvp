# US-007: Test Coverage — Auth, RBAC, Schema — Done

## Summary

Written test suite for Phase 1 security layer: JWT, RBAC, schema constraints.
Tests require no running PostgreSQL or Plone instance. All external dependencies mocked.

## Test Files

- `backend/tests/conftest.py` — shared fixtures + env-var bootstrap for pydantic-settings
- `backend/tests/test_auth.py` — 14 tests: JWT unit tests, get_current_user dependency, plone-login endpoint
- `backend/tests/test_rbac.py` — 12 tests: permission mapping, require_permission dependency, cross-tenant isolation
- `backend/tests/test_schema.py` — 14 tests: table names, constraints, FK structure, cascade rules, audit append-only

## Coverage Details

### test_auth.py
- `create_access_token`: required claims present (sub, tenant_id, iss, type, exp)
- `create_refresh_token`: type claim is "refresh"
- `verify_token`: rejects wrong type, tampered signature, wrong issuer, expired token; accepts correct type
- `get_current_user`: valid cookie, missing cookie (401), expired token (401), garbage token (401), missing sub (401), missing tenant_id (401)
- `POST /api/v1/auth/plone-login`: success (200 + cookies), invalid token (401, no cookies), Plone unreachable/timeout (503), audit logged on failure, audit logged on success

### test_rbac.py
- `get_permissions`: Manager full perms, Member query-only, Editor/Reviewer query+mcp, unknown role empty, empty roles empty, role union, Site Administrator == Manager
- `require_permission`: Manager allowed on QUERY_EXECUTE (200), Member blocked on PLUGIN_ENABLE (403), Member blocked on PLUGIN_DISABLE (403), Member blocked on ADMIN (403), unauthenticated → 401 not 403
- Cross-tenant isolation: JWT tenant_id always wins; two separate tokens decode to independent tenant_ids

### test_schema.py
- Table name assertions for all 5 models
- UniqueConstraint and CheckConstraint names on User
- CheckConstraint text covers admin/member/guest values
- All 5 models registered in Base.metadata
- AuditLog has zero foreign keys (GDPR retention)
- AuditLog user_id and tenant_id columns are nullable
- FK targets: TenantPlugin → tenants.id, TenantTokenQuota → tenants.id, User → tenants.id
- FK ondelete=CASCADE on User and TenantPlugin
- AuditService._write contains no UPDATE/DELETE/session.update/session.delete/session.merge

## Mocking Strategy

- **Plone HTTP**: mocked with `respx` (`respx.mock` decorator on each test)
- **DB session**: `unittest.mock.AsyncMock` passed via `app.dependency_overrides[get_db]`
- **AuditService (Depends path)**: overridden via `app.dependency_overrides[get_audit_service]`
- **AuditService (direct call path in middleware)**: patched via `patch("app.audit.service._audit_service", mock_audit)` — required because `require_permission` in `middleware.py` calls `get_audit_service()` directly rather than via FastAPI Depends

## Assumptions and Notes

1. `conftest.py` sets required env vars (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `PLONE_BASE_URL`, `QDRANT_URL`) via `os.environ.setdefault` before any app module import, and clears the `lru_cache` on `get_settings`. This avoids `ValidationError` from pydantic-settings when no `.env` file is present.

2. The `create_app()` factory is called without running the lifespan context (no `asynccontextmanager` enter). This means `init_audit_service()` is never called by the app machinery in tests. The `_audit_service` module singleton is patched directly for tests that exercise code paths calling `get_audit_service()` outside of FastAPI Depends.

3. `test_plone_login_success`: the mock for `db.refresh` uses a `side_effect` function that mutates the `User` object in place (sets `id` and `tenant_id`). This mirrors what SQLAlchemy does after a real DB insert with `server_default`.

4. `asyncio_mode = "auto"` is set in `pyproject.toml` — `@pytest.mark.asyncio` decorators are present for clarity but are not strictly required.

5. `test_require_permission_blocks_insufficient_role` and similar denial tests use `raise_server_exceptions=False` on `TestClient` to prevent pytest from surfacing the 403 `HTTPException` as a test failure at the TestClient layer.

6. The cross-tenant isolation test (`test_cross_tenant_isolation_via_jwt`) documents the architectural contract: `get_current_user` reads `tenant_id` exclusively from the JWT claim. No request body or header can override it.

## Known Gaps (deferred to Phase 3 / US-029)

- No integration tests against a real PostgreSQL instance (unique constraint violations, FK cascade, check constraint enforcement at DB level)
- No E2E test for the full login → refresh → access flow
- No load/concurrency tests for quota enforcement
- Audit log immutability not tested at DB role level (requires real DB with restricted privileges)

## How to Run

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

Expected: all tests pass with no DB or Docker running.
