# Enterprise Multi-Tenant AI Orchestration Platform — Implementation Plan

## Phase 0 Confirmation

I have read in full:

- `docs/mvp-spec.md` — full specification including all 20 sections
- `.claude/agents/backend-dev.md`, `security-engineer.md`, `aiml-engineer.md`, `frontend-dev.md`, `dev-ops.md`, `qa-engineer.md`
- `.claude/workflow.md` — all 4 phases with US table, dependencies, and Phase Gates
I understand the mandatory workflow, agent routing rules, hard constraints, and escalation protocol. What follows is the complete technical plan ready for your approval before any delegation occurs.

---

## 1. Project Directory Structure

```
ai-platform/                          # monorepo root
├── CLAUDE.md                         # (existing) tech lead instructions
├── docs/
│   ├── mvp-spec.md                   # (existing) full spec
│   ├── plan.md                       # THIS document (written to disk by tech lead)
│   ├── adr/                          # Architecture Decision Records
│   │   ├── ADR-001-plone-auth-bridge.md
│   │   ├── ADR-002-plugin-isolation.md
│   │   ├── ADR-003-rag-strategy.md
│   │   └── ADR-004-mcp-trust.md
│   └── progress/                     # US completion summaries (written by agents)
│       └── .gitkeep
├── .claude/
│   ├── agents/                       # (existing) agent personality files
│   └── workflow.md                   # (existing) phase/US table
│
├── backend/                          # Python FastAPI service
│   ├── pyproject.toml                # deps: fastapi, sqlalchemy, alembic, redis, pydantic v2
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_initial_schema.py
│   │       └── 002_plone_identity_fields.py
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory, lifespan, middleware stack
│   │   ├── config.py                 # Settings (pydantic-settings, env vars only)
│   │   ├── db/
│   │   │   ├── base.py               # SQLAlchemy async engine + session factory
│   │   │   └── models/
│   │   │       ├── tenant.py         # Tenant, TenantPlugin, TenantTokenQuota
│   │   │       ├── user.py           # User (platform identity, mapped from Plone)
│   │   │       └── audit.py          # AuditLog
│   │   ├── auth/
│   │   │   ├── jwt.py                # sign/verify, refresh logic
│   │   │   ├── dependencies.py       # FastAPI Depends: get_current_user, require_permission
│   │   │   └── plone_bridge.py       # PloneIdentityAdapter: validates Plone session → issues platform JWT
│   │   ├── rbac/
│   │   │   ├── permissions.py        # Permission enum + role→permission mapping
│   │   │   └── middleware.py         # RBAC enforcement middleware
│   │   ├── plugins/
│   │   │   ├── manager.py            # PluginManager: load, enable, disable per tenant
│   │   │   ├── registry.py           # in-memory registry of active plugin instances
│   │   │   └── manifest.py           # ManifestSchema (pydantic), manifest.yaml parser
│   │   ├── quota/
│   │   │   ├── tracker.py            # Redis-backed token usage tracker
│   │   │   └── enforcer.py           # pre-request quota gate
│   │   ├── audit/
│   │   │   └── service.py            # AuditService: structured append-only log writes
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── router.py         # mounts all v1 sub-routers
│   │   │   │   ├── query.py          # POST /query — assemble context, run planner
│   │   │   │   ├── plugins.py        # GET/POST /plugins — enable/disable
│   │   │   │   ├── tenants.py        # GET/PATCH /tenants — admin quota + user mgmt
│   │   │   │   └── auth.py           # POST /auth/plone-login, POST /auth/refresh
│   │   │   └── health.py             # GET /health
│   │   └── core/
│   │       ├── planner.py            # CostAwarePlanner (AI/ML domain)
│   │       ├── orchestrator.py       # ExecutionGraph runner
│   │       └── response.py           # ResponseFormatter: source+confidence+fallback
│   └── tests/
│       ├── conftest.py               # fixtures: async DB, test tenant, test users
│       ├── test_auth.py
│       ├── test_rbac.py
│       ├── test_schema.py
│       └── test_quota.py
│
├── ai/                               # AI/ML layer (owned by AI/ML Engineer)
│   ├── models/
│   │   ├── base.py                   # ModelAdapter ABC: generate(prompt, context) → str
│   │   ├── claude.py                 # AnthropicClaudeAdapter
│   │   └── copilot.py                # GitHubCopilotAdapter
│   ├── mcp/
│   │   ├── registry.py               # MCPRegistry: register, query by trust score
│   │   ├── base.py                   # MCPServer ABC: async query() → {data, source, confidence}
│   │   ├── trust.py                  # TrustFilter: filters below threshold
│   │   └── context_builder.py        # ContextBuilder: aggregates MCP + RAG + plugins
│   ├── rag/
│   │   ├── pipeline.py               # LlamaIndex pipeline: ingest, embed, retrieve
│   │   ├── qdrant_store.py           # QdrantVectorStore wrapper (tenant-namespaced)
│   │   └── document_processor.py    # Document upload → text extraction → embedding
│   └── tests/
│       ├── test_planner.py
│       ├── test_mcp.py
│       └── test_rag.py
│
├── plugins/                          # Plugin addon directory
│   ├── plone_integration/            # CRITICAL: bridges Plone auth to platform
│   │   ├── manifest.yaml
│   │   ├── plugin.py                 # PloneIntegrationPlugin
│   │   └── plone_client.py           # REST calls to Plone @users endpoint to verify identity + role
│   ├── docs_rag/                     # RAG plugin: site-specific documentation
│   │   ├── manifest.yaml
│   │   ├── plugin.py                 # DocsRAGPlugin — ingests docs, exposes retrieval
│   │   └── docs/                     # seed documentation for demo
│   ├── volto_block_builder/          # Agent: builds Volto blocks for Page CT
│   │   ├── manifest.yaml
│   │   └── plugin.py
│   └── document_import/              # Agent: Page CT from uploaded document
│       ├── manifest.yaml
│       └── plugin.py
│
├── frontend/                         # Volto addons + Plone integration
│   ├── packages/
│   │   └── ai-platform-volto/        # Volto addon
│   │       ├── package.json
│   │       ├── src/
│   │       │   ├── index.ts           # addon entry, register blocks + reducers
│   │       │   ├── components/
│   │       │   │   ├── ChatPanel/     # main chat UI
│   │       │   │   ├── QueryResult/   # source attribution + confidence display
│   │       │   │   └── PluginPanel/   # tenant admin: plugin management
│   │       │   ├── store/
│   │       │   │   ├── auth.ts        # JWT cookie handling, Plone session bridge
│   │       │   │   └── chat.ts        # query state, streaming
│   │       │   └── api/
│   │       │       └── client.ts      # typed API client (generated from OpenAPI)
│   │       └── tests/
│   └── plone-site/                   # cookiecutter-generated Plone 6 site
│       ├── docker-compose.yml        # Plone + Volto on ai-platform docker network
│       └── ...
│
├── infra/
│   ├── docker/
│   │   ├── Dockerfile.backend        # multi-stage, non-root user
│   │   ├── Dockerfile.frontend
│   │   └── Dockerfile.worker
│   ├── docker-compose.yml            # LOCAL DEV: all services + Plone on shared network
│   ├── docker-compose.override.yml   # local secrets (gitignored)
│   ├── k8s/
│   │   ├── namespace.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── worker-deployment.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── redis-statefulset.yaml
│   │   ├── qdrant-statefulset.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml.example      # template only — real secrets via CI injection
│   │   ├── resource-quota.yaml       # per-tenant CPU/mem limits
│   │   └── network-policy.yaml
│   └── ci/
│       └── .github/workflows/
│           ├── test.yml
│           └── deploy.yml
└── .env.example                      # all required env vars documented, no values
```

---

## 2. Architecture Decisions and Rationale

### ADR-001: Plone Auth Bridge — how Plone identity reaches the platform

**Decision.** The platform does NOT replicate Plone's user database. Instead, a dedicated `PloneIntegrationPlugin` acts as an identity provider bridge:

1. The Volto frontend authenticates the user to Plone normally (username/password via Plone's `@login` REST API endpoint). Plone issues its own auth token (JWT or classic session cookie).
2. Volto then calls the platform's `POST /api/v1/auth/plone-login` endpoint, passing the Plone auth token in the request body.
3. The `PloneIdentityAdapter` (backend) calls Plone's `@users/{userid}` REST endpoint using that token to verify the identity and extract the user's Plone roles (e.g. `Manager`, `Member`, `Editor`).
4. If verification succeeds, the platform issues its own JWT containing `{user_id, tenant_id, roles: [plone_roles]}`. This token is returned as an `httpOnly` cookie.
5. All subsequent platform requests use this cookie. The RBAC middleware translates Plone roles to platform permissions.
**Rationale.** This is the only approach that does not require Plone to be modified, does not require an LDAP/SSO setup, and preserves the Plone role model. The PloneIntegrationPlugin is the first plugin to build because everything else depends on knowing who the user is and what their role is.
**Risk.** If Plone's `@users` REST endpoint is not enabled or the token format changes between Plone versions, this breaks. Mitigation: the plugin must explicitly document the required Plone REST API version and endpoints.

### ADR-002: Plugin Isolation Strategy

**Decision.** For the MVP, plugins run in a subprocess (Python `subprocess` with `resource` limits), not in-process. Each subprocess:

- Gets only its own tenant's config (injected as environment variables or stdin JSON)
- Has a wall-clock timeout (10s default)
- Has memory limits enforced via cgroups where available
- Has no network access (iptables-blocked or network namespace)
The PluginManager maintains one subprocess pool per (tenant_id, plugin_name) pair. Plugins communicate via stdin/stdout with a simple JSON envelope.
**Rationale.** Full container isolation is a Phase 4 enterprise feature. Subprocess isolation is sufficient for MVP with trusted plugins (spec section 7: "MVP assumption: plugins are trusted"). The manifest.yaml declares capabilities so the manager can enforce what each plugin is allowed to do.
**File boundary.** `backend/app/plugins/` handles lifecycle. `ai/` layer handles plugin output as context. `plugins/` directory contains the actual plugin code. These are distinct directories with no cross-imports at runtime.

### ADR-003: RAG Integration Strategy

**Decision.** RAG lives entirely in `ai/rag/` and is tenant-namespaced at the Qdrant collection level. Each tenant gets a dedicated Qdrant collection named `tenant_{tenant_id}`. The `DocsRAGPlugin` handles ingestion for the demo; the `DocumentImportPlugin` handles user-uploaded documents.
LlamaIndex is used for:

- Document parsing (PDF, DOCX, plain text via `SimpleDirectoryReader` or `BytesIO` reader for uploads)
- Embedding (via `OpenAIEmbedding` adapter pointing at any compatible endpoint, or a local model)
- Retrieval (top-k similarity search via `QdrantVectorStore`)
The RAG pipeline output is one of the inputs to `ContextBuilder`, which also aggregates MCP results and plugin outputs. All context chunks carry `{source, confidence, tenant_id}` metadata.
**Rationale.** Keeping tenant data in separate Qdrant collections is the simplest way to guarantee no cross-tenant retrieval without application-level filtering on every query.

### ADR-004: MCP Trust Scoring and Context Assembly

**Decision.** The `MCPRegistry` is a singleton holding registered `MCPServer` instances. Each has a statically declared trust score (matching spec section 10). At context assembly time, `ContextBuilder`:

1. Queries all MCP servers registered for the tenant in parallel (async gather)
2. Filters out any result with confidence below `min_confidence` (default 0.5, configurable per tenant)
3. Sorts remaining results by confidence descending
4. Formats each chunk as: `[Source: {source} | confidence: {confidence:.2f}]\n{data}`
5. Sanitizes the combined context against a prompt-injection pattern list
6. Returns the assembled context string plus a structured source list for attribution
**Rationale.** Filtering at assembly time rather than at query time gives the maximum amount of data to the filtering step, and keeps the trust policy centralized. Source attribution in the context string satisfies EU AI Act traceability requirements.

### ADR-005: Token Quota Architecture

**Decision.** Token tracking uses two layers:

- **Redis** (fast path): per-`user_id:tenant_id` sliding window counter for rate limiting (prevents duplicate/rapid submissions). Key TTL = 60 seconds for rate limit window.
- **PostgreSQL** (`tenant_token_quota` table): persistent monthly quota tracking per tenant. Tokens used are written to Postgres after each model call completes.
Before any model call, the `QuotaEnforcer` checks both:

1. Redis rate limit (user-level, per minute)
2. Postgres quota remaining (tenant-level, monthly)
If either check fails, the request is rejected with HTTP 429 before reaching the model layer.
**Rationale.** Redis for rate limiting gives sub-millisecond checks. Postgres for quota gives durable tracking that survives Redis restarts. The two layers cover different threat models: Redis stops burst abuse, Postgres stops slow-burn quota exhaustion.

---

## 3. Cross-Cutting Concerns

### Auth (spans all layers)

Every request to the platform API must carry the platform JWT in an `httpOnly` cookie. The Security Engineer owns `backend/app/auth/` and `backend/app/rbac/`. The JWT contains:

```json
{
  "sub": "<platform_user_id>",
  "tenant_id": "<uuid>",
  "roles": ["Member"],
  "plone_user": "<plone_username>",
  "exp": <unix_ts>,
  "iss": "ai-platform"
}
```

`tenant_id` and `user_id` are ALWAYS extracted from the verified token, NEVER from the request body. This is enforced by a FastAPI dependency (`get_current_user`) that is injected into every route handler.
The Plone bridge flow is the only place where an external identity is accepted — and even there, the platform verifies directly with Plone before issuing its own token.

### Multitenancy (spans DB + Redis + Qdrant + plugins + AI layer)

Every DB query is filtered by `tenant_id` (enforced by Backend Dev's checklist). Every Redis key is prefixed with `tenant_id:user_id:`. Every Qdrant collection is named `tenant_{tenant_id}`. Every plugin subprocess receives only its tenant's config. The QA Engineer writes a mandatory cross-tenant leak test for every US that touches data access.

### Audit Logging (spans all agents except Frontend Dev)

The `AuditService` in `backend/app/audit/service.py` exposes a single async method:

```python
async def log(action: str, resource: str, user_id: str, tenant_id: str, metadata: dict)
```

This is called by:

- Auth layer: login, logout, token refresh
- RBAC layer: permission denied events
- Plugin manager: enable, disable, instantiation errors
- Model layer (via orchestrator): every model query with token count
- MCP layer: every MCP server query with source and confidence
- Quota enforcer: quota exceeded events
Logs are written to the `audit_logs` PostgreSQL table with an append-only constraint (no UPDATE or DELETE granted to the application DB user). This satisfies GDPR and EU AI Act traceability requirements.

### Response Format (all API responses containing AI output)

Every AI response must include:

```json
{
  "response": "...",
  "sources": [
    {"source": "internal_docs", "confidence": 0.95},
    {"source": "github", "confidence": 0.7}
  ],
  "model_used": "claude-3-5-sonnet",
  "fallback": false,
  "tokens_used": 1240
}
```

This format is defined in `backend/app/core/response.py` and is the contract between Backend Dev and Frontend Dev. The Frontend Dev must not hardcode source names — it must render whatever the API returns
---

## 4. Dependency Graph — All Phases

```
US-001 (scaffold)
    └── US-002 (schema)          └── US-003 (docker-compose)  [parallel with US-002]
            └── US-004 (JWT auth)
                    ├── US-005 (RBAC middleware)
                    └── US-006 (audit logging)              [parallel with US-005]
                            └── US-007 (QA: auth+RBAC)     [after US-005 + US-006]
[PHASE GATE 1]
US-005 ──────────────────────────────────┐
US-002 ──────────────────────────────────┼──> US-010 (plugin manager)
                                         │        └── US-011 (plugin runtime isolation)  [Security]
                                         │
US-002 ──────────────────────────────────┼──> US-012 (model layer)
                                         │        └── US-013 (cost-aware planner)
                                         │                └── US-017 (quota+rate limit)  [parallel with US-013]
                                         │
US-005 ──────────────────────────────────┼──> US-014 (MCP registry + trust scoring)
                                         │        ├── US-015 (context builder)
                                         │        └── US-016 (RAG pipeline)             [parallel with US-015]
                                         │
US-011 + US-015 ─────────────────────────┴──> US-018 (Security review: plugin+MCP)
US-013 + US-016 + US-018 ─────────────────────> US-019 (QA: planner+MCP+RAG)
[PHASE GATE 2]
US-013 + US-015 ────────────────────────────> US-020 (API: query endpoint)
US-010 ─────────────────────────────────────> US-021 (API: plugin mgmt)  [parallel with US-020]
US-017 ─────────────────────────────────────> US-022 (API: tenant admin) [parallel with US-020]
US-004 ─────────────────────────────────────> US-023 (Frontend scaffold) [parallel with US-020]
US-023 ─────────────────────────────────────> US-024 (Frontend: auth flow)
US-024 + US-020 ────────────────────────────> US-025 (Frontend: query UI)
US-024 + US-021 ────────────────────────────> US-026 (Frontend: plugin panel)
US-020 ─────────────────────────────────────> US-027 (Response format)
US-020–022 + US-027 ────────────────────────> US-028 (Security review: API)
US-025 + US-028 ────────────────────────────> US-029 (E2E tests)
[PHASE GATE 3]
US-003 ─────────────────────────────────────> US-030 (K8s manifests)
US-030 ─────────────────────────────────────> US-031 (Resource limits)   [parallel with US-032]
US-030 ─────────────────────────────────────> US-032 (CI/CD)             [parallel with US-031]
US-030 ─────────────────────────────────────> US-033 (Secrets mgmt)
US-033 ─────────────────────────────────────> US-034 (Hardening)
US-031 + US-034 ────────────────────────────> US-035 (Load + smoke test)
[PHASE GATE 4 — MVP DONE]
```

---

## 5. Phase 1 User Stories (Detailed)

### US-001: Project Scaffold

**Agent:** Backend Dev
**Phase:** 1
**Dependencies:** none
**Priority:** critical
**Context.**
This is a monorepo. The backend is Python 3.11+ with FastAPI and async SQLAlchemy. The frontend is a Volto addon (TypeScript/React). The agent creates the project skeleton so all subsequent agents have a base to work from. No business logic yet — structure only.
**Task.**
Create the complete directory structure as defined in the architecture plan. Initialize:

- `backend/pyproject.toml` with all declared dependencies (fastapi, sqlalchemy[asyncio], alembic, asyncpg, redis, pydantic-settings, python-jose, passlib, httpx)
- `backend/app/main.py`: FastAPI app factory with CORS middleware, a placeholder lifespan, and `/health` endpoint
- `backend/app/config.py`: pydantic-settings `Settings` class reading from environment variables (DATABASE_URL, REDIS_URL, SECRET_KEY, PLONE_BASE_URL, QDRANT_URL). No defaults for secrets.
- `backend/alembic/` initialized with `alembic init` pattern — `env.py` must use async engine
- `ai/` directory with empty `__init__.py` in each module
- `plugins/` directory with empty `plone_integration/`, `docs_rag/`, `volto_block_builder/`, `document_import/` subdirs, each with a placeholder `manifest.yaml`
- `docs/progress/` directory with `.gitkeep`
- `.env.example` listing every required environment variable with descriptions but no values
**Acceptance Criteria.**
- [ ] `uvicorn backend.app.main:app` starts without errors
- [ ] `GET /health` returns HTTP 200 `{"status": "ok"}`
- [ ] `alembic current` runs without error (even with no migrations yet)
- [ ] All declared pyproject.toml dependencies can be installed with `pip install -e .`
- [ ] `.env.example` contains every variable referenced in `config.py`
- [ ] No secrets or credentials in any committed file
- [ ] `docs/progress/US-001-done.md` written with completion summary
**Files the agent may create or modify.**

```
backend/pyproject.toml
backend/app/main.py
backend/app/config.py
backend/alembic/env.py
backend/alembic/alembic.ini
ai/__init__.py
ai/models/__init__.py
ai/mcp/__init__.py
ai/rag/__init__.py
plugins/plone_integration/manifest.yaml
plugins/docs_rag/manifest.yaml
plugins/volto_block_builder/manifest.yaml
plugins/document_import/manifest.yaml
docs/progress/US-001-done.md
.env.example
```

**Expected output.** Runnable FastAPI skeleton, initialized Alembic, placeholder plugin manifests, `.env.example`
---

### US-002: Database Schema

**Agent:** Backend Dev
**Phase:** 1
**Dependencies:** US-001
**Priority:** critical
**Context.**
The DB must support multi-tenancy at every layer. All entities are tenant-scoped. The schema is the foundation that all other agents build on — schema changes after this point require explicit coordination. Use async SQLAlchemy with Alembic migrations. Never write migrations by hand — always use `alembic revision --autogenerate`.
**Task.**
Create SQLAlchemy ORM models and the initial Alembic migration for:

```
tenants (id UUID PK, name TEXT NOT NULL, plan TEXT NOT NULL, created_at TIMESTAMP)
users (id UUID PK, tenant_id UUID FK→tenants.id, email TEXT UNIQUE, plone_username TEXT, role TEXT CHECK(role IN ('admin','member','guest')), created_at TIMESTAMP)
tenant_plugins (id SERIAL PK, tenant_id UUID FK→tenants.id, plugin_name TEXT, enabled BOOLEAN DEFAULT false, config JSONB DEFAULT '{}')
tenant_token_quota (tenant_id UUID FK→tenants.id PK, max_tokens INT NOT NULL, tokens_used INT DEFAULT 0, reset_date TIMESTAMP NOT NULL)
audit_logs (id UUID PK, user_id UUID, tenant_id UUID, action TEXT NOT NULL, resource TEXT, timestamp TIMESTAMP DEFAULT NOW(), metadata JSONB DEFAULT '{}')
```

Constraints:

- `users.plone_username` + `users.tenant_id` must be UNIQUE together (a Plone user can exist in only one tenant in the platform)
- `audit_logs` table: the application DB user must NOT have UPDATE or DELETE privileges on this table (document this in the migration comment and in the completion summary)
- All UUID columns use `gen_random_uuid()` as server-side default
- Add indexes: `users(tenant_id)`, `tenant_plugins(tenant_id, plugin_name)`, `audit_logs(tenant_id, timestamp)`
**Acceptance Criteria.**
- [ ] `alembic upgrade head` runs against a fresh PostgreSQL instance without errors
- [ ] All 5 tables created with correct columns, types, constraints, and indexes
- [ ] SQLAlchemy models defined in `backend/app/db/models/` with proper relationships
- [ ] `tenant_id` FK enforced at DB level (not just application level)
- [ ] `audit_logs` has no UPDATE/DELETE grant (documented, enforced in migration SQL)
- [ ] `alembic downgrade -1` reverses the migration cleanly
- [ ] Unit test: assert all models can be instantiated and round-tripped through the DB
- [ ] `docs/progress/US-002-done.md` written
**Files the agent may create or modify.**

```
backend/app/db/base.py
backend/app/db/models/tenant.py
backend/app/db/models/user.py
backend/app/db/models/audit.py
backend/alembic/versions/001_initial_schema.py
backend/tests/test_schema.py
docs/progress/US-002-done.md
```

**Expected output.** Alembic migration file, SQLAlchemy models, schema unit test
---

### US-003: Docker Compose Local Environment

**Agent:** DevOps/Infra
**Phase:** 1
**Dependencies:** US-001
**Priority:** critical
**Context.**
This is for local development only. Production uses K8s (Phase 4). The docker-compose must bring up all infrastructure services AND the Plone 6 site on the same Docker network. The Plone site is generated via `cookiecutter https://github.com/collective/cookiecutter-plone-starter` (or equivalent). The AI platform backend must be able to call `http://plone:8080` on the internal network.
The services needed are:

- `postgres`: PostgreSQL 16, data volume persisted
- `redis`: Redis 7, data volume persisted
- `qdrant`: Qdrant latest stable, data volume persisted
- `api`: the FastAPI backend (built from `infra/docker/Dockerfile.backend`)
- `plone`: Plone 6 backend
- `volto`: Volto frontend (Plone's React frontend)
All services on a single Docker network named `ai-platform`.
**Task.**

1. Write `infra/docker-compose.yml` with all services above. Secrets via `.env` file (gitignored). Document all required variables in `.env.example`.
2. Write `infra/docker/Dockerfile.backend`: multi-stage build, non-root user (`appuser`), final image based on `python:3.11-slim`.
3. Bootstrap the Plone 6 site using cookiecutter. Place the generated output in `frontend/plone-site/`. The `docker-compose.yml` must reference the Plone service from this directory.
4. Write a `Makefile` at repo root with targets: `make up`, `make down`, `make logs`, `make migrate` (runs alembic upgrade head inside the api container).
**Acceptance Criteria.**

- [ ] `make up` starts all services without errors
- [ ] `http://localhost:8000/health` returns 200 from the FastAPI API
- [ ] `http://localhost:3000` serves the Volto frontend
- [ ] `http://localhost:8080` serves the Plone backend
- [ ] API container can resolve `http://plone:8080` via Docker internal DNS
- [ ] Volto can call Plone's REST API at `http://plone:8080`
- [ ] No credentials in any committed file (`.env` is gitignored, `.env.example` has placeholders)
- [ ] All containers run as non-root users
- [ ] `make migrate` runs alembic migrations inside the api container
- [ ] `docs/progress/US-003-done.md` written
**Files the agent may create or modify.**

```
infra/docker-compose.yml
infra/docker/Dockerfile.backend
frontend/plone-site/   (entire cookiecutter output)
Makefile
.env.example           (extend with any new vars)
docs/progress/US-003-done.md
```

**Expected output.** Working docker-compose stack with Plone + Volto + platform services all on same network
---

### US-004: JWT Auth + Plone Bridge (backend)

**Agent:** Security Engineer
**Phase:** 1
**Dependencies:** US-002
**Priority:** critical
**Context.**
Plone users authenticate to Plone via username/password. The platform must bridge this identity to its own JWT system without replicating Plone's user store. The flow is:

1. Volto calls Plone `POST /@login` — gets a Plone auth token
2. Volto calls platform `POST /api/v1/auth/plone-login` with `{plone_token: "..."}`
3. Platform calls Plone `GET /@users/{username}` using that token to verify identity and extract roles
4. Platform upserts a `users` row (creating if first login)
5. Platform issues a signed JWT (HS256, SECRET_KEY from env) and a refresh token
6. JWT returned as `httpOnly`, `SameSite=Strict`, `Secure` cookie named `ai_platform_token`
7. Refresh token stored in `httpOnly` cookie named `ai_platform_refresh`
The JWT payload must be:

```json
{"sub": "<platform_user_id_uuid>", "tenant_id": "<uuid>", "roles": ["Member"], "plone_user": "<username>", "exp": <now+3600>, "iss": "ai-platform"}
```

Refresh token endpoint: `POST /api/v1/auth/refresh` — validates refresh token, issues new access JWT.
**Task.**
Implement:

- `backend/app/auth/jwt.py`: `create_access_token()`, `create_refresh_token()`, `verify_token()` — all using `python-jose` with HS256. SECRET_KEY from `config.py`. Access token TTL: 1 hour. Refresh token TTL: 7 days.
- `backend/app/auth/plone_bridge.py`: `PloneIdentityAdapter` — async httpx call to Plone `@users/{username}`, extracts roles from Plone response, returns `PloneIdentity(username, roles, tenant_id)`. Must handle: Plone unreachable (503 upstream), invalid token (401), user not found (404).
- `backend/app/auth/dependencies.py`: FastAPI `Depends` function `get_current_user()` — reads cookie, verifies JWT, returns `CurrentUser(id, tenant_id, roles)`. Raises HTTP 401 on any failure.
- `backend/app/api/v1/auth.py`: route handlers for `POST /auth/plone-login` and `POST /auth/refresh`.
- Upsert logic: if `users` row for `(plone_username, tenant_id)` does not exist, create it. If it exists, update `role` from Plone.
**Acceptance Criteria.**
- [ ] `POST /auth/plone-login` with valid Plone token returns `httpOnly` cookies and HTTP 200
- [ ] `POST /auth/plone-login` with invalid Plone token returns HTTP 401 (no cookie set)
- [ ] `POST /auth/plone-login` when Plone is unreachable returns HTTP 503
- [ ] Access token expires after 1 hour (verified in test by mocking time)
- [ ] `POST /auth/refresh` with valid refresh token returns new access token
- [ ] `POST /auth/refresh` with expired/invalid refresh token returns HTTP 401
- [ ] `tenant_id` and `user_id` are NEVER read from request body — only from verified JWT
- [ ] JWT uses HS256, signed with SECRET_KEY from env (never hardcoded)
- [ ] All cookies have `httpOnly=True`, `SameSite=Strict`, `Secure=True` (in prod; allow http in dev via config flag)
- [ ] User upserted in `users` table on successful Plone login
- [ ] Audit log entry written for every login event (success and failure)
- [ ] `docs/progress/US-004-done.md` with Security Notes section
**Files the agent may create or modify.**

```
backend/app/auth/jwt.py
backend/app/auth/plone_bridge.py
backend/app/auth/dependencies.py
backend/app/api/v1/auth.py
backend/app/api/v1/router.py    (mount auth router)
docs/progress/US-004-done.md
```

**Expected output.** Working auth endpoints, Plone bridge, JWT cookie management. No business logic — security layer only
---

### US-005: RBAC Middleware — Permission Enforcement Per Tenant

**Agent:** Security Engineer
**Phase:** 1
**Dependencies:** US-004
**Priority:** critical
**Context.**
All platform permissions are scoped to `(user, tenant)`. Plone roles must be mapped to platform permissions. The RBAC system is the enforcement layer — it does not contain business logic. It only answers "is this user allowed to do X in this tenant?"
Plone role → platform permission mapping for MVP:

```
Plone Manager  → platform roles: [admin, query.execute, plugin.enable, plugin.disable, mcp.query]
Plone Editor   → platform roles: [query.execute, mcp.query]
Plone Member   → platform roles: [query.execute]
Plone Reviewer → platform roles: [query.execute, mcp.query]
(any other)    → [] (deny all)
```

**Task.**
Implement:

- `backend/app/rbac/permissions.py`: `Permission` enum with all permission strings. `ROLE_PERMISSIONS: dict[str, list[Permission]]` mapping. Function `get_permissions(plone_roles: list[str]) -> set[Permission]`.
- `backend/app/rbac/middleware.py`: FastAPI dependency `require_permission(permission: Permission)` — factory function returning a `Depends` that checks if `current_user` has the required permission. Raises HTTP 403 if not. Permission check happens BEFORE any DB query or business logic in the route.
- Every permission denial must be written to audit log: `action="permission_denied"`, `resource=<permission_name>`, `metadata={"required": permission, "user_roles": user.roles}`.
**Acceptance Criteria.**
- [ ] `require_permission(Permission.QUERY_EXECUTE)` as a FastAPI dependency blocks requests from users without the permission (HTTP 403)
- [ ] A Plone `Manager` user has all permissions
- [ ] A Plone `Member` user has only `query.execute`
- [ ] An unauthenticated request returns HTTP 401 (from `get_current_user`), not 403
- [ ] Permission check uses JWT roles only — never reads from DB per request
- [ ] Every denied permission attempt is logged to `audit_logs`
- [ ] Default is DENY — unknown roles get zero permissions
- [ ] Cross-tenant: a user authenticated for tenant A cannot be granted permissions in tenant B (roles are scoped to the JWT's `tenant_id`)
- [ ] `docs/progress/US-005-done.md` with Security Notes section
**Files the agent may create or modify.**

```
backend/app/rbac/permissions.py
backend/app/rbac/middleware.py
docs/progress/US-005-done.md
```

**Expected output.** RBAC permission system, role mapping, FastAPI dependency, audit integration
---

### US-006: Audit Logging Service

**Agent:** Security Engineer
**Phase:** 1
**Dependencies:** US-004
**Priority:** high
**Context.**
GDPR and EU AI Act require tamper-evident logs of all AI system actions, including: who made the request, what model was used, what sources were cited, with what confidence. The audit log is append-only. The application DB user has no UPDATE or DELETE on `audit_logs` (established in US-002). This US runs in parallel with US-005.
**Task.**
Implement:

- `backend/app/audit/service.py`: `AuditService` class with single method `async log(action, resource, user_id, tenant_id, metadata={})`. Writes to `audit_logs` table. Must be non-blocking — use `asyncio.create_task` so audit writes do not add to request latency.
- `AuditService` is a singleton instantiated at app startup (via FastAPI lifespan) and injected via `Depends`.
- Define all `action` string constants as a typed `AuditAction` enum: `LOGIN_SUCCESS`, `LOGIN_FAILURE`, `PERMISSION_DENIED`, `MODEL_QUERY`, `MCP_QUERY`, `PLUGIN_ENABLED`, `PLUGIN_DISABLED`, `QUOTA_EXCEEDED`, `DOCUMENT_UPLOADED`.
- Write a `get_audit_service()` FastAPI dependency for injection into route handlers and other services.
**Acceptance Criteria.**
- [ ] `audit_service.log(...)` writes a row to `audit_logs` with all required fields
- [ ] Audit write is non-blocking (does not fail the request if audit write fails — but logs the error to stderr)
- [ ] All `AuditAction` enum values are defined and used consistently
- [ ] The service cannot execute UPDATE or DELETE on `audit_logs` (verified by attempting both in a test — both must raise DB-level errors)
- [ ] Integration test: simulate 3 actions and verify all 3 rows appear in DB with correct fields
- [ ] `docs/progress/US-006-done.md` with Security Notes (including note about non-blocking write trade-off: write failure is not surfaced to user)
**Files the agent may create or modify.**

```
backend/app/audit/service.py
backend/app/audit/__init__.py
docs/progress/US-006-done.md
```

**Expected output.** Working AuditService, AuditAction enum, FastAPI dependency
---

### US-007: Test Coverage — Auth, RBAC, Schema

**Agent:** QA Engineer
**Phase:** 1
**Dependencies:** US-005, US-006
**Priority:** high
**Context.**
This is the Phase 1 QA sign-off. The QA Engineer writes tests that DELIBERATELY try to break auth and RBAC, not just happy path. Tests run against a real (test) PostgreSQL instance (use pytest-asyncio with a transactional rollback fixture). Mock Plone's HTTP endpoints using `respx` or `httpx_mock`.
**Task.**
Write the following test files:
`backend/tests/test_auth.py`:

- Happy path: valid Plone token → platform JWT issued → cookie set
- Plone token invalid → 401, no cookie
- Plone unreachable → 503
- Expired access token → 401 on protected endpoint
- Valid refresh token → new access token issued
- Invalid/expired refresh token → 401
`backend/tests/test_rbac.py`:
- Manager role → all permissions granted
- Member role → only query.execute granted
- Unknown role → zero permissions
- Permission denied → audit log entry written
- Cross-tenant isolation: JWT for tenant A cannot access tenant B's protected resource
`backend/tests/test_schema.py`:
- All 5 tables created correctly (column types, constraints)
- FK constraint: user with non-existent tenant_id → DB error
- Unique constraint: duplicate (plone_username, tenant_id) → DB error
- audit_logs append-only: UPDATE attempt → DB error, DELETE attempt → DB error
**Acceptance Criteria.**
- [ ] All tests pass with `pytest backend/tests/` on a clean DB
- [ ] Test coverage for `auth/` and `rbac/` modules >= 90%
- [ ] Cross-tenant isolation test explicitly present and passing
- [ ] No test modifies production DB (transactional rollback fixture used)
- [ ] Plone HTTP calls mocked in all tests (no real Plone instance required)
- [ ] `docs/progress/US-007-done.md` with coverage report
**Files the agent may create or modify.**

```
backend/tests/conftest.py
backend/tests/test_auth.py
backend/tests/test_rbac.py
backend/tests/test_schema.py
docs/progress/US-007-done.md
```

**Expected output.** Full test suite with coverage report. Must pass before Phase Gate 1
---

## 6. Plone/Volto Integration Points — Detailed

### Integration Point 1: Plone Login → Platform Token

This is the most critical integration. The exact sequence:

1. User enters credentials in Volto login form
2. Volto calls `POST http://plone:8080/@login` with `{login, password}` — Plone returns a `token` (Plone JWT or classic session)
3. Volto immediately calls `POST http://api:8000/api/v1/auth/plone-login` with `{plone_token: token, tenant_id: "<configured_uuid>"}` in the request body. The `tenant_id` is configured at the Volto addon level (env variable or Volto registry setting).
4. Platform verifies token with Plone, issues its own JWT cookie
5. All subsequent Volto API calls to the platform use the httpOnly cookie automatically
The Volto addon must intercept Plone's login flow (via Volto's Redux middleware or a custom `LOGIN_SUCCESS` action handler) to trigger step 3.

### Integration Point 2: PloneIntegrationPlugin — Role Verification

The `PloneIntegrationPlugin` in `plugins/plone_integration/` is responsible for:

- Calling Plone's `GET /@users/{username}` or `GET /@groups` to get the user's current roles
- Mapping Plone roles to platform permissions (this mapping is defined in `backend/app/rbac/permissions.py` but the plugin is the source of truth for role data)
- Refreshing role data on each platform token refresh (roles can change in Plone without the platform knowing)
This plugin is enabled for every tenant that uses Plone as their identity provider. It is the only plugin that has network access to Plone's internal URL.

### Integration Point 3: Volto Block Builder Demo

The Volto block builder agent demo works as follows:

1. User is on a Plone Page content type in Volto edit mode
2. The AI chat panel (Volto addon component) appears alongside the editor
3. User types: "Add a hero block with the title 'Welcome' and a description 'Our platform...'"
4. Volto addon calls `POST /api/v1/query` with `{prompt: "...", context: {page_uid: "...", current_blocks: {...}}, agent: "volto_block_builder"}`
5. Platform runs the `volto_block_builder` plugin, which generates a Volto blocks JSON structure
6. Response includes the generated blocks JSON in `metadata.blocks`
7. Volto addon applies the blocks to the current page via Plone's REST API `PATCH /@content/{uid}`

### Integration Point 4: Document Upload Demo

1. User uploads a PDF/DOCX to the AI chat panel
2. Volto addon sends `POST /api/v1/query` with `Content-Type: multipart/form-data`, file in form data
3. Platform: `document_import` plugin extracts text via LlamaIndex `SimpleDirectoryReader`, then calls the model to generate a Volto Page structure (title + text blocks from document sections)
4. Response includes the Page content type JSON
5. Volto addon creates the Page via Plone's REST API `POST /api/@content`

### Integration Point 5: RAG Documentation Agent

1. User types a question about Volto blocks or platform documentation
2. `docs_rag` plugin is queried — it retrieves relevant documentation chunks from Qdrant (pre-embedded at startup)
3. Results feed into `ContextBuilder` alongside any MCP results
4. Model receives assembled context and generates an answer with source attribution
5. Volto renders the response with `[Source: internal_docs | confidence: 0.95]` attribution visible

---

## 7. Risk Areas

### Risk 1: Plone REST API Compatibility (HIGH)

Plone's `@login` endpoint and `@users` endpoint behavior depends on the Plone version and installed addons (notably `plone.restapi`). The platform's Plone bridge assumes `plone.restapi >= 8.x` and JWT auth enabled. If the Plone cookiecutter generates a site with a different restapi version or without JWT auth configured, the entire auth bridge breaks.
Mitigation: US-003 (DevOps) must document the exact `plone.restapi` version pinned in the cookiecutter. US-004 (Security) must handle all Plone HTTP error cases explicitly. A health check endpoint on the platform must verify Plone reachability on startup.

### Risk 2: Volto Addon Auth Intercept (HIGH)

Volto's Redux-based authentication flow is complex. Intercepting the login flow to add the platform token exchange step requires deep knowledge of Volto's `@plone/volto` internal actions. If Volto's internals change between versions, the addon breaks silently (users can log into Plone but not the platform).
Mitigation: Frontend Dev must pin the Volto version in package.json. The auth intercept must be implemented as a Redux middleware (not a component), so it fires regardless of which login component is used. The demo flow must be E2E-tested with Playwright (US-029).

### Risk 3: Cross-Tenant Isolation in Qdrant (HIGH)

If a developer accidentally queries the wrong Qdrant collection (e.g. uses `tenant_id` from a request body instead of from the JWT), documents from one tenant are returned to another. This is invisible at the application level.
Mitigation: `qdrant_store.py` must ONLY accept `tenant_id` from the verified `CurrentUser` object (passed in, never from request). QA Engineer must write a mandatory cross-tenant Qdrant test in US-019. Qdrant collection naming convention `tenant_{uuid}` must be the only access pattern.

### Risk 4: Plugin Subprocess Communication Latency (MEDIUM)

JSON envelope over stdin/stdout between the FastAPI process and plugin subprocesses adds latency. For the Volto block builder demo (which needs to feel responsive), this latency compounds with model API latency.
Mitigation: Plugin process pool (pre-warm one subprocess per active plugin per tenant on enable). Measure P99 latency in QA load tests (US-035). If unacceptable, fall back to in-process execution for trusted MVP plugins only, with a clear comment marking it as a security debt.

### Risk 5: Alembic Migration State Drift (MEDIUM)

Multiple agents (Backend Dev for schema, AI/ML Engineer if Qdrant-related tables are needed) may need to add migrations. If two agents create migration files simultaneously with conflicting heads, `alembic upgrade head` breaks for everyone.
Mitigation: All schema changes route through Backend Dev only (per agent routing rules). AI/ML Engineer must NOT create Alembic migrations — if new columns are needed for AI features, the AI/ML Engineer files a request to Backend Dev as a dependency. This must be enforced by the tech lead at delegation time.

### Risk 6: EU AI Act Source Attribution in Audit Logs (MEDIUM)

EU AI Act Article 13 (transparency) requires that AI-generated content be traceable to its sources. If the `ContextBuilder` assembles context but the final audit log entry only records the model name and not the specific MCP/RAG sources used in that response, the platform is non-compliant.
Mitigation: The `AuditAction.MODEL_QUERY` log entry must include `metadata.sources` (list of `{source, confidence}` for every source included in the context). This must be part of the `AuditService.log()` call in the orchestrator, after `ContextBuilder` returns. This must be explicitly in the acceptance criteria for US-006 and US-018.

### Risk 7: Plone Cookiecutter Version Pinning (MEDIUM)

`cookiecutter-plone-starter` templates change frequently. If DevOps runs the cookiecutter without a pinned tag, the generated Plone site may use a Plone version incompatible with the restapi assumptions.
Mitigation: US-003 must use a specific git tag of the cookiecutter template (not `main`). Document the exact Plone version in `docs/progress/US-003-done.md`
---

## Phase 1 Parallel Execution Map

The following User Stories can be spawned simultaneously after their dependencies resolve:
**Day 1 — Sequential.**

- Spawn US-001 (Backend Dev). Wait for completion.
**Day 1-2 — Parallel batch.**
- Spawn US-002 (Backend Dev) and US-003 (DevOps/Infra) simultaneously. Wait for both.
**Day 2-3 — Sequential.**
- Spawn US-004 (Security Engineer). Wait for completion.
**Day 3-4 — Parallel batch.**
- Spawn US-005 (Security Engineer) and US-006 (Security Engineer) simultaneously. Note: both go to the same agent. If the agent system supports only one instance per agent, run series. If parallel instances are supported, run in parallel since they touch different files.
**Day 4-5.**
- Spawn US-007 (QA Engineer). Wait for completion.
**Phase Gate 1 checkpoint** — present to user, get approval before Phase 2.
