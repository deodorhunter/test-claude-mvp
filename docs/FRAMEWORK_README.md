# AI Governance Framework — Developer Reference
> Version 3.0 · 2026-03-30 · oh-my-claudecode Enterprise Edition
> EU AI Act compliant · Multi-tenant · Append-only audit trail

---

## Overview

This framework governs how Claude Code agents operate within this repository. It provides:
- **Pre-flight state checks** (hook) before any tokens are consumed
- **Structured agent definitions** (YAML/XML) with enforced Mute Return
- **Cognitive decentralization** (orchestrator, product owner, critic roles)
- **EU AI Act compliance controls** (data boundary, human oversight, audit trail)
- **Token economics** (~145k tokens/session savings vs the previous monolithic CLAUDE.md)

The framework is directly inspired by [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) paradigms, selectively adopting its best cognitive patterns while rejecting infra-level features incompatible with EU enterprise requirements.

---

## Architecture

```
CLAUDE.md                    ← Global physics only (~120 lines, down from 450)
│
├── .claude/hooks/
│   └── pre-prompt.sh        ← State check: AI_REFERENCE, Serena, git bloat, .omc/
│
├── .claude/settings.json    ← Hook registration (UserPromptSubmit)
│
├── .claude/agents/
│   ├── orchestrator.md      ← Tech Lead: delegation, phase gates, agent routing
│   ├── product-owner.md     ← Backlog, US format, Task Complexity Matrix
│   ├── critic.md            ← Plan validation (NEW — from oh-my-claudecode)
│   ├── backend-dev.md       ← FastAPI, SQLAlchemy, Alembic, Redis
│   ├── qa-engineer.md       ← Test execution (Mode A) + test authoring (Mode B)
│   ├── devops-infra.md      ← Docker, CI/CD, K8s, secrets
│   ├── doc-writer.md        ← Handoff docs, architecture docs (append-only)
│   ├── frontend-dev.md      ← React/Volto, TypeScript, auth flows
│   ├── security-engineer.md ← JWT, RBAC, audit logging, plugin isolation
│   ├── aiml-engineer.md     ← LLM adapters, planner, MCP, RAG, Qdrant
│   └── TEMPLATE.md          ← Agent creation template
│
├── .claude/commands/
│   ├── handoff.md           ← /handoff US-NNN: append to ARCHITECTURE_STATE.md
│   ├── compress-state.md    ← /compress-state: session snapshot + /clear
│   ├── init-ai-reference.md ← /init-ai-reference: write docs/AI_REFERENCE.md
│   ├── judge.md             ← /judge US-NNN: pre-QA AC check (~2k tokens)
│   ├── notepad.md           ← /notepad [category] [entry]: session memory (NEW)
│   ├── reflexion.md         ← /reflexion: extract rules at phase gate
│   └── phase-retrospective.md ← /phase-retrospective: cost analysis + session costs
│
└── .claude/rules/project/
    ├── rule-001 through rule-010  ← Accumulated project rules
    └── rule-011-eu-ai-act-data-boundary.md  ← NEW: compliance boundary
```

---

## What Was Adopted from oh-my-claudecode

After deep analysis of the oh-my-claudecode repository, five paradigms were incorporated:

### 1. Critic Agent (`.claude/agents/critic.md`)
A dedicated agent that challenges plans before any implementing agent is spawned. Reads the US plan, asks "what assumptions could be wrong?", returns CRITICAL/HIGH/LOW objections. Runs in parallel with context assembly for MEDIUM/HIGH complexity US. Break-even: prevents ~1 QA bounce-back per 6 US = ~25k tokens net savings.

### 2. Evidence-Driven Verification
The "fresh output only, never assume" principle is now enforced in all verification steps. Every PASS verdict in judge.md, qa-engineer.md, and orchestrator.md requires actual terminal output shown verbatim. "Tests passed" without output is rejected.

### 3. Notepad Wisdom (`.claude/commands/notepad.md`)
Timestamped, categorized session memory under four categories: Learnings, Decisions, Issues, Problems. Complements the memory system by capturing in-session institutional knowledge before `/compress-state` synthesizes it. Gitignored, local-only (rule-011 compliant).

### 4. Separation of Authoring and Review
Formalized as Hard Rule 17: "The implementing agent for a US and the judge/verifier for that US must always be different agents." Existing practice (Security Engineer reviews others' work) is now a universal principle.

### 5. Atomic Changes Philosophy
Added as explicit constraint in every agent's `<hard_constraints>`: "Make the smallest correct change satisfying the AC. Do not refactor adjacent code. Do not add features not in the US." Replaces the implicit "don't over-engineer" guidance with a first-class rule.

---

## What Was Rejected from oh-my-claudecode (EU AI Act Reasons)

| Feature | Why Rejected |
|---|---|
| Plugin marketplace | Supply chain risk — unreviewed code execution; EU AI Act Art. 9 (risk management) |
| Discord/Telegram/Slack notifications | Code fragments leave project boundary; GDPR Art. 5(1)(f) violation |
| `.omc/` session sync / JSONL replay export | Proprietary code in mutable files; GDPR Art. 5(1)(e) storage limitation |
| Multi-provider auto-routing (Gemini, Codex) | Data residency — transfers to non-EEA providers without lawful basis; GDPR Art. 46 |
| Autopilot mode (no checkpoints) | No human oversight; EU AI Act Art. 14 violation for high-risk AI contexts |

---

## EU AI Act Compliance Position

This framework is designed for **EU AI Act enterprise use** with private code and databases. Our compliance controls:

| Requirement | Implementation |
|---|---|
| **Art. 10 — Data Governance** | All processing stays within configured providers (Ollama local, Claude API with EU DPA). Session notes gitignored. |
| **Art. 12 — Logging** | Append-only `echo >>` for all audit events. PostgreSQL append-only audit table. No mutable replay files. |
| **Art. 13 — Transparency** | This document. All agents and rules versioned in `.claude/`. |
| **Art. 14 — Human Oversight** | Mandatory STOP + explicit approval at every US checkpoint and Phase Gate. No autonomous modes. |
| **GDPR Art. 5(1)(e) — Storage Limitation** | Session notes gitignored and never synced. No external session storage. |
| **GDPR Art. 46 — Data Transfers** | Only Ollama (local) and Claude API (EU DPA) are allowed providers. Auto-routing to other providers prohibited. |

See `.claude/rules/project/rule-011-eu-ai-act-data-boundary.md` for the full compliance rule.

---

## Token Economics

### Before (CLAUDE.md v2.2 — monolithic)
| Component | Tokens per invocation |
|---|---|
| CLAUDE.md monolith | ~8,000–12,000 tokens |
| Agent file (free-text, duplicated constraints) | ~2,000–3,000 tokens |
| Explore agents for file reading | ~60,000–131,000 tokens per session |
| Parallel agent context (no compress-state) | ~80,000 × N agents wasted |
| **Estimated session cost** | **~145,000 avoidable tokens/session** |

### After (v3.0 — oh-my-claudecode enterprise)
| Component | Tokens per invocation |
|---|---|
| CLAUDE.md (global physics only) | ~1,500 tokens |
| Agent file (YAML/XML, no duplication) | ~800–1,200 tokens |
| Serena navigation (vs file reads) | ~200 tokens per symbol lookup |
| Pre-prompt hook (catches missing AI_REFERENCE early) | ~50 tokens |
| Mute Return (agents return DONE not source code) | saves ~60,000 tokens per parallel wave |
| **Estimated session savings** | **~120,000–145,000 tokens/session** |

---

## Setup & Usage

### First Run
```bash
# 1. Verify AI_REFERENCE exists (hook will block without it)
ls docs/AI_REFERENCE.md

# 2. If missing, generate it
claude "/init-ai-reference"

# 3. Hook is auto-registered via .claude/settings.json
# It fires on every UserPromptSubmit and checks:
#   - docs/AI_REFERENCE.md exists (hard gate: exit 1 if missing)
#   - Serena MCP is configured (soft warning if not)
#   - git status < 15 dirty files (soft warning if over)
#   - .omc/ directory absent (EU AI Act compliance check)
```

### Starting a Speed 2 Session
```bash
# The orchestrator reads these three files at session start:
cat docs/AI_REFERENCE.md         # stack reference
cat docs/backlog/BACKLOG.md      # current phase status
cat .claude/workflow.md          # phase dependency graph
```

### Key Commands
| Command | When to use |
|---|---|
| `/init-ai-reference` | First run or after major stack change |
| `/judge US-NNN` | After implementing agent finishes, before DocWriter + QA (~2k tokens) |
| `/handoff US-NNN` | After US merged to main — appends to ARCHITECTURE_STATE.md |
| `/compress-state` | After 15+ tool calls, before parallel waves, at phase gates |
| `/notepad Learnings [entry]` | Capture in-session insights before they're lost |
| `/reflexion Phase-N` | At phase gate — extract durable rules from session incidents |
| `/phase-retrospective` | Mandatory at every Phase Gate — cost analysis + SESSION_COSTS.md row |

### Agent Routing Quick Reference
| Work type | Agent | Model |
|---|---|---|
| API endpoints, DB models, quota, migrations | backend-dev | Haiku/Sonnet |
| Auth, RBAC, plugin isolation, security review | security-engineer | Sonnet |
| MCP, RAG, Qdrant, planner, model adapters | aiml-engineer | Sonnet |
| Docker, CI/CD, K8s manifests | devops-infra | Haiku/Sonnet |
| React/Volto UI, TypeScript components | frontend-dev | Haiku/Sonnet |
| Test execution (Mode A) + test authoring (Mode B) | qa-engineer | Haiku (A) / Sonnet (B) |
| Handoff docs, architecture docs | doc-writer | Haiku |
| Plan/design challenge before delegation | critic | Haiku |

---

## Adding New Agents

1. Copy `.claude/agents/TEMPLATE.md` to `.claude/agents/<name>.md`
2. Fill in YAML frontmatter (name, description, owns, forbidden)
3. Fill in `<identity>`, `<hard_constraints>` (include relevant rules 001-011), `<workflow>`, `<output_format>`
4. Keep the file under 80 lines — lean agents cost less per invocation
5. Add agent to the routing table in `orchestrator.md`

---

## Adding New Rules

Rules are discovered via `/reflexion` at phase gates. Survival test before saving:
> "If an agent had known this rule from the start, would it have prevented at least one circuit-breaker trigger or QA bounce-back?"

If no → discard. Format: `.claude/rules/project/rule-NNN-short-name.md`. Import in CLAUDE.md Part 3.
