---
id: rule-004
title: "AI_REFERENCE.md check is mandatory at every Speed 2 session start"
layer: project
phase_discovered: "Phase 2b"
us_discovered: "US-013"
trigger: "At the start of any Speed 2 (Orchestrator Mode) session"
cost_if_ignored: "~60,000 tokens — without AI_REFERENCE.md the Tech Lead falls back to blind codebase exploration (Glob, Grep, Read loops) to reconstruct stack knowledge already captured in the reference file"
updated: "2026-03-29"
---

# Rule 004 — AI_REFERENCE.md Check Every Session

## Constraint

At the very start of every Speed 2 session, before spawning any agent or reading any file, attempt to read `docs/AI_REFERENCE.md`. If it does not exist: **STOP immediately**. Do not explore the codebase as a fallback. Tell the user: *"AI_REFERENCE.md is missing. Please run: `claude \"Esegui @.claude/commands/init-ai-reference.md\"`"*

## Context

The original CLAUDE.md described the `AI_REFERENCE.md` check as part of "Phase 0 — Bootstrap (first run of a new project only)", implying it was a one-time setup step. This caused the Tech Lead to skip the check in subsequent sessions. The check must be treated as a **per-session precondition**, not a one-time setup. Without it, the Tech Lead reconstructed ~45,000 tokens of stack knowledge through Explore agents that was already in (or should have been in) the reference file. The "first run only" framing in CLAUDE.md is incorrect and was the direct root cause of the violation.

## Examples

✅ Correct (session start):
```
1. Read docs/AI_REFERENCE.md  →  found → proceed
2. Read docs/backlog/BACKLOG.md
3. Begin planning
```

❌ Avoid:
```
1. AI_REFERENCE.md missing
2. Spawn Explore agents to understand the stack  ← STOP HERE instead
3. Read handoffs, models, tests to reconstruct knowledge
```
