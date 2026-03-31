---
applyTo: "backend/**"
---

# Backend Rules

## Tenant isolation (always required)

Every SQLAlchemy query on tenant-owned data must be filtered by `tenant_id`. No exceptions.

```python
# Correct
select(Plugin).where(Plugin.tenant_id == current_user.tenant_id)

# Wrong — returns data for ALL tenants
select(Plugin).where(Plugin.id == plugin_id)
```

`tenant_id` comes from the JWT token (`current_user.tenant_id`), never from the request body.

## Migration before model

When editing `backend/app/db/models.py`, create the Alembic migration first:

1. `alembic revision --autogenerate -m "description"`
2. Review and manually correct the generated migration (autogenerate misses enum additions, index changes, check constraints)
3. Update `models.py`
4. `alembic upgrade head`

Do not update the model first — a schema mismatch at smoke test requires full re-work.

## Targeted editing

Do not rewrite SQLAlchemy models or Alembic migrations from scratch. Use the `Edit` tool for precise replacements. For migrations, always read the previous version before adding a new one.
