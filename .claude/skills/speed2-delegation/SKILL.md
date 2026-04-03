---
name: speed2-delegation
description: "Speed 2 orchestration protocol for delegating User Stories to specialist sub-agents. Encodes agent routing, rule injection, context sizing, batching, parallelism, and confidence gating. Load before any delegation decision in Phase 2 or Phase 3."
metadata:
  trigger: "When the Orchestrator (Tech Lead) delegates any US to a sub-agent, or decides whether to delegate vs. implement directly"
  type: skill
  updated: "2026-03-31"
  version: "2.0"
---

<insight>
Default: **direct implementation**. Delegation is justified only when the feature is clearly horizontal (1-3 independent domains). For vertical integration slices (4+ tightly coupled domains), direct implementation is 3-5x cheaper (Phase 2d empirical data). The question is not "which agent handles this?" but "does the coordination overhead exceed the implementation cost?"
</insight>

<why_this_matters>
Delegating a 5-domain vertical slice generates ≥2 parallel waves, compress/clear cycles, QA Mode A bounces, and synthesis overhead — often more tokens than the implementation itself. Phase 2d (US-020) confirmed this: direct Tech Lead implementation at ~73k tokens vs. estimated ~200–300k for a full delegation cycle. Wrong delegation decision = avoidable token waste and increased incident surface.
</why_this_matters>

<recognition_pattern>
**Delegate (horizontal feature — 1–3 domains):**
- US touches one primary domain (e.g., API endpoints only, or Docker only)
- Files are co-located in one specialist's territory
- Dependencies are resolved (no schema changes pending in other US)

**Implement directly (vertical integration slice — ≥4 domains):**
- US requires simultaneous edits in 4+ specialist territories (e.g., Docker + TypeScript + Python adapter + tests + docs)
- Domains are tightly coupled within the same feature — changes must be consistent across all files at once
- Delegation would require ≥2 parallel waves with compress/clear between them

**Confidence gate (before any HIGH complexity US):**
- Acceptance criteria unambiguous? (≥90% confidence → proceed)
- All dependencies resolved? (check BACKLOG.md status)
- File context sufficient? (Serena overview covers all touched modules)
- If confidence < 70% on any criterion: ask user for clarification. For MEDIUM tasks: use `ultrathink` instead of Critic agent.
</recognition_pattern>

<approach>

## S1 — Agent Routing

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

## S2 — Direct vs. Delegate Decision

**Default: direct implementation.** Delegate only when clearly justified.

| Domain count | Decision | Reason |
|---|---|---|
| 1-3 domains, independent | **Delegate** to specialist agent(s) | Clear boundaries, no cross-domain coupling |
| 4+ domains, tightly coupled | **Direct implementation** | Coordination overhead > implementation cost |

## S3 — Delegation Checklist (4 mandatory items)

Every sub-agent prompt MUST include:
1. **`<user_story>`** — full content of `docs/backlog/US-NNN.md`
2. **`<file path="...">`** — raw content of files the agent will modify (Read them first, inject as XML)
3. **Explicit model** — `claude-haiku-4-5-20251001` (LOW) or `claude-sonnet-4-6` (MEDIUM/HIGH). Never `dynamic`.
4. **Muzzle constraint** (verbatim): "CRITICAL OUTPUT CONSTRAINT: When finished, return ONLY the word DONE followed by a 1-sentence summary."

Use TodoWrite to track delegation checklist completion before spawning.

## S5 — Batching Protocol

When delegating ≥3 US in the same phase:
1. Group by domain: backend / ai-ml / frontend / infra — different domains can run in parallel.
2. Never parallelize US sharing schema, migration, or auth layer — SERIES dependencies.
3. After each parallel wave: `/consistency-check` on ALL returned outputs.
4. Mandatory compress-state before each wave (rule-010).
5. Wave ordering: security-critical US first (rule-001, rule-002). DocWriter last in each wave.

## S6 — Parallelism Rules

- Different file domains + resolved dependencies → parallel
- Same files or schema → series
- Security Engineer → always after target US, before merge
- DocWriter → after each US (Mode A) and each phase gate (Mode B)

</approach>

<example>
**Horizontal feature — delegate (Phase 2b/2c pattern):**
> US-012: Add quota enforcement to plugin API. Touches: `backend/app/quota/`, `backend/app/api/plugins.py`, `backend/tests/test_quota.py`.
> → 2 domains (Backend Dev + QA). Delegate to Backend Dev. QA Mode A after.

**Vertical integration slice — implement directly (Phase 2d pattern):**
> US-020: Plone MCP integration. Touches: `infra/docker-compose.yml`, `infra/Dockerfile.plone-mcp`, `infra/plone-mcp/src/index.ts`, `ai/mcp/servers/plone.py`, `ai/mcp/registry.py`, `backend/tests/test_plone_mcp.py`, `.env.example`, `docs/AI_REFERENCE.md`.
> → 5 domains (DevOps × 2, Frontend/TS, AIML, Backend Dev, DocWriter). Tech Lead implements directly.
</example>
