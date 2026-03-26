# US-002: Database Schema — Done

## Summary
Created SQLAlchemy ORM models and Alembic migration for all 5 core tables.

## Tables created
- `tenants` — organization entities
- `users` — platform users mapped from Plone identities; UNIQUE(plone_username, tenant_id)
- `tenant_plugins` — per-tenant plugin enable/disable + JSONB config
- `tenant_token_quota` — per-tenant monthly token quota tracking
- `audit_logs` — append-only compliance log (GDPR / EU AI Act)

## Security Note: audit_logs append-only enforcement
The `audit_logs` table MUST be append-only in production. The application database user
must NOT have UPDATE or DELETE privileges on this table. This is enforced at the DB role
level, not application level. In production, run after DB init:

    REVOKE UPDATE, DELETE ON TABLE audit_logs FROM <app_db_user>;

This cannot be done inside the Alembic migration (migrations run as owner/superuser).
The DevOps/Infra engineer must add this REVOKE to the DB initialization runbook.

## Indexes
- `ix_users_tenant_id` on `users(tenant_id)`
- `ix_tenant_plugins_tenant_plugin` on `tenant_plugins(tenant_id, plugin_name)`
- `ix_audit_logs_tenant_timestamp` on `audit_logs(tenant_id, timestamp)`

## Verification
1. `cd backend && alembic upgrade head` — all 5 tables created
2. `cd backend && alembic downgrade -1` — all tables dropped cleanly
3. `cd backend && pytest tests/test_schema.py` — 6 tests pass (no DB needed)
