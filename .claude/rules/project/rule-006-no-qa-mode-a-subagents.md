# Rule 006 — No QA Sub-Agents for Mode A Validation

## Constraint

The Tech Lead MUST NOT spawn a QA Engineer sub-agent for Mode A (per-US) validation. QA sub-agents cannot execute Bash/docker commands and will stall requesting permissions. Instead, the Tech Lead runs the manual tests directly using the `Write` tool + `docker cp` + `docker exec` pattern, then presents commands and actual output to the user.

## Context

Every QA Mode A sub-agent in Phase 2c stalled immediately requesting Bash permissions. The Tech Lead then fell into a circuit-breaker violation trying to run the tests itself via repeated docker exec attempts. The correct pattern: write a single test script with the `Write` tool, copy it into the container once, run it once, present results to user. Max 2 attempts (Rule 4 applies here). If both attempts fail, report and stop.

## Pattern

✅ Correct:
```python
# 1. Write test script
Write tool → /tmp/qa_us_NNN.py

# 2. Copy into container and run (one command)
docker cp /tmp/qa_us_NNN.py ai-platform-api:/tmp/ && \
  docker exec -e PYTHONPATH=/app ai-platform-api python3 /tmp/qa_us_NNN.py && \
  docker exec ai-platform-api rm /tmp/qa_us_NNN.py

# 3. Present exact command + output to user at Phase 3 step 6
```

❌ Avoid:
```python
Agent(subagent_type="qa-engineer", prompt="Run manual tests from handoff doc...")
# → stalls on first tool call, requests Bash permission, returns nothing
```

## When `make test` suffices

If all automated unit tests pass (`make test -q`), the manual docker exec step is supplementary verification for the user. The Tech Lead must still present the commands and output (or the pytest results) so the user can independently confirm.
