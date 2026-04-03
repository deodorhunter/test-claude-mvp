<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-006
description: "When the Tech Lead needs to validate a US (Mode A per-US validation)"
updated: "2026-03-31"
paths:
  - "backend/tests/**"
---

# Rule 006 — No QA Sub-Agents for Mode A

<constraint>
Tech Lead runs Mode A tests directly: write to `backend/tests/.temp_qa_us_NNN.py` (volume-mounted), execute via `docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa_us_NNN.py`, delete. Max 2 attempts. Never `/tmp` (not mounted).
</constraint>

<why>
QA sub-agents stall on Bash permissions, triggering circuit-breaker violations.
</why>
