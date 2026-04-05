# AI Governance Framework — Developer Reference
> Version 4.0 · 2026-04-03 · oh-my-claudecode Enterprise Edition
> EU AI Act compliant · Multi-tenant · Append-only audit trail

---

## Overview

This framework governs how Claude Code agents operate within this repository. It provides:
- **Pre-flight state checks** (hook) before any tokens are consumed
- **Structured agent definitions** (YAML/XML) with enforced Mute Return
- **Cognitive decentralization** (orchestrator, product owner, critic roles)
- **EU AI Act compliance controls** (data boundary, human oversight, audit trail)
- **Token economics** (context loading: 60,764 → 39,313 bytes, −35% — see benchmark/results/optimized.txt; anti-pattern avoidance: up to ~145k tokens/session — Explore agents, missing context injection, etc.)

The framework is directly inspired by [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) paradigms, selectively adopting its best cognitive patterns while rejecting infra-level features incompatible with EU enterprise requirements. For a full feature comparison, honest assessment, and token-saving techniques extracted from OMC, see [`docs/COMPETITIVE_ANALYSIS.md`](COMPETITIVE_ANALYSIS.md).

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
│   ├── init-ai-reference.md ← /init-ai-reference: write docs/AI_REFERENCE.md
│   ├── judge.md             ← /judge US-NNN: pre-QA AC check (~2k tokens)
│   ├── notepad.md           ← /notepad [category] [entry]: session memory (NEW)
│   ├── reflexion.md         ← /reflexion: extract rules at phase gate
│   └── phase-retrospective.md ← /phase-retrospective: cost analysis + session costs
│
└── .claude/rules/project/
    └── rule-001 through rule-019  ← 13 active rules (gaps where rules were absorbed or deleted)
```

---

## Persistent Memory System

Claude Code maintains a file-based memory system for this project at:
`~/.claude/projects/-Users-martina-personal-projects-test-claude-mvp/memory/`

This directory is **not inside the repo** — it lives in Claude Code's personal workspace, keyed by project path. It persists across sessions and is loaded automatically.

### What is stored

| Type | Purpose | Examples |
|---|---|---|
| `user` | Role, background, preferences | expertise level, coding background |
| `feedback` | Behavioral corrections + confirmations | "never skip phase gate", "no QA sub-agents for Mode A" |
| `project` | Ongoing initiatives, decisions, deadlines | MVP phase status, incident postmortems |
| `reference` | Pointers to external resources | Linear board, Grafana dashboard |

### How it works

- `MEMORY.md` — index file, loaded every session (150-line limit; one-line entry per memory file)
- Individual `.md` files — full memory bodies with YAML frontmatter (`name`, `description`, `type`)
- Claude writes proactively for durable, non-obvious facts; reads when context suggests prior knowledge applies
- Stale memories are updated or removed — never blindly trusted over current file state

### What NOT to store

Code patterns, file paths, or project architecture (derivable from codebase). Git history (`git log` is authoritative). In-progress task state (use Tasks instead). Anything already in CLAUDE.md.

### Current state

15 active entries covering incidents, behavioral feedback rules, MVP initiative status, and infrastructure configuration (as of 2026-04-04).

---

## Three-Format Architecture: Rule vs Skill vs Command

The framework uses three distinct formats for governance knowledge. Choosing the wrong one creates rule bloat, silent failures, or wasted tokens. The decision criterion is the **token cost model**, not the importance of the constraint.

| Format | Job | Loaded when | Use when |
|---|---|---|---|
| **Rule** | Behavioral red line | Always (within path scope) | Any agent could violate this. Cost of missing it > cost of always loading it. |
| **Skill** | Procedure for doing something well | On-demand at task start | Only one agent/task type needs it. Loading it every session would waste tokens. |
| **Command** | User-invoked macro | Only when user runs `/command` | Human decides when it's needed. Zero cost otherwise. |

**Survival tests:**
- Rule: "Could any agent, on any task in scope, violate this and cause a breach, bounce-back, or compliance failure?" If no → wrong format.
- Skill: "Does only one agent/task type need this, only at a specific moment?" If yes → Skill.
- Command: "Does a human need to consciously invoke this?" If yes → Command.

**Worked example — Hart's Rules for audience-aware writing:**
Obvious candidate for a Rule. But only `doc-writer` uses it, only during Mode B. A Rule on `docs/**` would load for any agent touching a doc path — including the orchestrator injecting `<file>` tags. Most sessions would pay the token cost and gain nothing. Correctly placed as a Skill (`.claude/skills/writing-audience.md`): zero cost until `doc-writer` enters Mode B and loads it explicitly.

**Token cost implications:**
- Rules: `wc -c .claude/rules/project/*.md` — every byte here loads every session in scope
- Skills: free until triggered; loaded via `trigger:` frontmatter or explicit agent instruction
- Commands: free until the user types `/commandname`

---

## What Was Adopted from oh-my-claudecode

After deep analysis of the oh-my-claudecode repository, five paradigms were incorporated:

### 1. Critic Agent (`.claude/agents/critic.md`)
A dedicated agent that challenges plans before any implementing agent is spawned. Reads the US plan, asks "what assumptions could be wrong?", returns CRITICAL/HIGH/LOW objections. Runs in parallel with context assembly for MEDIUM/HIGH complexity US. Break-even: prevents ~1 QA bounce-back per 6 US = ~25k tokens net savings.

### 2. Evidence-Driven Verification
The "fresh output only, never assume" principle is now enforced in all verification steps. Every PASS verdict in judge.md, qa-engineer.md, and orchestrator.md requires actual terminal output shown verbatim. "Tests passed" without output is rejected.

### 3. Notepad Wisdom (`.claude/commands/notepad.md`)
Timestamped, categorized session memory under four categories: Learnings, Decisions, Issues, Problems. Captures in-session institutional knowledge before `/clear` closes the context. Gitignored, local-only (rule-011 compliant).

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

## EU AI Act Compliance Map

> **Regulation:** EU AI Act — Regulation (EU) 2024/1689, in force 1 August 2024. High-risk AI obligations (Title III) apply from August 2026.
> **GDPR:** Regulation (EU) 2016/679.
> **Classification note:** Whether this system qualifies as high-risk AI under Annex III of Reg. (EU) 2024/1689 depends on its specific deployment context and use case. This framework's controls address the requirements that would apply in a high-risk context. Actual classification requires legal review. [Cross-referenced]

---

### For CEOs and boards — the exposure

AI tools that operate without governance controls create legal and financial exposure under EU law. The EU AI Act — Regulation (EU) 2024/1689 — introduces penalties of up to €30 million or 6% of worldwide annual turnover, whichever is higher, for breaches of obligations applicable to high-risk AI systems (Art. 99(3) [[Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]). Separately, GDPR enforcement for unlawful data transfers remains active: regulators have issued penalties well above €100M for systematic violations.

This framework is a documented, auditable answer to the question "what controls do you have over your AI systems?" Every decision the AI makes is tied to a named requirement, approved by a human, and logged in append-only records. The controls are inspectable — they are text files in this repository, not black-box vendor features.

---

### For product managers and project leads — what the controls look like in practice

Each article below maps to a concrete control in this framework. The "evidence at" column tells you exactly where an auditor would look.

| Article | Requirement (summary) | This framework's control | Evidence at | Confidence |
|---|---|---|---|---|
| Art. 9 — Risk management | Maintain an ongoing risk management system appropriate to the AI system's risk class | Phase gate checkpoints at every development phase; Critic agent validates plans before delegation; circuit breaker halts AI after 2 failed attempts | `.claude/agents/critic.md`, `orchestrator.md` phase gate section, CLAUDE.md Rule 4 | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) |
| Art. 10 — Data governance | Data used for training/operation must be subject to appropriate data governance practices; no unlawful transfer outside EEA | Processing stays within Ollama (local) and Claude API (EU DPA only); no code or session data routed to unapproved providers; tenant data queries always scoped by `tenant_id` | `rule-011-eu-ai-act-data-boundary.md`, `rule-001-tenant-isolation.md` | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) |
| Art. 12 — Record-keeping | High-risk AI systems must keep logs sufficient to ensure traceability of results | Every US action logged in append-only `docs/ARCHITECTURE_STATE.md`; PostgreSQL append-only audit table in production; no mutable session files | `docs/ARCHITECTURE_STATE.md`, `backend/app/audit/`, `.claude/commands/handoff.md` | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) |
| Art. 13 — Transparency | Sufficient information about the AI system must be provided to enable informed use | This document; all agent definitions in `.claude/agents/`; all rules in `.claude/rules/`; every AI output tied to a named User Story with acceptance criteria | `docs/FRAMEWORK_README.md`, `.claude/agents/`, `.claude/rules/` | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) |
| Art. 14 — Human oversight | High-risk AI systems must be designed to allow effective human oversight; autonomous operation must include stop-and-review points | Mandatory human approval at US checkpoint, Phase Gate, and before any data-modifying action; no autonomous modes; hard rule: no self-approval | `orchestrator.md` workflow, CLAUDE.md Hard Rule 17, all agent `<hard_constraints>` blocks | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) |
| GDPR Art. 46 — Data transfers | Transfers of personal data to third countries require appropriate safeguards (SCCs, adequacy decision, or binding DPA) | Only two providers permitted: Ollama (local, no transfer) and Claude API with explicit EU Data Processing Agreement; auto-routing to other providers blocked at rule level | `rule-011-eu-ai-act-data-boundary.md`, `rejected_features` table above | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) |
| GDPR Art. 5(1)(e) — Storage limitation | Personal data kept no longer than necessary; mutable session data not retained externally | Session notes gitignored; no JSONL replay files committed or synced; `.temp_context.md` gitignored | `.gitignore`, pre-prompt hook | [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) |

---

### For security teams and DPOs — technical controls per article

**Art. 9 — Risk management system** [Reg. (EU) 2024/1689, Art. 9 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]
Implemented as a multi-layer control: (1) pre-delegation Critic agent review for MEDIUM/HIGH complexity work; (2) circuit breaker hard stop after 2 failed attempts, preventing runaway AI loops; (3) pre-prompt hook (`hooks/pre-prompt.sh`) that blocks session start if `docs/AI_REFERENCE.md` is absent (prevents uninformed AI operation); (4) `/reflexion` command at every phase gate to extract and codify new risk patterns as rules.

**Art. 10 — Data and data governance** [Reg. (EU) 2024/1689, Art. 10 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]
Provider allowlist enforced at rule level (`rule-011`): only `ollama_local` and `claude_api_eu` (with EU DPA). No code fragments, schema excerpts, or session data transmitted to Discord, Slack, Telegram, or plugin marketplaces. Multi-tenant data isolation enforced at query level: every SQLAlchemy query on tenant-owned data requires `.where(Model.tenant_id == current_user.tenant_id)` — `tenant_id` sourced from JWT, never from request body (`rule-001`). MCP tool integrations require full-schema validation (not description-only) plus allowlist check (`rule-012`).

**Art. 12 — Record-keeping** [Reg. (EU) 2024/1689, Art. 12 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]
Append-only logging enforced by command constraint: `/handoff` uses `echo >>` exclusively; the `Write` and `Edit` tools are prohibited on `docs/ARCHITECTURE_STATE.md`. PostgreSQL audit table uses `INSERT`-only access pattern. Session replay JSONL files are gitignored and never committed. Log entries include: agent identity, US identifier, timestamp, action type, acceptance criteria reference.

**Art. 13 — Transparency** [Reg. (EU) 2024/1689, Art. 13 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]
Every AI action is tied to a User Story with explicit acceptance criteria (visible to operator before execution). Agent identities, capabilities, and constraints are documented in `.claude/agents/`. The full rule set is in `.claude/rules/`. Output artifacts (handoffs, architecture state) are human-readable Markdown with provenance references.

**Art. 14 — Human oversight** [Reg. (EU) 2024/1689, Art. 14 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)]
Hard stops at: (a) US plan approval before delegation, (b) US result review before QA escalation, (c) Phase Gate before next phase begins. No autonomous mode exists — every phase transition requires explicit user confirmation. Hard Rule 17 prevents self-approval: the agent that implements a US cannot also be its verifier. All agents include `<hard_constraints>` blocks that prohibit bypassing these checkpoints.

**GDPR Art. 46 — Data transfers** [Reg. (EU) 2016/679, Art. 46 · [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679)]
Lawful basis for the Claude API transfer: Data Processing Agreement with Anthropic covering EU data residency. Ollama: local inference, no transfer. All other providers are blocked by `rule-011`. The pre-prompt hook checks for the presence of `.omc/` (oh-my-claudecode session sync directory) and exits with a warning if found, preventing accidental activation of unapproved multi-provider routing.

**Annex III — High-risk AI classification** [Reg. (EU) 2024/1689, Annex III · Cross-referenced]
Whether this system constitutes high-risk AI under Annex III depends on deployment scope (e.g. use in employment decisions, critical infrastructure, law enforcement). The above controls satisfy requirements applicable to high-risk systems and also represent security best practice for any AI-assisted development environment. Formal classification: consult your legal or DPO team.

See also: `.claude/rules/project/rule-011-eu-ai-act-data-boundary.md` (full compliance rule) and `.claude/rules/project/rule-012-mcp-trust-boundary.md` (MCP-specific controls).

---

## Token Economics

### Before (CLAUDE.md v2.2 — monolithic)
| Component | Tokens per invocation |
|---|---|
| CLAUDE.md monolith | ~8,000–12,000 tokens |
| Agent file (free-text, duplicated constraints) | ~2,000–3,000 tokens |
| Explore agents for file reading | ~60,000–131,000 tokens per session |
| Parallel agent context (uncompressed, no /clear between waves) | ~80,000 × N agents wasted |
| **Estimated session cost** | **~145,000 avoidable tokens/session** |

### After (v4.0 — oh-my-claudecode enterprise)
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

### Testing & Evaluation

**Want to evaluate this framework on your own codebase?** Start with [`docs/TESTING_AND_FEEDBACK.md`](TESTING_AND_FEEDBACK.md).

This guide includes:
- Baseline measurement checklist (token cost, quality, speed, governance metrics)
- Seven experiments to try (local Ollama vs cloud, Serena adoption, custom rules, multi-tenant edge cases, CI/CD automation, long-running projects)
- Three feedback templates for developers, security experts, and legal/DPO teams
- How framework improvements are driven by user-submitted findings

### Starting a Speed 2 Session
```bash
# The orchestrator reads these three files at session start:
cat docs/AI_REFERENCE.md         # stack reference
cat docs/backlog/BACKLOG.md      # current phase status
cat .claude/workflow.md          # phase dependency graph
```

### Local Model Providers (Ollama + LiteLLM)

The framework supports **fully local AI inference** via Ollama + LiteLLM. This satisfies GDPR Art. 46 [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) and EU AI Act Art. 10 [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689) automatically — no data processing agreements needed, no data leaves the machine.

**When to use local vs cloud:**

| Scenario | Provider |
|---|---|
| Sensitive codebase, regulated data, no Anthropic DPA | Ollama + LiteLLM (local) |
| Fastest iteration on non-sensitive code | Claude API (cloud) |
| Cost-constrained volume work (drafts, refactors) | Ollama `qwen2.5-coder:7b` |
| Best quality for complex multi-file reasoning | Claude Sonnet (cloud) or `qwen2.5-coder:32b` (local + GPU) |

**Setup:** see [`docs/AI_TOOLS_SETUP.md`](AI_TOOLS_SETUP.md) for full configuration, model recommendations, and the sandboxed Docker setup (`infra/docker-compose.ai-tools.yml`).

### Key Commands
| Command | When to use |
|---|---|
| `/init-ai-reference` | First run or after major stack change |
| `/judge US-NNN` | After implementing agent finishes, before DocWriter + QA (~2k tokens) |
| `/handoff US-NNN` | After US merged to main — appends to ARCHITECTURE_STATE.md |
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
