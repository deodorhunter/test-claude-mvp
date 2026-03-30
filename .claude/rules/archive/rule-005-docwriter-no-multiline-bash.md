---
id: rule-005
title: "DocWriter and QA must not use multiline Python inside bash -c"
layer: project
phase_discovered: "Phase 2b"
us_discovered: "US-013"
trigger: "When DocWriter writes Manual Test Instructions, or when QA runs live integration tests in Docker"
cost_if_ignored: "~15,000 tokens — multiline Python in bash -c fails on quote escaping and indentation; QA agent enters debugging loop rewriting the same script multiple times before giving up or switching approach"
updated: "2026-03-29"
---

# Rule 005 — No Multiline Python in bash -c for Docker Tests

## Constraint

When DocWriter writes Manual Test Instructions, or when QA runs integration tests via `docker exec`, NEVER embed multi-line Python scripts inside `bash -c "..."`. Instead: write the script to a temporary file using the `Write` tool, execute it via `docker exec ... python3 /tmp/qa_script.py`, then delete it.

## Context

`docker exec container python3 -c "import asyncio\nasync def test():\n    ..."` breaks on shell quoting, heredoc escaping, and Python indentation. The DocWriter generated this pattern in the US-013 handoff for all three manual test scenarios; the QA agent had to rewrite each command. Using a temp file sidesteps all quoting issues, produces readable error messages, and is trivially deletable after the test run.

## Examples

✅ Correct:
```python
# Write tool → /tmp/qa_us013.py
import asyncio
from ai.planner.planner import Planner
...
asyncio.run(test())
```
```bash
docker exec ai-platform-api python3 /tmp/qa_us013.py && rm /tmp/qa_us013.py
```

❌ Avoid:
```bash
docker exec ai-platform-api python3 -c "
import asyncio
from ai.planner.planner import Planner   # breaks on quote/indent
...
"
```
