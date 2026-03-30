# Rule 001 — Every DB Query Filtered by tenant_id

## Constraint
Every SQLAlchemy query on tenant-owned data must include `.where(Model.tenant_id == tenant_id)`. tenant_id comes from JWT, never request body.

## Why
Missing tenant filter = silent cross-tenant data breach.

## Pattern
```python
select(Plugin).where(Plugin.tenant_id == current_user.tenant_id)  # correct
# select(Plugin).where(Plugin.id == plugin_id)  # WRONG — not tenant-scoped
```
