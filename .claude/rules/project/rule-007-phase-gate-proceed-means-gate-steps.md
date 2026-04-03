---
description: "When user says \"proceed\", \"approved\", or \"continue\" at a phase boundary, OR when all US in a phase are marked Done"
---

<metadata>
  id: rule-007
  updated: "2026-04-03"
</metadata>

# Rule 007 — Phase Gate Is Mandatory and Non-Discretionary

<constraint>
When user says "proceed"/"approved"/"continue" at a phase boundary, complete ALL Phase Gate steps BEFORE starting next phase. When all US in a phase are marked Done, proceed IMMEDIATELY with Phase Gate steps — never ask "Phase N+1 work OR Phase Gate N?" The gate is mandatory, not a choice.
</constraint>

<why>
Phase Gate was skipped in Phase 2c, presented as optional in Phase 3b, and again in Phase 3c. Each skip costs ~40k tokens (missing retrospective, cost analysis). Absorbs former rule-020 (phase gate auto-proceed).
</why>

<pattern>
✅ All US Done → "Proceeding with mandatory Phase Gate steps." → run all gate steps → present to user
✅ User says "proceed" → run all gate steps → then start next phase
❌ "Ready for: 1. Phase 3c work 2. Phase Gate 3b — which do you prefer?"
❌ User says "proceed" → skip gate → start planning next phase immediately
</pattern>
