# Technical Plan — AI Orchestration Platform MVP

> Last updated: 2026-03-31 | Post-retrospettiva Phase 2
> Phase 1: ✅ Completata | Phase 2: ✅ Completata (Gate 2026-03-31) | Phase 3: 📋 Backlog

---

## Architecture Overview

Multi-tenant AI orchestration platform. Backend: Python/FastAPI. Frontend: Volto addon on Plone 6. AI: LlamaIndex + Qdrant + Ollama/Claude. Infra: Docker Compose (MVP) / K8s (roadmap).

### Key Architecture Decisions

**ADR-001: Plone Auth Bridge**
Platform does NOT replicate Plone's user store. Flow:
1. Volto logs in to Plone → Plone token
2. Volto calls `POST /api/v1/auth/plone-login` with Plone token
3. `PloneIdentityAdapter` verifies via Plone `GET /@users/@current` → extracts roles
4. Platform issues own JWT as `httpOnly` cookie (`ai_platform_token`)
5. JWT payload: `{sub, tenant_id, roles: [plone_roles], plone_user, exp, iss}`

**ADR-002: Plugin Isolation (MVP)**
Subprocess with resource limits (resource module, 10s timeout). JSON over stdin/stdout. Pool per `(tenant_id, plugin_name)`. Network blocked except `plone_integration`.

**ADR-003: RAG Tenancy**
Each tenant = dedicated Qdrant collection `tenant_{tenant_id}`. `tenant_id` comes ONLY from verified JWT, never from request body.

**ADR-004: Token Quota**
Two layers: Redis (rate limit, 60s window, sub-ms) + PostgreSQL (monthly quota, durable). Both checked before every model call.

**ADR-005: AI Response Format**
```json
{"response": "...", "sources": [{"source": "...", "confidence": 0.95}], "model_used": "...", "fallback": false, "tokens_used": 1240}
```

**ADR-006: AI Provider Scope (MVP)**
Ollama (demo mode, locale nel container) + Claude API (demo-api mode, con API key). GitHub Copilot e altri provider: mockati, non implementati. Modalità configurata via `AI_MODE` in `.env`.

**ADR-007: K8s scope**
K8s manifest sono placeholder per roadmap enterprise. L'MVP demo gira su Docker Compose. Nessuna dipendenza K8s per il Phase Gate.

### Cross-Cutting Rules

| Concern | Rule |
|---|---|
| Auth | `tenant_id` / `user_id` from verified JWT ONLY, never request body |
| Multitenancy | All DB queries filtered by `tenant_id`. Redis keys: `tenant_id:user_id:*`. Qdrant: `tenant_{id}` |
| Audit log | Append-only. No UPDATE/DELETE grant. `MODEL_QUERY` entries must include `metadata.sources` |
| Schema | Only Backend Dev creates Alembic migrations |
| Smoke test | Obbligatorio dopo ogni US prima di procedere — Tech Lead lo esegue |
| Blocker | Segnalato dall'agente → registrato in backlog US → analizzato dal Tech Lead → utente notificato se critico |

---

## Phase Dependency Graph

```
US-001 (scaffold) → US-002 (schema) + US-003 (docker) [parallel]
                          ↓
                   US-004 (JWT/Plone auth)
                     ↓              ↓
           US-005 (RBAC)    US-006 (audit log) [parallel]
                          ↓
                   US-007 (QA) → [PHASE GATE 1 ✅]
                          ↓
         Phase 2a: US-010 → US-011
                          ↓ [mini-gate 2a]
         Phase 2b: US-012 → US-013
                  (US-012 parallelo con US-010)
                          ↓ [mini-gate 2b]
         Phase 2c: US-014 → US-015 + US-016 [parallel]
                  (US-014 parallelo con US-012)
                          ↓ [mini-gate 2c]
         Phase 2d: US-017 + US-018 → US-019
                          ↓ [PHASE GATE 2]
         US-020–029 (API & Frontend) → [PHASE GATE 3]
                          ↓
         US-030–035 (Production Infra) → [PHASE GATE 4 = MVP Done]
```

---

## Phase 1 — Foundation ✅

| US | Title | Agent | Status |
|---|---|---|---|
| US-001 | Project Scaffold | Backend Dev | ✅ Done |
| US-002 | Database Schema | Backend Dev | ✅ Done |
| US-003 | Docker Compose Local | DevOps/Infra | ✅ Done |
| US-004 | JWT Auth + Plone Bridge | Security Engineer | ✅ Done |
| US-005 | RBAC Middleware | Security Engineer | ✅ Done |
| US-006 | Audit Logging Service | Security Engineer | ✅ Done |
| US-007 | Test Coverage | QA Engineer | ✅ Done |

### Residual Risks da Phase 1 (da risolvere)

| Rischio | Severità | Owner | Quando |
|---|---|---|---|
| Audit log non integrato con auth events (US-004/005) | HIGH | Security Engineer | US-018 |
| DB role REVOKE UPDATE/DELETE su audit_logs mancante | CRITICAL | DevOps/Infra | US-030 (runbook) |
| Plone restapi version compatibility non verificata | HIGH | Tech Lead + DevOps | Pre-avvio Phase 2 |
| Refresh token rotation non implementata | HIGH | Security Engineer | US-018 |
| Integration test con PostgreSQL reale mancanti | MEDIUM | QA Engineer | US-019 |

> ⚠️ **Prima di avviare Phase 2**: eseguire `make up` e verificare manualmente che Plone risponda su porta 8080. Se fallisce, bloccare Phase 2 e risolvere.

---

## Phase 2 — Core Platform 📋

**Backlog completo:** vedere `docs/backlog/` (US-010 through US-019)

### Phase 2a — Plugin System

**US:** US-010 (Backend Dev) → US-011 (Security Engineer)
**Serie:** obbligatorio (US-011 dipende da US-010)
**Deliverable:** Plugin caricabile, manifest validato, subprocess isolation testata

### Phase 2b — Model Layer

**US:** US-012 (AI/ML Engineer) → US-013 (AI/ML Engineer)
**Parallelo con:** Phase 2a (file domain diverso)
**Deliverable:** Ollama adapter funzionante, Claude adapter mockato, planner operativo

**Nota:** US-012 aggiorna il workflow da "Claude + Copilot" a "Ollama + Claude" per allineamento con ADR-006.

### Phase 2c — MCP + RAG

**US:** US-014 → US-015 + US-016 (AI/ML Engineer, US-015/016 parallel)
**Dipendenza:** US-014 deve essere done prima di US-015 e US-016
**Deliverable:** RAG query con source attribution, MCP trust scoring, sanitization prompt injection

### Phase 2d — Quota + Security Review + Tests

**US:** US-017 (Backend Dev, parallelo con 2b/2c) → US-018 (Security Engineer) → US-019 (QA Engineer)
**Deliverable:** Rate limiting + quota enforcement, audit log integrato, test coverage ≥ 80%

### Phase 2 Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Ollama container startup lento (model download) | HIGH | Pre-scaricare il modello nel Dockerfile; health check ritardato |
| Qdrant collection isolation test | HIGH | Verificare cross-tenant in US-016 con test esplicito |
| MCP output sanitization incompleta | HIGH | US-015 + review US-018 — pattern injection lista aggiornata |
| Plugin subprocess non supportato su alcune piattaforme | MEDIUM | Fallback graceful + errore chiaro; documentare limitazioni |

---

## Phase 3 — API & Frontend 📋

Da pianificare in dettaglio dopo Phase Gate 2. Verrà coperta da US-020 through US-029.

**Demo scenarios da verificare in Phase 3:**
1. Plone user in Volto chatters con agente che costruisce blocchi in una Page
2. Plone user in Volto chatters per help RAG su documentazione sito
3. Plone user in Volto uploada documento → agente costruisce Page con contenuto

---

## Phase 4 — Production Infra 📋

Da pianificare dopo Phase Gate 3. Coperta da US-030 through US-035.
Docker hardening, CI/CD, secrets management. K8s manifest come placeholder roadmap.

---

## Top Risks Globali

| Risk | Severity | Mitigation |
|---|---|---|
| Plone REST API version mismatch | HIGH | Pin plone.restapi; verifica `make up` prima di Phase 2 |
| Volto auth intercept fragility | HIGH | Pin Volto version; E2E test in US-029 |
| Cross-tenant Qdrant leak | HIGH | `qdrant_store.py` accetta tenant_id SOLO da JWT; test esplicito US-016 |
| Alembic migration conflicts | MEDIUM | Solo Backend Dev crea migrations |
| Incomplete audit for EU AI Act | MEDIUM | MODEL_QUERY logs devono includere metadata.sources — verificato in US-018 |
| Ollama model download at startup | HIGH | Pre-pull in Dockerfile; health check after model ready |

---

## Phase 3a — Token Optimization & Model Routing ✅ COMPLETE

**Completed:** 2026-04-02 | Mini-gate: Archive rules + Model routing matrix + Orchestration guide
**US:** US-050 ✅ + US-051 ✅ + US-053 ✅ (all Done)
**Cost:** ~102k tokens | Avoidable waste: ~20k (file injection bloat)
**Rule extracted:** rule-019 (Serena-git isolation for worktrees)

---

## Phase 3b — Automation & Cognitive Tooling 📋

**Objective:** Implement automation for context management, document verification, and cognitive patterns. Foundation for Phase 3c (adoption & DX).

**Mini-gate 3b Checklist:**
- [ ] Cognitive patterns documented (US-054)
- [ ] Doc verification CI passes (US-055)
- [ ] Context compression automation hooked (US-056)

### Sprint Structure

**Wave 1 (Parallel — No Dependencies):**
- US-054 (Doc Writer, HIGH, Haiku): Cognitive patterns docs — learn/judge/notepad/reflexion/deep-interview patterns, automation potential, token costs
- US-055 (QA Engineer, HIGH, Haiku): Doc verification CI (`make verify-docs`) — bash script, link checker, port validator, US file existence checker
- US-066 (DevOps/Infra, MEDIUM, Sonnet): Serena MCP .git/ ignore config — implements rule-019; Serena settings.json update + docs

**Wave 2 (Sequential — After Wave 1):**
- US-056 (AI/ML Engineer, MEDIUM, Sonnet): Automated context compression hook — rule-010 automation; configurable threshold; fallback to manual /compress-state
- US-067 (Doc Writer, MEDIUM, Haiku): Optimize file context injection — symbol overviews per rule-009; ~10k token savings per doc phase
- US-068 (Product Owner, MEDIUM, Haiku, depends on US-054): Pre-collect command metadata — docs/.command-catalog.md reference; reusable across phases

### Cost Estimate

| Wave | Estimate | Notes |
|---|---|---|
| Wave 1 (parallel) | ~60k tokens | US-054: ~20k; US-055: ~15k; US-066: ~25k (Sonnet) |
| Wave 2 (sequential) | ~50k tokens | US-056: ~20k; US-067: ~15k; US-068: ~15k |
| **Total Phase 3b** | **~110k tokens** | 4× Haiku + 2× Sonnet |

### Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| US-056 hook API research: May not support all trigger types | MEDIUM | US-056 task 1: Research first. Fallback: manual /compress-state still works. |
| US-055 CI timeout on large repos | LOW | Keep script <30s; use HEAD requests only (no full downloads). |
| US-068 blocked by US-054 completion | LOW | US-054 high priority Wave 1; US-068 Wave 2 after ~4 days. |

### Files Expected

```
docs/COGNITIVE_PATTERNS.md (new)
benchmark/verify-docs.sh (new)
Makefile (add verify-docs target)
.claude/settings.json (Serena ignored_paths)
.claude/hooks/auto-compress.sh (new, conditional)
.claude/agents/doc-writer.md (symbol-based context guidance)
docs/AI_REFERENCE.md (Context Management section)
docs/.command-catalog.md (new reference)
```

