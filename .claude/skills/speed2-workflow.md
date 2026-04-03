---
name: speed2-workflow
description: "Speed 2 orchestration workflow: session bootstrap, planning, delegation, post-US verification, and phase gates. Load when starting a Speed 2 (multi-US, multi-agent) session."
metadata:
  trigger: "When starting a Speed 2 session, planning a new phase, or delegating User Stories to sub-agents"
  type: skill
  updated: "2026-04-03"
  version: "4.0"
---

# Speed 2 Workflow

> On-demand skill for multi-US orchestration. Not loaded during Speed 1 (single-file fixes).
> For delegation protocol details, see `.claude/skills/speed2-delegation/SKILL.md`.
> For US format and complexity matrix, see `.claude/agents/product-owner.md`.

## Session Bootstrap

1. Read `docs/AI_REFERENCE.md` — ground truth for stack, ports, make targets.
2. Read `docs/backlog/BACKLOG.md` — current phase and US status.
3. Confirm understanding to the user before proceeding.

## Planning

1. Write technical plan in `docs/plan.md`.
2. Identify User Stories for current phase. Create `docs/backlog/US-NNN.md` files.
3. Assign each US to the correct agent. Select model per Task Complexity Matrix (in product-owner.md).
4. **STOP — present full plan and US list to user. Wait for explicit approval.**

## Git Branching (per US)

- Before work: `git checkout -b us/US-NNN-short-title`
- After approval: merge to `main`

## Delegation vs Direct Implementation

Default: **direct implementation**. Delegate only for clearly horizontal features.

| Domain count | Decision |
|---|---|
| 1-3 domains, independent | **Delegate** to specialist agent(s) |
| 4+ domains, tightly coupled | **Implement directly** |

See `.claude/skills/speed2-delegation/SKILL.md` for delegation protocol when delegating.

## Post-US Workflow (4 steps — use TodoWrite to track)

1. **Verify**: Run `/judge US-NNN` (git diff vs acceptance criteria)
2. **Test**: Smoke test — `curl -s http://localhost:8000/health` + `pytest -q --tb=short`
3. **Present**: Show user exact commands, output, and judge verdict. **STOP — wait for approval.**
4. **Merge**: On approval, merge branch → update US status in BACKLOG.md

## Phase Gate Workflow (5 steps — mandatory per rule-007)

When all US in a phase are Done, proceed **immediately** (never present as optional choice):

1. **Verify** all US marked Done in BACKLOG.md
2. **Full service verification**:
   ```bash
   make down && make up && make migrate
   curl -s http://localhost:8000/health  # API
   curl -s http://localhost:8080          # Plone
   curl -s http://localhost:6333/health  # Qdrant
   make test                              # all green
   ```
3. **Run `/phase-retrospective`** (appends cost row to SESSION_COSTS.md)
4. **Present summary** to user. **STOP — wait for approval.**
5. **Update** BACKLOG.md phase status, docs/plan.md

## Escalation Protocol

1. Record blocker in `docs/backlog/US-NNN.md` → "Blockers" section.
2. Critical (blocks dependent US) → STOP. Present to user immediately.
3. Contained → document as residual risk. Continue only if user is informed.
4. Never mark a US done with unresolved critical blockers.

## Critic Consultation (HIGH complexity only)

Before delegating a HIGH complexity US, spawn the Critic agent with the plan. Act only on CRITICAL objections. For HIGH tasks: also produce a Deliberation Record (`.claude/skills/ralplan-deliberation.md`).
