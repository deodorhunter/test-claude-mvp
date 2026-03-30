# Rule 002 — Migration Before Model

## Constraint
Any change to `backend/app/db/models.py` requires a matching Alembic migration in `backend/alembic/versions/`. Write migration first, then update model.

## Why
Autogenerate misses enum/index/constraint changes. Model-first → smoke test fail → full US re-delegation.

## Pattern
`alembic revision --autogenerate -m "desc"` → review/correct → update `models.py` → `alembic upgrade head`
