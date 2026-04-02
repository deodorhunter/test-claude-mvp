---
id: rule-007
trigger: "When user says \"proceed\", \"approved\", or \"continue\" at a phase boundary"
updated: "2026-03-31"
---

# Rule 007 — "Proceed" = Complete Gate Steps First

<constraint>
When user says "proceed"/"approved"/"continue" at a phase boundary, complete ALL Phase Gate steps BEFORE starting next phase. "Proceed" = run the Gate, not skip it.
</constraint>

<why>
Phase Gate was skipped entirely in Phase 2c — BACKLOG not updated, retrospective not run. Gate steps are in orchestrator.md Phase 4.
</why>

<pattern>
✅ User says "proceed" → run all Phase 4 gate steps → then start next phase
❌ User says "proceed" → skip gate → start planning next phase immediately
</pattern>
