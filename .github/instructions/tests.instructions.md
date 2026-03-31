---
applyTo: "backend/tests/**"
---

# Test Rules

## No multiline Python in bash -c

When writing test instructions that run inside Docker, never embed multi-line Python inside `bash -c "..."`. It breaks on shell quoting and Python indentation.

Instead: write the script to a file, execute via `docker exec`, delete after.

```bash
# Correct
docker exec ai-platform-api python3 /app/tests/.temp_qa_script.py

# Wrong — breaks on quoting
docker exec ai-platform-api python3 -c "
import asyncio
async def test():
    ...
"
```

The volume-mounted path is `backend/tests/` — write temp scripts there, not to `/tmp` (not mounted).

## Circuit breaker

Max 2 debug attempts on any failing test. If it fails after two targeted fixes, stop and report:
- Exact error output (≤ 10 lines)
- What was tried in each attempt
- Root cause hypothesis

Do not run `pip install` inside a running container. Update `backend/pyproject.toml` and tell the user to rebuild.

## Test isolation

Tests must not share state across tenants. Any test that touches tenant-owned data must assert that a different `tenant_id` cannot access the same resource.
