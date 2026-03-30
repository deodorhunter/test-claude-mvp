---
id: rule-003
title: "No Explore sub-agents for file reading or summarization"
layer: project
phase_discovered: "Phase 2b"
us_discovered: "US-013"
trigger: "When the Tech Lead needs to understand existing code or file contents before planning or delegating"
cost_if_ignored: "~60,000 tokens — Explore agents read files and return summaries, destroying the raw content needed for context injection; the Tech Lead must pay to re-read the same files when delegating to implementing agents"
updated: "2026-03-29"
---

# Rule 003 — No Explore Sub-Agents for File Reading

## Constraint

The Tech Lead MUST NEVER spawn a sub-agent (of any type, including `subagent_type: "Explore"`) solely to read, scan, or summarize files. Use the `Read`, `Grep`, or `Glob` tools directly in the Tech Lead's own context.

## Context

Explore agents read files and return a *summary* to the Tech Lead. The raw file content is lost. When the Tech Lead later needs to inject those files into an implementing agent's prompt (via `<file>` XML tags), it must pay to read them again — doubling the token cost. In a session, two Explore agents consumed ~60,000 tokens reading files that still had to be re-read for context injection. Direct `Read`/`cat` costs O(file_size) once; Explore costs O(file_size) twice plus the agent overhead.

## Examples

✅ Correct:
```
Read tool → /ai/planner/planner.py   (content now in Tech Lead context, ready to inject)
Grep tool → search for "class Planner"
```

❌ Avoid:
```python
Agent(subagent_type="Explore", prompt="Read ai/planner/ and summarize what's implemented")
# Returns a summary — raw content gone, cannot be injected downstream
```
