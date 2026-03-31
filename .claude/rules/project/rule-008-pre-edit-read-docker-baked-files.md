---
id: rule-008
trigger: "Before making any fix that requires a Docker image rebuild (make up)"
updated: "2026-03-31"
paths:
  - "infra/**"
  - "backend/app/core/config.py"
  - "backend/Dockerfile"
---

# Rule 008 — Read All Files Before Docker Fix

<constraint>
Before any fix requiring `make up` rebuild: read ALL files that could affect the symptom. Apply ALL fixes in one batch, rebuild once.
</constraint>

<why>
Single-file fix → rebuild → discover second cause → rebuild again = 2 rebuilds that should be 1.
</why>

<pattern>
Always read before backend Docker fix: the failing file + `backend/tests/conftest.py` + `infra/docker-compose.yml` env + `backend/app/core/config.py`
</pattern>
