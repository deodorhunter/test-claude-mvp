<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-001
description: "When an agent writes any SQLAlchemy query or raw SQL on tenant-owned data"
updated: "2026-03-31"
---

# Rule 001 — Every DB Query Filtered by tenant_id

<constraint>
Every SQLAlchemy query on tenant-owned data must include `.where(Model.tenant_id == tenant_id)`. tenant_id comes from JWT, never request body.
</constraint>

<why>
Missing tenant filter = silent cross-tenant data breach.
</why>

<pattern>
```python
select(Plugin).where(Plugin.tenant_id == current_user.tenant_id)  # correct
# select(Plugin).where(Plugin.id == plugin_id)  # WRONG — not tenant-scoped
```
</pattern>
