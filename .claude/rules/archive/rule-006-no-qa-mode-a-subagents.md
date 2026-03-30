# Rule 006 — No QA Sub-Agents for Mode A Validation

## Constraint

The Tech Lead MUST NOT spawn a QA Engineer sub-agent for Mode A (per-US) validation. QA sub-agents stall requesting Bash permissions. The Tech Lead runs tests directly: write script to `backend/tests/.temp_qa_us_NNN.py` (volume-mounted), execute via `docker exec -e PYTHONPATH=/app ai-platform-api python3 tests/.temp_qa_us_NNN.py`, delete from host. Max 2 attempts. Never write to `/tmp` — not volume-mounted.

## Context

Every QA Mode A sub-agent in Phase 2c stalled immediately requesting Bash permissions, triggering circuit-breaker violations. The volume-mounted path pattern (`backend/tests/`) eliminates both the sub-agent stall and the `/tmp` mount failure. For the full pattern see `.claude/agents/orchestrator.md` Phase 3 step 5.
