# Rule 004 — AI_REFERENCE.md Check Every Session

## Constraint
At every Speed 2 session start, read `docs/AI_REFERENCE.md` first. If missing: STOP. Tell user to run `/init-ai-reference`. Never explore the codebase as a fallback.

## Why
Per-session precondition, not one-time setup. Without it, ~45k tokens wasted reconstructing stack knowledge via Explore agents.
