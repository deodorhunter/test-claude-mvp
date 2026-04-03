---
name: backlog-refinement
description: "Pre-sprint backlog refinement ceremony. Applies a 5-question yes-man filter to each Backlog US, producing KEEP/REWRITE/DROP/DEMOTE verdicts. Used by /refine-backlog command or invoked directly by product-owner agent."
metadata:
  trigger: "Before sprint planning for any phase, or when user requests backlog review"
  type: skill
  updated: "2026-04-02"
  version: "1.0"
---

<insight>
Agent-generated US tend toward reflexive agreement — restating user feedback as a feature without questioning whether new tooling, new files, or new processes are warranted. 3 of 15 Phase 3 US were yes-man responses caught only by explicit critic review. This skill encodes the filter.
</insight>

<why_this_matters>
A yes-man US wastes 5k–50k tokens in implementation + QA before anyone notices the deliverable adds no value. Catching it during refinement costs ~500 tokens (Haiku reads the US and applies the checklist). 100:1 cost ratio.
</why_this_matters>

<recognition_pattern>
Run this skill when:
- A new batch of US has been created from user feedback
- Sprint planning is about to begin for a phase
- User explicitly requests `/refine-backlog`
- Product-owner agent is validating backlog before delegation

Do NOT use for: individual US edits, implementation work, or post-sprint review.
</recognition_pattern>

<approach>

## The 5-Question Yes-Man Filter

For each US with status `📋 Backlog`, answer these questions:

### Q1 — New-File Test
> Does this US create a NEW file when consolidating into an existing doc/config would suffice?

Red flag: US creates `docs/NEW_GUIDE.md` when the content belongs in an existing section of `docs/AI_REFERENCE.md` or `CLAUDE.md`.

### Q2 — CP Test
> Does this US build tooling (make targets, scripts, commands) that `cp`, `mv`, or a 3-line shell command replaces?

Red flag: US creates `make init-framework` when `cp -r .claude/ target/` is the real workflow.

### Q3 — Hallucination Test
> Is >30% of the implementation detail unverifiable against actual tool documentation or files in the repo?

Red flag: US references settings keys, CLI flags, API fields, or hook types that cannot be confirmed by reading tool docs or existing config files. Check EVERY technical claim.

### Q4 — Duplication Test
> Does another US already cover ≥60% of this scope?

Red flag: Two US both "document model routing" or both "improve adoption docs."

### Q5 — User-Value Test
> If we ship everything else in this phase but skip this US, would users notice?

Red flag: US exists because feedback mentioned a topic, but the actual user need is addressed by a different US.

## Scoring

| Flags triggered | Verdict |
|---|---|
| 0 | **KEEP** — proceed to sprint |
| 1 | **KEEP with note** — address the flagged concern in implementation |
| 2 | **REWRITE** — scope is wrong, redefine before sprint |
| 3+ | **DROP or DEMOTE** — present to user for decision |

## Output Format

Present results as a markdown table:

```markdown
| US | Title | Q1 | Q2 | Q3 | Q4 | Q5 | Flags | Verdict | Note |
|---|---|---|---|---|---|---|---|---|---|
| US-NNN | Title | ✅ | ✅ | ⚠️ | ✅ | ⚠️ | 2 | REWRITE | [reason] |
```

Where: ✅ = passes (no concern), ⚠️ = flagged

After the table, provide a brief recommendation for each REWRITE/DROP/DEMOTE item:
- What specifically should change (for REWRITE)
- What absorbs the valid kernel (for DROP)
- Why it can wait (for DEMOTE)

## Constraints

1. Read each US file directly — do not rely on BACKLOG.md summaries alone
2. For Q3 (hallucination test): verify technical claims against actual files in the repo. Use `grep` or file reads, not assumptions
3. Present ALL verdicts to the human — never auto-drop a US
4. This skill produces analysis only. It does not modify US files

</approach>
