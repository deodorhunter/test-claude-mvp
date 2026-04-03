<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-005
description: "When DocWriter writes Manual Test Instructions, or when QA runs integration tests via docker exec"
updated: "2026-03-31"
paths:
  - "backend/tests/**"
  - "docs/handoffs/**"
---

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
