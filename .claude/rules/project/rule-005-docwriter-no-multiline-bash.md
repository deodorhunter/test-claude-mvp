---
description: "When DocWriter writes Manual Test Instructions, or when QA runs integration tests via docker exec"
paths:
  - "backend/tests/**"
  - "docs/handoffs/**"
---

<metadata>
  id: rule-005
  updated: "2026-03-31"
</metadata>

# Rule 005 — No Multiline Python in bash -c

<constraint>
Never embed multi-line Python inside `docker exec ... python3 -c "..."`. Write script to temp file with `Write` tool, execute via `docker exec ... python3 /path/script.py`, then delete.
</constraint>

<why>
Shell quoting + Python indentation inside bash -c breaks reliably. Temp file pattern is quoting-safe and debuggable.
</why>

<pattern>
```bash
# Write tool → backend/tests/.temp_qa.py, then:
docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa.py && rm backend/tests/.temp_qa.py
```
</pattern>
