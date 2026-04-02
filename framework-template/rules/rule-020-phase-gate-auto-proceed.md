<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-020
trigger: "After all US in a phase are marked ✅ Done"
updated: "2026-04-02"
---

# Rule 020 — Phase Gate Auto-Proceed (No Discretionary Choices)

<constraint>
When all User Stories in a phase are marked ✅ Done, orchestrator MUST proceed immediately and automatically with Phase Gate steps (orchestrator.md Phase 4). Never ask the user "Phase N+1 work OR Phase Gate N?" — the gate is mandatory and non-discretionary.
</constraint>

<why>
Phase Gate was skipped in Phase 2c and nearly again in Phase 3b. Each skip costs ~40k tokens (missing retrospective, cost analysis, architecture doc). Recurrence indicates the gate is being treated as optional. Hard Rule 7 (rule-007) mandates gate execution; this rule prevents the discretionary-choice anti-pattern.
</why>

<pattern>
✅ **Correct (orchestrator auto-proceeds):**
```
Wave 2b complete (US-068 ✅ Done).
→ "Phase Gate 3b — Proceeding with mandatory gate steps."
→ Full Service Verification
→ DocWriter Mode B
→ /phase-retrospective
→ /reflexion
→ Append SESSION_COSTS.md
→ "STOP — wait for explicit user approval before starting Phase 4."
```

❌ **What to avoid:**
```
"Wave 2b complete. Ready for:
1. Phase 3c work — continue with adoption docs
2. Phase Gate 3b — full verification + retrospective

Which would you prefer?"
```
(This gives the user a choice over a mandatory gate — violates rule-007.)
</pattern>
