<!-- framework-template v3.0 | synced: 2026-04-02 -->
---
id: rule-004
description: "At the start of any Speed 2 (Orchestrator Mode) session"
updated: "2026-03-31"
---

# Rule 004 — AI_REFERENCE.md Check Every Session

<constraint>
At every Speed 2 session start, read `docs/AI_REFERENCE.md` first. If missing: STOP. Tell user to run `/init-ai-reference`. Never explore the codebase as a fallback.
</constraint>

<why>
Per-session precondition, not one-time setup. Without it, ~45k tokens wasted reconstructing stack knowledge via Explore agents.
</why>
