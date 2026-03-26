# US-004: JWT Auth + Plone Bridge — Done

## Summary
Implemented JWT-based authentication with Plone identity bridge.

## Auth Flow
1. Volto authenticates user to Plone → receives Plone token
2. Volto calls `POST /api/v1/auth/plone-login` with `{plone_token, tenant_id}`
3. `PloneIdentityAdapter` calls `GET {PLONE_BASE_URL}/@users/@current` with Bearer token
4. Platform upserts User row, issues JWT access + refresh tokens as httpOnly cookies
5. All subsequent calls use `ai_platform_token` cookie

## Security Properties
- JWT signed with HS256, SECRET_KEY from env (never hardcoded)
- `tenant_id` and `user_id` NEVER read from request body — only from verified token
- Cookies: `httpOnly=True`, `SameSite=Strict`, `Secure=True` in production (controlled by ENVIRONMENT setting)
- Access token TTL: configured via ACCESS_TOKEN_EXPIRE_MINUTES (default 60 min)
- Refresh token TTL: configured via REFRESH_TOKEN_EXPIRE_DAYS (default 7 days)
- Plone unreachable → HTTP 503 (not 500 — explicit upstream error)
- Invalid Plone token → HTTP 401 with no cookie set

## Residual Risks
1. **Plone @users/@current endpoint** — behavior depends on `plone.restapi` version and whether JWT auth is enabled in Plone. If the Plone site uses classic session auth, the token format may differ. The DevOps/Infra engineer must verify the Plone restapi version after `make up`.
2. **Refresh token rotation** — current implementation issues a new refresh token on refresh but does NOT invalidate the old one (no token blocklist). A stolen refresh token remains valid until expiry. Mitigation for Phase 2: implement Redis-backed refresh token rotation/invalidation.
3. **No audit logging yet** — US-006 implements the AuditService. Auth events (login success/failure) must be wired up after US-006 completes.
4. **tenant_id from request body** — the `/plone-login` endpoint accepts `tenant_id` in the request body to determine which tenant to associate the user with. This is a necessary bootstrap step (the user has no JWT yet). The tenant must exist in the DB — a missing tenant causes a 500. In production, tenants should be pre-provisioned by an admin.
