# Rule 003 — No Explore Sub-Agents for File Reading

## Constraint
NEVER spawn a sub-agent (including `subagent_type: "Explore"`) to read or summarize files. Use `Read`, `Grep`, or `Glob` directly.

## Why
Explore agents return summaries — raw content is lost. Files must be re-read for `<file>` XML injection, doubling token cost (~60k wasted in Phase 2b).
