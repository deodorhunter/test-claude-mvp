<!-- framework-template v3.0 | synced: 2026-04-02 -->

# AI Governance Framework — Template

This directory contains the portable layer of the AI governance framework.

**Last synced:** 2026-04-02
**Framework version:** v3.0

## Contents

| Path | Purpose | Notes |
|---|---|---|
| `CLAUDE.template.md` | Root configuration template | Rename to `CLAUDE.md` in new project |
| `HOW-TO-ADOPT.md` | Adoption guide | Copy-first path as primary |
| `agents/` | Specialized agent definitions | All 12 agents (orchestrator, backend-dev, frontend-dev, etc.) |
| `rules/` | Behavioral constraint templates | 20 active project rules + TEMPLATE.md for new rules |
| `copilot-instructions.template.md` | Copilot-specific instructions | Rename to `.github/copilot-instructions.md` in new project |

## Quick Start

```bash
# 1. Copy framework to new project (PRIMARY adoption path)
cp -r .claude /your-new-project/
cp CLAUDE.md /your-new-project/

# 2. Customize for your stack
cd /your-new-project
vi docs/AI_REFERENCE.md          # Stack identity (FastAPI, Django, etc.)
vi .claude/agents/backend-dev.md # Your project paths
```

See `HOW-TO-ADOPT.md` for full details.

## Agents Included

- `orchestrator.md` — Tech Lead (orchestration, phase gates, delegation)
- `backend-dev.md` — Backend engineer (FastAPI, models, migrations)
- `frontend-dev.md` — Frontend engineer (React, TypeScript, styling)
- `aiml-engineer.md` — AI/ML engineer (models, embeddings, RAG)
- `security-engineer.md` — Security engineer (auth, RBAC, audit)
- `devops-infra.md` — DevOps engineer (Docker, CI/CD, infra)
- `doc-writer.md` — Documentation specialist (handoff docs, architecture)
- `qa-engineer.md` — QA engineer (testing, validation)
- `product-owner.md` — Product owner (backlog, US, ceremonies)
- `critic.md` — Plan validator (pre-implementation review)
- `debugger.md` — Bug fixer (targeted fixes, small refactors)
- `general-purpose.md` — Research agent (open-ended exploration)

## Rules Included

20 active behavioral constraints organized by concern:

| ID | Title | Concern |
|---|---|---|
| rule-001 | Every DB query filtered by tenant_id | Multitenancy |
| rule-002 | Migrations before model changes | Schema safety |
| rule-003 | No Explore agents for file reading | Token efficiency |
| rule-004 | AI_REFERENCE.md check every session | Stack knowledge |
| rule-005 | DocWriter no multiline bash | Output clarity |
| rule-006 | No QA Mode A subagents | Tool permissions |
| rule-007 | Phase Gate "proceed" = complete all steps | Workflow enforcement |
| rule-008 | Pre-edit read Docker baked files | CI/CD safety |
| rule-009 | Serena-first navigation (LSP) | Token efficiency |
| rule-010 | Compress-state before parallel waves | Context budgeting |
| rule-011 | EU AI Act data boundary | Compliance |
| rule-012 | MCP trust boundary validation | Security |
| rule-013 | Docker COPY no shell operations | Dockerfile safety |
| rule-014 | Registry enforcement opt-in | Plugin safety |
| rule-018 | Pre-sprint backlog refinement | Agile ceremony |
| rule-019 | Serena-Git isolation in worktrees | Worktree safety |
| rule-020 | Phase Gate auto-proceed (no choice) | Workflow enforcement |

## Customization Checklist

When copying to a new project:

- [ ] Update `docs/AI_REFERENCE.md` with your stack identity
- [ ] Edit `.claude/agents/backend-dev.md` to match your project's `owns:` and `forbidden:` paths
- [ ] Remove project-specific rules (e.g., rule-001 if you're not multi-tenant)
- [ ] Add your first domain rule (e.g., your auth pattern, schema constraint)
- [ ] Test with Speed 1 (Copilot) on a small fix to verify file scope

## Adoption Paths

**Copy-first (recommended):** 2 commands, full framework
→ See `HOW-TO-ADOPT.md`

**Selective (advanced):** Cherry-pick agents + rules
→ See "Advanced: Selective Adoption" in `HOW-TO-ADOPT.md`

---

For more details, see `HOW-TO-ADOPT.md` and the main framework `FRAMEWORK_README.md`.
