# Project Backlog — AI Orchestration Platform MVP

> Master index di tutte le User Stories. Aggiornato dal Tech Lead.
> Ultimo aggiornamento: 2026-03-27 | Post-retrospettiva Phase 1

---

## Legenda stati

| Simbolo | Stato |
|---|---|
| ✅ Done | Completata, verificata, approvata |
| 🔄 In Progress | In lavorazione |
| 📋 Backlog | Pianificata, non ancora iniziata |
| ⚠️ Blocked | Bloccata da dipendenza non risolta |
| 🔁 Needs Rework | Completata ma richiede revisione |

---

## Phase 1 — Foundation

**Obiettivo:** struttura progetto, DB, auth base, infra locale funzionante.
**Status:** ✅ Completata — Phase Gate 1 approvato (2026-03-26)
**Nota:** Residual risks documentati — vedere sezione dedicata in `docs/plan.md`

| US | Titolo | Agente | Dipendenze | Priorità | Stato | File |
|---|---|---|---|---|---|---|
| [US-001](US-001.md) | Project Scaffold | Backend Dev | — | critical | ✅ Done | [progress](../progress/US-001-done.md) |
| [US-002](US-002.md) | Database Schema | Backend Dev | US-001 | critical | ✅ Done | [progress](../progress/US-002-done.md) |
| [US-003](US-003.md) | Docker Compose Locale | DevOps/Infra | US-001 | critical | ✅ Done | [progress](../progress/US-003-done.md) |
| [US-004](US-004.md) | JWT Auth + Plone Bridge | Security Engineer | US-002 | critical | ✅ Done | [progress](../progress/US-004-done.md) |
| [US-005](US-005.md) | RBAC Middleware | Security Engineer | US-004 | critical | ✅ Done | [progress](../progress/US-005-done.md) |
| [US-006](US-006.md) | Audit Logging Service | Security Engineer | US-004 | critical | ✅ Done | [progress](../progress/US-006-done.md) |
| [US-007](US-007.md) | Test Coverage Phase 1 | QA Engineer | US-005, US-006 | high | ✅ Done | [progress](../progress/US-007-done.md) |

---

## Phase 2 — Core Platform

**Obiettivo:** plugin system, model layer, planner, MCP, RAG pipeline.
**Status:** 🔄 In Progress — Phase 2c ✅ Gate chiuso (2026-03-29), Phase 2d in avvio
**Prerequisito:** Phase Gate 1 approvato ✅

### Phase 2a — Plugin System

**Mini-gate 2a:** plugin caricabile da manifest, isolamento subprocess funzionante, test isolamento passano.

| US | Titolo | Agente | Dipendenze | Priorità | Stato | File |
|---|---|---|---|---|---|---|
| [US-010](US-010.md) | Plugin Manager: hot-plug, manifest, tenant isolation | Backend Dev | US-005 | critical | ✅ Done | [progress](../progress/US-010-done.md) |
| [US-011](US-011.md) | Plugin Runtime: subprocess isolation + resource limits | Security Engineer | US-010 | critical | ✅ Done | [progress](../progress/US-011-done.md) |

### Phase 2b — Model Layer

**Mini-gate 2b:** Ollama query funzionante nel container, Claude adapter mockato testato, generate() interface stabile.

| US | Titolo | Agente | Dipendenze | Priorità | Stato | File |
|---|---|---|---|---|---|---|
| [US-012](US-012.md) | Model Layer: Ollama + Claude adapters, generate() interface | AI/ML Engineer | US-002 | critical | ✅ Done | [progress](../progress/US-012-done.md) |
| [US-013](US-013.md) | Cost-aware Planner + multi-model fallback | AI/ML Engineer | US-012 | critical | ✅ Done | [progress](../progress/US-013-done.md) |

### Phase 2c — MCP + RAG

**Mini-gate 2c:** RAG query ritorna risultati con source attribution, MCP trust scoring filtra correttamente, nessun prompt injection.

| US | Titolo | Agente | Dipendenze | Priorità | Stato | File |
|---|---|---|---|---|---|---|
| [US-014](US-014.md) | MCP Registry + trust scoring | AI/ML Engineer | US-005 | high | ✅ Done | [progress](../progress/US-014-done.md) |
| [US-015](US-015.md) | Context Builder: MCP query, filter, source attribution | AI/ML Engineer | US-014 | high | ✅ Done | [progress](../progress/US-015-done.md) |
| [US-016](US-016.md) | RAG Pipeline: Qdrant embeddings + retrieval | AI/ML Engineer | US-014 | high | ✅ Done | [progress](../progress/US-016-done.md) |

### Phase 2d — Quota, Planner Integration, Review + Tests

**Mini-gate 2d:** rate limiting funzionante, quota tracking in DB, planner seleziona modello corretto, test suite verde.

| US | Titolo | Agente | Dipendenze | Priorità | Stato | File |
|---|---|---|---|---|---|---|
| [US-017](US-017.md) | Token Quota Tracking + Rate Limiting (Redis) | Backend Dev | US-012 | high | ✅ Done | [progress](../progress/US-017-done.md) |
| [US-018](US-018.md) | Security Review: plugin isolation + MCP sanitization | Security Engineer | US-011, US-015 | critical | ✅ Done | [progress](../progress/US-018-done.md) |
| [US-019](US-019.md) | Test Coverage Phase 2: planner, MCP, RAG, plugin lifecycle | QA Engineer | US-013, US-016, US-018 | high | 📋 Backlog | — |

---

## Phase 3 — API & Frontend

**Obiettivo:** API REST completa, UI Volto funzionante, flussi tenant-aware end-to-end.
**Status:** 📋 Backlog — non iniziata
**Prerequisito:** Phase Gate 2 approvato

| US | Titolo | Agente | Dipendenze | Priorità | Stato |
|---|---|---|---|---|---|
| US-020 | API REST: query endpoint (planner + context) | Backend Dev | US-013, US-015 | critical | 📋 Backlog |
| US-021 | API REST: plugin management endpoints | Backend Dev | US-010 | high | 📋 Backlog |
| US-022 | API REST: tenant admin (quota, user management) | Backend Dev | US-017 | high | 📋 Backlog |
| US-023 | Frontend scaffold: Volto addon + routing + auth client | Frontend Dev | US-004 | critical | 📋 Backlog |
| US-024 | Frontend: login/token flow, RBAC-aware navigation | Frontend Dev | US-023 | critical | 📋 Backlog |
| US-025 | Frontend: query UI con source attribution e confidence | Frontend Dev | US-024, US-020 | critical | 📋 Backlog |
| US-026 | Frontend: plugin management panel (per tenant admin) | Frontend Dev | US-024, US-021 | medium | 📋 Backlog |
| US-027 | Response format: source, confidence, fallback indication | Backend Dev | US-020 | high | 📋 Backlog |
| US-028 | Security Review: API endpoints, input validation, output format | Security Engineer | US-020–022, US-027 | critical | 📋 Backlog |
| US-029 | E2E test: flusso completo query → risposta con attribution | QA Engineer | US-025, US-028 | high | 📋 Backlog |

---

## Phase 4 — Production Infra

**Obiettivo:** Docker hardening, CI/CD, K8s (roadmap), secrets management.
**Status:** 📋 Backlog — non iniziata
**Prerequisito:** Phase Gate 3 approvato
**Nota MVP:** K8s manifest sono placeholder per roadmap enterprise. L'MVP gira su Docker Compose.

| US | Titolo | Agente | Dipendenze | Priorità | Stato |
|---|---|---|---|---|---|
| US-030 | Docker hardening: non-root, health checks, resource limits | DevOps/Infra | US-003 | critical | 📋 Backlog |
| US-031 | CI/CD pipeline: build → test → deploy | DevOps/Infra | US-030 | high | 📋 Backlog |
| US-032 | Secrets management: env injection, no secrets in code | Security Engineer | US-030 | critical | 📋 Backlog |
| US-033 | K8s manifests (placeholder): tutti i services | DevOps/Infra | US-030 | medium | 📋 Backlog |
| US-034 | Docker security policies + hardening finale | Security Engineer | US-032 | high | 📋 Backlog |
| US-035 | Load + smoke test su staging | QA Engineer | US-031, US-034 | high | 📋 Backlog |

---

## Residual Risks da Phase 1

Issues aperti da risolvere prima o durante Phase 2:

| Rischio | Severità | Owner | Risoluzione prevista |
|---|---|---|---|
| Audit log non integrato con auth events (US-004/005 → AuditService) | HIGH | Security Engineer | US-018 |
| DB role REVOKE UPDATE/DELETE su audit_logs (non in migration) | CRITICAL | DevOps/Infra | US-030 (runbook) |
| Plone restapi version compatibility non verificata | HIGH | DevOps/Infra | Pre-avvio Phase 2 (`make up` + verifica) |
| Refresh token rotation non implementata | HIGH | Security Engineer | US-018 review |
| Real PostgreSQL integration tests mancanti | MEDIUM | QA Engineer | US-019 |

---

## Come usare questo backlog

- **Tech Lead**: aggiorna lo stato di ogni US qui e nel file individuale quando deleghi o ricevi completion
- **Agenti**: non modificano questo file — scrivono in `docs/progress/US-NNN-done.md` e `docs/handoffs/US-NNN-handoff.md`
- **Utente**: questo file è il punto di riferimento per la visibilità sul progresso
- **Git**: ogni modifica di stato è un commit separato → storia versionabile
