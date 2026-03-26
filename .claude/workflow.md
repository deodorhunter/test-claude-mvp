# MVP Workflow

> Fasi da seguire in ordine. Il Tech Lead NON passa alla fase successiva senza approvazione esplicita dell'utente.

---

## FASE 1 — Foundation (tutto bloccante per le fasi successive)

**Obiettivo:** struttura progetto, DB, auth base, infra locale funzionante.

| US | Titolo | Agente | Dipendenze | Parallelismo |
|---|---|---|---|---|
| US-001 | Project scaffold (Python backend + TS frontend) | Backend Dev | nessuna | — |
| US-002 | Database schema: tenants, users, plugins, quota | Backend Dev | US-001 | serie dopo US-001 |
| US-003 | Docker Compose locale (Postgres, Redis, Qdrant, API) | DevOps/Infra | US-001 | parallelo con US-002 |
| US-004 | JWT auth + refresh token (backend) | Security Engineer | US-002 | serie dopo US-002 |
| US-005 | RBAC middleware: permission enforcement per tenant | Security Engineer | US-004 | serie dopo US-004 |
| US-006 | Audit logging service | Security Engineer | US-004 | parallelo con US-005 |
| US-007 | Test coverage: auth + RBAC + schema | QA Engineer | US-005, US-006 | dopo US-005+006 |

**Phase Gate 1:** schema stabile, auth funzionante, RBAC enforced, Docker locale up. QA + Security sign-off richiesti.

---

## FASE 2 — Core Platform (features principali)

**Obiettivo:** plugin system, model layer, planner, MCP, RAG pipeline.

| US | Titolo | Agente | Dipendenze | Parallelismo |
|---|---|---|---|---|
| US-010 | Plugin manager: hot-plug, manifest, tenant isolation | Backend Dev | US-005 | — |
| US-011 | Plugin runtime: subprocess isolation + resource limits | Security Engineer | US-010 | serie dopo US-010 |
| US-012 | Model layer: Claude + Copilot adapters, generate() interface | AI/ML Engineer | US-002 | parallelo con US-010 |
| US-013 | Cost-aware planner + multi-model fallback | AI/ML Engineer | US-012 | serie dopo US-012 |
| US-014 | MCP Registry + trust scoring | AI/ML Engineer | US-005 | parallelo con US-012 |
| US-015 | Context builder: MCP query, filter, source attribution | AI/ML Engineer | US-014 | serie dopo US-014 |
| US-016 | RAG pipeline: Qdrant embeddings + retrieval | AI/ML Engineer | US-014 | parallelo con US-015 |
| US-017 | Token quota tracking + rate limiting (Redis) | Backend Dev | US-012 | parallelo con US-013 |
| US-018 | Security review: plugin isolation + MCP sanitization | Security Engineer | US-011, US-015 | dopo US-011+015 |
| US-019 | Test coverage: planner, MCP, RAG, plugin lifecycle | QA Engineer | US-013, US-016, US-018 | dopo tutto sopra |

**Phase Gate 2:** plugin system funzionante, planner operativo, RAG pipeline testata, MCP con trust scoring. QA + Security sign-off richiesti.

---

## FASE 3 — API & Frontend

**Obiettivo:** API REST completa, UI funzionante, flussi tenant-aware end-to-end.

| US | Titolo | Agente | Dipendenze | Parallelismo |
|---|---|---|---|---|
| US-020 | API REST: query endpoint (assembla contesto, esegue planner) | Backend Dev | US-013, US-015 | — |
| US-021 | API REST: plugin management endpoints (enable/disable) | Backend Dev | US-010 | parallelo con US-020 |
| US-022 | API REST: tenant admin (quota, user management) | Backend Dev | US-017 | parallelo con US-020 |
| US-023 | Frontend scaffold: React + TS + routing + auth client | Frontend Dev | US-004 | parallelo con US-020 |
| US-024 | Frontend: login/token flow, RBAC-aware navigation | Frontend Dev | US-023 | serie dopo US-023 |
| US-025 | Frontend: query UI con source attribution e confidence | Frontend Dev | US-024, US-020 | serie dopo US-024+020 |
| US-026 | Frontend: plugin management panel (per tenant admin) | Frontend Dev | US-024, US-021 | serie dopo US-024+021 |
| US-027 | Response format: source, confidence, fallback indication | Backend Dev | US-020 | serie dopo US-020 |
| US-028 | Security review: API endpoints, input validation, output format | Security Engineer | US-020–022, US-027 | dopo US-020–027 |
| US-029 | E2E test: flusso completo query → risposta con attribution | QA Engineer | US-025, US-028 | dopo tutto sopra |

**Phase Gate 3:** API completa, UI funzionante end-to-end, response format con attribution. QA + Security sign-off richiesti.

---

## FASE 4 — Production Infra

**Obiettivo:** K8s deployment, resource limits per tenant, CI/CD, hardening.

| US | Titolo | Agente | Dipendenze | Parallelismo |
|---|---|---|---|---|
| US-030 | K8s manifests: tutti i services (API, Worker, Redis, Postgres, Qdrant) | DevOps/Infra | US-003 | — |
| US-031 | Resource limits per tenant (CPU/memory) in K8s | DevOps/Infra | US-030 | serie dopo US-030 |
| US-032 | CI/CD pipeline (build, test, deploy) | DevOps/Infra | US-030 | parallelo con US-031 |
| US-033 | Secrets management (no secrets in code, env injection) | Security Engineer | US-030 | serie dopo US-030 |
| US-034 | Docker hardening + K8s security policies | Security Engineer | US-033 | serie dopo US-033 |
| US-035 | Load + smoke test su staging | QA Engineer | US-031, US-034 | dopo US-031+034 |

**Phase Gate 4 (MVP Done):** deploy su staging funzionante, tutti i test verdi, security hardening completato. Approvazione finale richiesta.
