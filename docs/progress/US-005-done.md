# US-005: RBAC Middleware — Done

## Summary
Implemented permission system mapping Plone roles to platform permissions, with a FastAPI dependency factory for per-route enforcement.

## Permission Model

| Plone Role | Platform Permissions |
|---|---|
| Manager / Site Administrator | admin, query.execute, plugin.enable, plugin.disable, mcp.query |
| Editor | query.execute, mcp.query |
| Reviewer | query.execute, mcp.query |
| Member | query.execute |
| (unknown) | — (DENY ALL) |

## Usage Example
```python
@router.post("/query")
async def execute_query(
    current_user: CurrentUser = require_permission(Permission.QUERY_EXECUTE),
):
    ...
```

## Security Properties
- Default is DENY — unknown Plone roles get zero permissions
- Permission check uses JWT payload only — no DB query per request (sub-ms overhead)
- Cross-tenant isolation is enforced by JWT itself: `tenant_id` is in the token, not the request. A user authenticated for tenant A cannot present a token for tenant B.
- Every denial is logged to stderr; full audit trail will be wired in US-006.

## Security Notes — Residual Risks
1. **Audit log stub** — denial events are currently logged to stderr only. Must be wired to `AuditService` (US-006) after it is complete. Until then, denial events are not persisted.
2. **Role refresh** — Plone roles are embedded in the JWT at login time. If an admin changes a user's Plone role, the change is not reflected until the user's JWT expires and they re-login. Access token TTL is 60 minutes by default. For security-sensitive role changes, admins should be instructed to invalidate sessions (requires Redis-backed token invalidation, deferred to Phase 2).
3. **`guest` role** — The User model has `role IN ('admin', 'member', 'guest')` but `guest` has no permissions in ROLE_PERMISSIONS. This is intentional: guest users can authenticate but cannot execute any query. If guest access is needed, a separate US must define its permissions.
