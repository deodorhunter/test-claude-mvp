# Rule 008 — Read All Files Before Docker Fix

## Constraint
Before any fix requiring `make up` rebuild: read ALL files that could affect the symptom. Apply ALL fixes in one batch, rebuild once.

## Why
Single-file fix → rebuild → discover second cause → rebuild again = 2 rebuilds that should be 1.

## Always Read Before Backend Docker Fix
- The failing file + `backend/tests/conftest.py` + `infra/docker-compose.yml` env + `backend/app/core/config.py`
