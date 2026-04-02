---
id: rule-002
title: "Write Alembic migration before touching ORM models"
layer: project
phase_discovered: "Phase 1"
us_discovered: "US-002"
trigger: "When an agent modifies backend/app/db/models.py"
cost_if_ignored: "~15,000 tokens — make migrate fails at smoke test, US re-delegation"
updated: "2026-03-29"
---

# Rule 002 — Migration Before Model

## Constraint

Any change to `backend/app/db/models.py` must be accompanied by a new Alembic migration in `backend/alembic/versions/`. Write the migration first, then update the model. Never make schema changes manually or assume autogenerate will catch everything.

## Context

Alembic autogenerate misses some changes (enum additions, index changes, check constraints). Writing the migration explicitly before the model prevents `make migrate` from failing at the smoke test step, which triggers a full US re-delegation cycle.

## Examples

✅ Correct order:
1. `alembic revision --autogenerate -m "add_plugin_tenant_index"`
2. Review and manually correct the generated migration
3. Update `models.py` to match
4. Run `alembic upgrade head` in smoke test

❌ Avoid:
1. Update `models.py` first
2. Forget the migration
3. Smoke test fails: `make migrate` → schema mismatch error
