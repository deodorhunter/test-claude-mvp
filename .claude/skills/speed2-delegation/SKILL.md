# Speed 2 Delegation Protocol

> Loaded on-demand when the orchestrator delegates US to sub-agents.

## Agent Routing

| Domain | Agent |
|---|---|
| API endpoints, DB models, quota, rate limiting | Backend Dev |
| React/Volto UI, auth flows in browser | Frontend Dev |
| Docker, CI/CD, secrets | DevOps/Infra |
| Unit, integration, E2E tests | QA Engineer |
| MCP, RAG, Qdrant, planner, model layer | AI/ML Engineer |
| Auth/RBAC, plugin isolation, audit logging, MCP security review | Security Engineer |
| Handoff docs, architecture docs, runbooks | DocWriter |
| Plan/design challenge and validation | Critic |
| Speed 1 bug fixes, targeted single-file errors | Debugger |

## Agent-Scoped Rule Injection (S3)

Inject ONLY the rules relevant to that agent type as inline `<rules>` XML. Do NOT rely on system-prompt inheritance.

| Agent | Rules to inject |
|---|---|
| Backend Dev | 001 (tenant), 002 (migration) |
| AI/ML Engineer | 001 (tenant), 011 (EU boundary), 012 (MCP trust) |
| Security Engineer | 001 (tenant), 011 (EU boundary), 012 (MCP trust) |
| DevOps/Infra | 008 (docker fix) |
| DocWriter | 005 (no bash -c) |
| QA Engineer | 005 (no bash -c), 006 (no QA subagents) |
| Frontend Dev | 001 (tenant) |
| Critic | none (read-only) |

## Context Injection Decision (S4)

Default: **symbols-only injection**. Full file requires justification.

| Condition | Injection type | Size |
|---|---|---|
| Agent will **modify** the file | `<file path="...">full content</file>` | 100% |
| Agent will **call into / reference** the file | `<symbols path="...">serena overview</symbols>` | ~10% |
| Agent needs **types/interfaces only** | `<interface path="...">signatures</interface>` | ~5% |

Always run `serena__get_symbols_overview` first. Inject `<file>` only when the file will be edited.

## Batching Protocol

When delegating ≥3 US in the same phase:
1. Group by domain: backend / ai-ml / frontend / infra — different domains can run in parallel.
2. Never parallelize US sharing schema, migration, or auth layer — SERIES dependencies.
3. After each parallel wave: `/consistency-check` on ALL returned outputs.
4. Mandatory compress-state before each wave (rule-010).
5. Wave ordering: security-critical US first (rule-001, rule-002). DocWriter last in each wave.

## Parallelism Rules

- Different file domains + resolved dependencies → parallel
- Same files or schema → series
- Security Engineer → always after target US, before merge
- DocWriter → after each US (Mode A) and each phase gate (Mode B)

## Confidence Gating (pre-delegation check)

Before delegating any HIGH complexity US, assess:
1. Are acceptance criteria unambiguous? (≥90% confidence → proceed)
2. Are all dependencies resolved? (check BACKLOG.md status)
3. Is file context sufficient? (Serena overview covers all touched modules)

If confidence < 70% on any criterion: ask user for clarification instead of delegating.
For MEDIUM tasks: use `ultrathink` instead of Critic agent.
