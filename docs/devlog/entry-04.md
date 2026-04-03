← [Back to DEVLOG index](../DEVLOG.md)

## Entry 4 — Architectural Decision: Rules vs Skills vs Agents

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

A recurring early mistake: appending "lessons learned" prose directly to `CLAUDE.md`. This is wrong because `CLAUDE.md` is always-loaded — every token added to it costs tokens in every future session, forever.

The correct architecture emerged from asking: what is the right granularity for different types of knowledge?

**Agents** — specialized roles with domain expertise. The orchestrator, the backend developer, the security reviewer. These are long-lived and session-persistent.

**Skills** — reusable procedures loaded on demand. How to delegate a User Story. How to run a phase gate. Triggered only when the relevant task starts.

**Rules** — behavioral constraints. "Never write a DB query without tenant_id." "Always read the migration file before touching the model." Small, discrete, actionable. One rule per file. Active until explicitly removed.

The key mechanic: `CLAUDE.md` stays a lean index that imports only currently-active rules. When a rule is no longer needed, remove the import. When a rule is valuable org-wide, promote it to an organization-level layer. **`CLAUDE.md` itself never grows** — only the import list changes.

---
