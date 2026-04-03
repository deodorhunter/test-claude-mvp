<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-002
description: "When an agent modifies backend/app/db/models.py"
updated: "2026-03-31"
paths:
  - "backend/app/db/**"
  - "backend/alembic/**"
---

# Rule 002 — Migration Before Model

<constraint>
Any change to `backend/app/db/models.py` requires a matching Alembic migration in `backend/alembic/versions/`. Write migration first, then update model.
</constraint>

<why>
Autogenerate misses enum/index/constraint changes. Model-first → smoke test fail → full US re-delegation.
</why>

<pattern>
`alembic revision --autogenerate -m "desc"` → review/correct → update `models.py` → `alembic upgrade head`
</pattern>
