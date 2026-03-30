# Rule 006 — No QA Sub-Agents for Mode A

## Constraint
Tech Lead runs Mode A tests directly: write to `backend/tests/.temp_qa_us_NNN.py` (volume-mounted), execute via `docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa_us_NNN.py`, delete. Max 2 attempts. Never `/tmp` (not mounted).

## Why
QA sub-agents stall on Bash permissions, triggering circuit-breaker violations.
