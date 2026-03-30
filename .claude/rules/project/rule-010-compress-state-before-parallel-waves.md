# Rule 010 — Compress-State Before Parallel Waves

## Constraint
MANDATORY `/compress-state` → `/clear` → read `docs/.temp_context.md` BEFORE: spawning ≥2 parallel agents, after receiving ≥2 parallel results, after 15 tool calls, at Phase Gate opening.

## Why
80k planning context × 3 agents = 240k wasted tokens. Clear break between waves costs 30s, saves thousands of tokens.
