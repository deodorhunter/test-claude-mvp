---
id: rule-001
title: "Every DB query must be filtered by tenant_id"
layer: project
phase_discovered: "Phase 1"
us_discovered: "US-002"
trigger: "When an agent writes any SQLAlchemy query or raw SQL"
cost_if_ignored: "~25,000 tokens — cross-tenant leak caught at QA, full US re-delegation"
updated: "2026-03-29"
---

# Rule 001 — Every DB Query Must Be Filtered by tenant_id

## Constraint

Every SQLAlchemy query that accesses tenant-owned data must include `.filter(Model.tenant_id == tenant_id)` or equivalent. No exceptions. The `tenant_id` comes from the JWT token, never from the request body.

## Context

This platform is multi-tenant. A query without tenant scoping will silently return data from all tenants to any authenticated user. This is a data breach, not a bug. The Security Engineer's review checklist catches this, but the implementing agent should enforce it at write time, not at review time.

## Examples

✅ Correct:
```python
plugins = await db.execute(
    select(Plugin).where(Plugin.tenant_id == current_user.tenant_id)
)
```

❌ Avoid:
```python
plugins = await db.execute(select(Plugin))  # returns ALL tenants' plugins
plugins = await db.execute(
    select(Plugin).where(Plugin.id == plugin_id)  # ID alone is not tenant-scoped
)
```
