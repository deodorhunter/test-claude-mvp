---
description: "Before sprint planning for any phase"
---

<metadata>
  id: rule-018
  updated: "2026-04-02"
</metadata>

# Rule 018 — Pre-Sprint Backlog Refinement

<constraint>
Before selecting work for a sprint, run `/refine-backlog` on all 📋 Backlog US in the target phase. Present verdicts to the user; no US status changes without human approval.
</constraint>

<why>
3 of 15 Phase 3 US were yes-man responses (reflexive agreement with user feedback). Catching them post-implementation wasted ~30k tokens. Catching them during refinement costs ~500 tokens.
</why>

<pattern>
✅ Before sprint: run `/refine-backlog` → present verdicts → human approves → sprint starts
❌ Add US to sprint without yes-man filter check
</pattern>
