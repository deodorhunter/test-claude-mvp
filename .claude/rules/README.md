---
type: rules-architecture
version: "1.0.0"
updated: "2026-03-29"
---

# Rules Architecture

> Discrete, versioned behavioral constraints for Claude.
> Rules are **not** appended to CLAUDE.md — they are separate files, imported via `@` when active.
> This keeps CLAUDE.md lean while keeping rules versioned, diff-able, and deletable.

---

## Two Layers

```
.claude/rules/
  org/        ← constraints valid across ALL org projects (promoted to plugin when ready)
  project/    ← constraints discovered during THIS project's sessions
```

### Layer 1 — Project Rules (`.claude/rules/project/`)

Discovered during development. Saved by `/reflexion` at phase gates.

**Survival test before saving:** *"If an agent had known this rule from the start, would it have prevented at least one circuit-breaker trigger or one QA bounce-back?"*

If no → discard. The rule must earn its token cost in every future session it's loaded.

### Layer 2 — Org Rules (`.claude/rules/org/`)

Project rules that proved valuable enough to share across all 40 projects. These graduate to the org plugin when packaged.

Start empty. Promote rules here manually after they've proven themselves in 2+ projects.

---

## How to Activate a Rule

Add an `@` import to the `## Active Project Rules` section in `CLAUDE.md`:

```markdown
## Active Project Rules
@.claude/rules/project/rule-001-tenant-isolation.md
@.claude/rules/project/rule-002-redis-timeout.md
```

To deactivate: remove the import line. The rule file stays on disk (version history preserved).

To promote to org: move the file to `.claude/rules/org/` and add it to the org plugin.

---

## Rule File Format

```markdown
---
id: rule-NNN
title: "Short human-readable title"
layer: project | org
phase_discovered: "Phase 2a"
us_discovered: "US-011"
trigger: "When an agent [does X]"
cost_if_ignored: "~15,000 tokens (circuit breaker loop)" | "~25,000 tokens (full QA bounce-back)"
updated: "YYYY-MM-DD"
---

# Rule NNN — [Title]

## Constraint

[One clear sentence: what agents must or must not do.]

## Context

[2-3 sentences: WHY this rule exists. What failure it prevents. What we learned.]

## Examples

✅ Correct:
[concrete example]

❌ Avoid:
[concrete example of what triggered the failure]
```

---

## Naming Convention

```
rule-001-tenant-isolation.md      ← sequential ID + kebab-case topic
rule-002-no-raw-redis-timeout.md
rule-003-migration-before-model.md
```

Keep rules under 30 lines each. If a rule needs more explanation, it's a skill, not a rule.
