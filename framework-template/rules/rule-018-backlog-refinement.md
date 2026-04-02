<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-018
trigger: "Before sprint planning for any phase"
updated: "2026-04-02"
---

# Rule 018 — Pre-Sprint Backlog Refinement

<constraint>
Before selecting work for a sprint, run `/refine-backlog` on all 📋 Backlog US in the target phase. Present verdicts to the user; no US status changes without human approval.
</constraint>

<why>
3 of 15 Phase 3 US were yes-man responses (reflexive agreement with user feedback). Catching them post-implementation wasted ~30k tokens. Catching them during refinement costs ~500 tokens.
</why>
