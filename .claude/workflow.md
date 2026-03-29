# MVP Workflow

> Fasi da seguire in ordine. Il Tech Lead NON passa alla fase successiva senza approvazione esplicita dell'utente.
> Aggiornato post-retrospettiva Phase 1: sub-fasi atomiche, mini-gate, smoke test obbligatori.
> Aggiornato 2026-03-27 post retrospettiva Phase 2a: git branching per US + manual test instructions obbligatorie.
> Aggiornato 2026-03-27 token optimization overhaul: context injection protocol, git diff for QA/DocWriter, no-exploration constraints.
> Aggiornato 2026-03-29: YAML frontmatter on agents/commands, ultrathink for HIGH complexity, proactive context budget, destructive/non-destructive parallelism classification, Consolidate→/clear→Action pattern.

## Parallelism Classification (mandatory before spawning parallel agents)

Before spawning any parallel sub-agents, the Tech Lead MUST classify each task:

| Classification | Definition | Safe to parallelize? |
|---|---|---|
| **Non-destructive** | Reads, analysis, research, review tasks. Does not modify shared files. | ✅ Yes — parallelize aggressively |
| **Destructive** | Writes to files. May modify shared schema, config, or shared test fixtures. | ⚠️ Only if domains are strictly isolated |

**Decision flow:**
```
Is the task destructive?
  NO  → Spawn freely in parallel (research, review, QA analysis)
  YES → Do the agents own different, non-overlapping file domains?
         YES → Parallel OK (e.g. Backend on api/v1/ + Frontend on frontend/src/)
         NO  → Must run in series (e.g. two agents touching backend/app/db/)
```

**Before a destructive parallel wave:** enter Plan Mode or describe the parallel plan to confirm no file domain overlap.

## Consolidate → /compress-state → /clear → Action (between parallel waves)

When a parallel wave of 2+ agents completes, **do not chain immediately to the next step**:

```
❌ WRONG:  [Agent A done] → [Agent B done] → [review both] → [start Phase 2c]
✅ RIGHT:  [Agent A done] [Agent B done] → collect both results
                                        → /compress-state
                                        → user types /clear
                                        → fresh context → review consolidated results
                                        → proceed to Phase 2c
```

**Why:** Parallel agent results pollute each other's context. The Tech Lead's context fills with two concurrent execution threads, leading to confusion about which changes belong to which US. A clear break between waves costs ~30 seconds and saves thousands of tokens in confused reasoning.

## Git Branching Strategy

- Ogni US ha il proprio branch: `us/US-NNN-short-title` (es. `us/US-010-plugin-manager`)
- Il branch viene creato dal Tech Lead **prima** di delegare la US all'agente
- L'agente committa sul branch della US
- Dopo smoke test + QA validation + approvazione utente: merge su `main`
- Nessun commit diretto su `main` durante lo sviluppo di una US

## QA Engineer — Ruolo Per-US (Mode A)

Il QA Engineer viene spawnato **dopo ogni US**, non solo a fine fase. Esegue i comandi di test manuale dall'handoff doc contro l'ambiente Docker live.

- **Modello:** `claude-haiku-4-5-20251001` (task semplice: run commands, compare output)
- **Context injection (mandatory):** Tech Lead MUST inject BOTH:
  1. `git diff main...HEAD` as `<git_diff>` XML
  2. full content of `docs/handoffs/US-NNN-handoff.md` as `<handoff_doc>` XML
- **Output:** pass/fail report con output reale vs atteso
- **Se fail — routing obbligatorio:**
  - Bug applicativo (output errato, feature mancante) → ri-delega all'**agente implementatore**
  - Errore infrastrutturale (mount mancante, env var, porta, container) → ri-delega a **DevOps/Infra**
  - NON presentare all'utente finché QA non passa
- **Se pass:** Tech Lead presenta QA pass report + comandi manuali dall'handoff all'utente per verifica finale

Questo intercetta errori di integrazione (es. path non montati, env vars mancanti) prima che l'utente debba testare manualmente.

---

## FASE 1 — Foundation (completata)

**Obiettivo:** struttura progetto, DB, auth base, infra locale funzionante.
**Status:** ✅ Completata — Phase Gate 1 approvato (2026-03-26)

| US | Titolo | Agente | Dipendenze | Stato |
|---|---|---|---|---|
| US-001 | Project scaffold (Python backend + TS frontend) | Backend Dev | nessuna | ✅ Done |
| US-002 | Database schema: tenants, users, plugins, quota | Backend Dev | US-001 | ✅ Done |
| US-003 | Docker Compose locale (Postgres, Redis, Qdrant, Plone, Volto) | DevOps/Infra | US-001 | ✅ Done |
| US-004 | JWT auth + Plone bridge + refresh token | Security Engineer | US-002 | ✅ Done |
| US-005 | RBAC middleware: permission enforcement per tenant | Security Engineer | US-004 | ✅ Done |
| US-006 | Audit logging service | Security Engineer | US-004 | ✅ Done |
| US-007 | Test coverage: auth + RBAC + schema | QA Engineer | US-005, US-006 | ✅ Done |

**Residual risks aperti:** vedere `docs/backlog/BACKLOG.md` sezione "Residual Risks da Phase 1".

---

## FASE 2 — Core Platform

**Obiettivo:** plugin system, model layer, planner, MCP, RAG pipeline.
**Status:** 📋 Backlog — in attesa di approvazione avvio Phase 2
**Prerequisito:** Phase Gate 1 approvato ✅

Phase 2 è divisa in **4 sub-fasi atomiche**, ciascuna con mini-gate e approvazione utente.

---

### Phase 2a — Plugin System

**Obiettivo:** plugin manager funzionante, subprocess isolation, tenant isolation verificata.

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-010 | Plugin manager: hot-plug, manifest, tenant isolation | Backend Dev | US-005 | — | 📋 Backlog |
| US-011 | Plugin runtime: subprocess isolation + resource limits | Security Engineer | US-010 | serie dopo US-010 | 📋 Backlog |

**Smoke test post US-010:**
```bash
make test backend/tests/test_plugin_manager.py  # tutti verdi
# Verificare che manifest.yaml venga caricato: check logs
```

**Smoke test post US-011:**
```bash
make test backend/tests/test_plugin_runtime.py  # tutti verdi
# Verificare timeout enforcement: check test output
```

**Mini-gate 2a:**
- [ ] Plugin caricabile da manifest YAML
- [ ] Enable/disable per tenant funzionante (no restart)
- [ ] Subprocess isolation verificata: cross-tenant test passa
- [ ] Timeout 10s enforcement testato
- [ ] Approvazione utente → avviare Phase 2b

---

### Phase 2b — Model Layer

**Obiettivo:** Ollama adapter funzionante nel container, Claude adapter testato con mock, interfaccia generate() stabile.

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-012 | Model layer: Ollama + Claude adapters, generate() interface | AI/ML Engineer | US-002 | parallelo con US-010 | 📋 Backlog |
| US-013 | Cost-aware planner + multi-model fallback | AI/ML Engineer | US-012 | serie dopo US-012 | 📋 Backlog |

**Nota MVP:** US-012 implementa Ollama (demo mode) e Claude API (demo-api mode). GitHub Copilot è rimosso dall'MVP.

**Smoke test post US-012:**
```bash
make test backend/tests/test_models.py          # tutti verdi
# Verifica manuale Ollama (se make up è attivo):
# docker exec -it <api-container> python -c "from ai.models.factory import get_model_adapter; ..."
```

**Smoke test post US-013:**
```bash
make test backend/tests/test_planner.py         # tutti verdi
```

**Mini-gate 2b:**
- [ ] `OllamaAdapter.generate()` funzionante (integrazione container Ollama)
- [ ] `ClaudeAdapter.generate()` testato con mock (nessuna chiamata reale)
- [ ] Planner seleziona modello corretto in base a quota e disponibilità
- [ ] Fallback Ollama → Claude funzionante (con mock)
- [ ] Approvazione utente → avviare Phase 2c

---

### Phase 2c — MCP + RAG

**Obiettivo:** RAG query con source attribution, MCP trust scoring, sanitizzazione prompt injection.

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-014 | MCP Registry + trust scoring | AI/ML Engineer | US-005 | parallelo con US-012 | 📋 Backlog |
| US-015 | Context builder: MCP query, filter, source attribution | AI/ML Engineer | US-014 | serie dopo US-014 | 📋 Backlog |
| US-016 | RAG pipeline: Qdrant embeddings + retrieval | AI/ML Engineer | US-014 | parallelo con US-015 | 📋 Backlog |

**Smoke test post US-014:**
```bash
make test backend/tests/test_mcp.py             # tutti verdi
```

**Smoke test post US-015:**
```bash
make test backend/tests/test_context_builder.py # tutti verdi
# Verificare formato output: [Fonte: X | confidence: Y]
```

**Smoke test post US-016:**
```bash
make test backend/tests/test_rag.py             # tutti verdi
# Verificare che Qdrant risponda: curl http://localhost:6333/health
```

**Mini-gate 2c:**
- [ ] RAG query ritorna risultati con source attribution formattata
- [ ] MCP trust scoring filtra risultati sotto soglia
- [ ] Prompt injection patterns bloccati (test dimostrano)
- [ ] Cross-tenant isolation RAG testata (documento tenant A non appare in search tenant B)
- [ ] Approvazione utente → avviare Phase 2d

---

### Phase 2d — Quota, Planner Integration, Security Review, Tests

**Obiettivo:** rate limiting funzionante, audit log completo, security review Phase 2, test coverage ≥ 80%.

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-017 | Token quota tracking + rate limiting (Redis) | Backend Dev | US-012 | parallelo con US-013 | 📋 Backlog |
| US-018 | Security review: plugin isolation + MCP sanitization + audit integration | Security Engineer | US-011, US-015 | dopo US-011+015 | 📋 Backlog |
| US-019 | Test coverage Phase 2: planner, MCP, RAG, plugin lifecycle | QA Engineer | US-013, US-016, US-018 | dopo tutto sopra | 📋 Backlog |

**Smoke test post US-017:**
```bash
make test backend/tests/test_quota.py           # tutti verdi
# Verificare Redis: docker exec <redis> redis-cli ping → PONG
```

**Smoke test post US-018:**
```bash
make test backend/tests/test_security_review.py # tutti verdi
# Verificare audit log entries: docker exec <postgres> psql -U ... -c "SELECT * FROM audit_logs LIMIT 5"
```

**Smoke test post US-019:**
```bash
make test                                        # TUTTI i test del progetto verdi
# Coverage report: make coverage (output in terminal)
```

**Mini-gate 2d (= Phase Gate 2):**
- [ ] Rate limiting blocca richieste in eccesso
- [ ] Quota mensile enforced (tenant senza quota → 429)
- [ ] Audit log integrato: login, denial, quota_exceeded, mcp_query, model_query
- [ ] Refresh token rotation implementata
- [ ] Test suite completa: ≥ 80% coverage su moduli Phase 2
- [ ] Full Service Verification (vedi CLAUDE.md) eseguita e passata

**Phase Gate 2:**
```
make down && make up && make migrate
# Attendi 30s
curl http://localhost:8000/health    → 200
curl http://localhost:8080            → Plone up
curl http://localhost:6333/health    → Qdrant up
make test                             → tutti verdi
make logs | grep -i error             → nessun errore critico
```

QA sign-off ✅ + Security sign-off ✅ → presentare summary all'utente → approvazione → DocWriter Mode B

---

## FASE 3 — API & Frontend

**Obiettivo:** API REST completa, UI Volto funzionante, flussi tenant-aware end-to-end.
**Status:** 📋 Backlog — non iniziata
**Prerequisito:** Phase Gate 2 approvato

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-020 | API REST: query endpoint (assembla contesto, esegue planner) | Backend Dev | US-013, US-015 | — | 📋 Backlog |
| US-021 | API REST: plugin management endpoints (enable/disable) | Backend Dev | US-010 | parallelo con US-020 | 📋 Backlog |
| US-022 | API REST: tenant admin (quota, user management) | Backend Dev | US-017 | parallelo con US-020 | 📋 Backlog |
| US-023 | Frontend scaffold: Volto addon + routing + auth client | Frontend Dev | US-004 | parallelo con US-020 | 📋 Backlog |
| US-024 | Frontend: login/token flow, RBAC-aware navigation | Frontend Dev | US-023 | serie dopo US-023 | 📋 Backlog |
| US-025 | Frontend: query UI con source attribution e confidence | Frontend Dev | US-024, US-020 | serie dopo US-024+020 | 📋 Backlog |
| US-026 | Frontend: plugin management panel (per tenant admin) | Frontend Dev | US-024, US-021 | serie dopo US-024+021 | 📋 Backlog |
| US-027 | Response format: source, confidence, fallback indication | Backend Dev | US-020 | serie dopo US-020 | 📋 Backlog |
| US-028 | Security review: API endpoints, input validation, output format | Security Engineer | US-020–022, US-027 | dopo US-020–027 | 📋 Backlog |
| US-029 | E2E test: flusso completo query → risposta con attribution | QA Engineer | US-025, US-028 | dopo tutto sopra | 📋 Backlog |

**Phase Gate 3:** API completa, UI Volto funzionante end-to-end, demo scenario 1 (block builder) testato manualmente. QA + Security sign-off.

---

## FASE 4 — Production Infra

**Obiettivo:** Docker hardening, CI/CD, secrets management. K8s manifest come placeholder roadmap.
**Status:** 📋 Backlog — non iniziata
**Prerequisito:** Phase Gate 3 approvato
**Nota MVP:** K8s non è in scope per il demo MVP. US-033 produce placeholder per roadmap.

| US | Titolo | Agente | Dipendenze | Parallelismo | Stato |
|---|---|---|---|---|---|
| US-030 | Docker hardening: non-root, health checks, resource limits | DevOps/Infra | US-003 | — | 📋 Backlog |
| US-031 | CI/CD pipeline: build → test → deploy | DevOps/Infra | US-030 | parallelo con US-032 | 📋 Backlog |
| US-032 | Secrets management: env injection completo, no secrets in code | Security Engineer | US-030 | parallelo con US-031 | 📋 Backlog |
| US-033 | K8s manifests (placeholder roadmap) | DevOps/Infra | US-030 | parallelo con US-031 | 📋 Backlog |
| US-034 | Docker security policies + hardening finale | Security Engineer | US-032 | serie dopo US-032 | 📋 Backlog |
| US-035 | Load + smoke test su staging | QA Engineer | US-031, US-034 | dopo US-031+034 | 📋 Backlog |

**Phase Gate 4 (MVP Done):** deploy su Docker Compose staging funzionante, tutti i test verdi, i 3 demo scenario dimostrabili. Approvazione finale.
