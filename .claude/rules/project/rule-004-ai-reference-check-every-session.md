---
description: "At the start of any Speed 2 (Orchestrator Mode) session"
---

<metadata>
  id: rule-004
  updated: "2026-04-07"
</metadata>

# Rule 004 — Memories First, AI_REFERENCE.md as Fallback

<constraint>
At every Speed 2 session start:
1. Call `mcp__serena__list_memories` → read relevant memories (`suggested_commands`, `architecture/*`, `testing/*`)
2. Fall back to `docs/AI_REFERENCE.md` only for env vars, health endpoints, or content not covered by memories
If AI_REFERENCE.md is missing AND memories are insufficient: STOP. Tell user to run `/init-ai-reference`.
</constraint>

<why>
Memories are a superset of AI_REFERENCE.md for common content (commands, ports, file paths) at ~65 tokens per memory vs ~1,743 tokens for the full file. Reading AI_REFERENCE.md when memories exist wastes ~1,300 tokens per delegation.
</why>

<pattern>
✅ Session start: `list_memories` → read `suggested_commands` + relevant `architecture/*` → proceed
✅ Fallback: `Read docs/AI_REFERENCE.md` when memory is insufficient (env vars, health endpoints)
❌ Session start: `Read docs/AI_REFERENCE.md` unconditionally when memories exist
❌ Session start: explore codebase to discover stack, ports, test commands
</pattern>
