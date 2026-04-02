# Rule 008 — Read All Relevant Files Before Editing When Docker Image Is Baked

## Constraint

Before making any fix that requires a Docker image rebuild (`make up`), the Tech Lead MUST read ALL files that could affect the symptom — including `conftest.py`, `docker-compose.yml` env sections, `pyproject.toml`, and any test setup files — not just the file where the error was observed. Apply all fixes in a single edit batch, then rebuild once.

## Context

In Phase 2c, a test failure was traced to `plone_bridge.py`. The fix was applied and the image rebuilt. Only after the rebuild was a second cause discovered: `conftest.py` was forcing `PLONE_BASE_URL` to a value that overrode the fix. A second rebuild was required. Had both files been read before the first edit, both fixes would have been batched and only one rebuild needed. Docker rebuilds are expensive (minutes of wall time + build log noise) and must never be triggered more than once per logical fix.

## Pattern

✅ Correct:
```
1. Symptom observed → identify all files that could be involved
2. Read: the failing file + conftest.py + docker-compose env + any test fixtures
3. Identify ALL root causes
4. Apply ALL fixes in one batch
5. Rebuild once: make up
```

❌ Avoid:
```
1. Fix the obvious file → rebuild → discover second cause
2. Fix second file → rebuild again
← Two rebuilds that should have been one
```

## Files to Always Read Before a Backend Docker Fix

- The file containing the error
- `backend/tests/conftest.py` (may override env vars or inject fixtures)
- `infra/docker-compose.yml` (env section may override Python `os.environ.setdefault`)
- `backend/app/core/config.py` (settings defaults)
