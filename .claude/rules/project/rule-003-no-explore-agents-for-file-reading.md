---
id: rule-003
trigger: "When the Tech Lead needs to understand existing code or file contents"
updated: "2026-03-31"
---

# Rule 003 — No Explore Sub-Agents for File Reading

<constraint>
NEVER spawn a sub-agent (including `subagent_type: "Explore"`) to read or summarize files. Use `Read`, `Grep`, or `Glob` directly.
</constraint>

<why>
Explore agents return summaries — raw content is lost. Files must be re-read for `<file>` XML injection, doubling token cost (~60k wasted in Phase 2b).
</why>
