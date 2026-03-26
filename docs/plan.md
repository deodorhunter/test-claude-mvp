# Technical Plan — AI Orchestration Platform MVP

> Last updated: 2026-03-26 | Phase: 1 (Foundation) — In Progress

## Architecture Overview

Multi-tenant AI orchestration platform. Backend: Python/FastAPI. Frontend: Volto addon on Plone 6. AI: LlamaIndex + Qdrant. Infra: Docker/K8s.

### Key Architecture Decisions

**ADR-001: Plone Auth Bridge**
Platform does NOT replicate Plone's user store. Flow:
1. Volto logs in to Plone → Plone token
2. Volto calls `POST /api/v1/auth/plone-login` with Plone token
3. `PloneIdentityAdapter` verifies via Plone `GET /@users/{username}` → extracts roles
4. Platform issues own JWT as `httpOnly` cookie (`ai_platform_token`)
5. JWT payload: `{sub, tenant_id, roles: [plone_roles], plone_user, exp, iss}`

**ADR-002: Plugin Isolation (MVP)**
Subprocess with resource limits (cgroups, 10s timeout). JSON over stdin/stdout. Pool per `(tenant_id, plugin_name)`. Network blocked except `plone_integration`.

**ADR-003: RAG Tenancy**
Each tenant = dedicated Qdrant collection `tenant_{tenant_id}`. `tenant_id` comes ONLY from verified JWT, never from request body.

**ADR-004: Token Quota**
Two layers: Redis (rate limit, 60s window, sub-ms) + PostgreSQL (monthly quota, durable). Both checked before every model call.

**ADR-005: AI Response Format**
```json
{"response": "...", "sources": [{"source": "...", "confidence": 0.95}], "model_used": "...", "fallback": false, "tokens_used": 1240}
```

### Cross-Cutting Rules

| Concern | Rule |
|---|---|
| Auth | `tenant_id` / `user_id` from verified JWT ONLY, never request body |
| Multitenancy | All DB queries filtered by `tenant_id`. Redis keys: `tenant_id:user_id:*`. Qdrant: `tenant_{id}` |
| Audit log | Append-only. No UPDATE/DELETE grant. `MODEL_QUERY` entries must include `metadata.sources` |
| Schema | Only Backend Dev creates Alembic migrations |

---

## Phase Dependency Graph

```
US-001 (scaffold) → US-002 (schema) + US-003 (docker) [parallel]
                              ↓
                       US-004 (JWT/Plone auth)
                         ↓              ↓
               US-005 (RBAC)    US-006 (audit log) [parallel]
                              ↓
                       US-007 (QA) → [PHASE GATE 1]
                              ↓
               US-010–019 (Core Platform) → [PHASE GATE 2]
                              ↓
               US-020–029 (API & Frontend) → [PHASE GATE 3]
                              ↓
               US-030–035 (Production Infra) → [PHASE GATE 4]
```

---

## Phase 1 — Foundation

| US | Title | Agent | Status |
|---|---|---|---|
| US-001 | Project Scaffold | Backend Dev | ✅ Done |
| US-002 | Database Schema | Backend Dev | ✅ Done |
| US-003 | Docker Compose Local | DevOps/Infra | ✅ Done |
| US-004 | JWT Auth + Plone Bridge | Security Engineer | ✅ Done |
| US-005 | RBAC Middleware | Security Engineer | ✅ Done |
| US-006 | Audit Logging Service | Security Engineer | ✅ Done |
| US-007 | Test Coverage | QA Engineer | ✅ Done |

### Top Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Plone REST API version mismatch | HIGH | Pin plone.restapi version in US-003; handle all HTTP errors in US-004 |
| Volto auth intercept fragility | HIGH | Pin Volto version; implement as Redux middleware; E2E test in US-029 |
| Cross-tenant Qdrant leak | HIGH | `qdrant_store.py` only accepts tenant_id from CurrentUser |
| Alembic migration conflicts | MEDIUM | Only Backend Dev creates migrations |
| Incomplete audit for EU AI Act | MEDIUM | MODEL_QUERY logs must include metadata.sources |
