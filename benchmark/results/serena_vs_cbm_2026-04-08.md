# Serena vs CBM Navigation Benchmark — 2026-04-08

## Summary

| Run | Status | Total tokens | Total tool calls |
|-----|--------|-------------|-----------------|
| Run A — Serena | Complete | 46,978 | 36 (agent) / 18 (Serena MCP) |
| Run B — CBM | Pending — CBM build failed (see note) | — | — |

---

## Run A — Serena Results

Sub-agent model: `claude-sonnet-4-6`
Navigation constraint: `mcp__serena__*` only (Read/Grep/Glob only as last resort after MCP miss)

### Task Results

#### T1 — Class definition with fields (`Plugin`)

**Tools called:** `mcp__serena__find_symbol` (×2), `mcp__serena__find_file`, `mcp__serena__search_for_pattern`, `mcp__serena__get_symbols_overview`, `mcp__serena__find_symbol` with body (×2)

**Tool call count:** 7

**Answer:** No class named `Plugin` exists. Models are split across `backend/app/db/models/` directory (not a single `models.py`). Closest equivalent is `TenantPlugin` in `backend/app/db/models/tenant.py`:

```
class TenantPlugin(Base):
    __tablename__ = "tenant_plugins"
    id:          Mapped[int]       — Integer, PK, autoincrement
    tenant_id:   Mapped[uuid.UUID] — UUID, FK → tenants.id (CASCADE), NOT NULL
    plugin_name: Mapped[str]       — Text, NOT NULL
    enabled:     Mapped[bool]      — Boolean, default=False, NOT NULL
    config:      Mapped[dict]      — JSONB, default=dict, NOT NULL
    tenant:      Mapped["Tenant"]  — relationship back to Tenant
```

Also found `PluginManifest` (Pydantic, `backend/app/plugins/manager.py`) with fields: id, version, capabilities, entrypoint, description.

**Accuracy score:** 2/3 — class name mismatch (task says `Plugin`, codebase has `TenantPlugin`), but correct model found with all fields

---

#### T2 — Call path tracing (`/api/plugins` GET)

**Tools called:** `mcp__serena__search_for_pattern` (×2), `mcp__serena__find_symbol`, `mcp__serena__search_for_pattern`

**Tool call count:** 4

**Answer:** No `/api/plugins` GET route exists. The API only exposes auth endpoints. Closest functional path:

1. (No HTTP handler)
2. `PluginManager.get_active_plugins(tenant_id, db)` — `backend/app/plugins/manager.py:83`
3. `db.execute(stmt)` — direct SQLAlchemy async query (`select(TenantPlugin).where(...)`)

**Accuracy score:** 2/3 — route doesn't exist in codebase; Serena correctly identified this and provided the closest available path

---

#### T3 — Cross-file reference search (`tenant_id`)

**Tools called:** `mcp__serena__search_for_pattern`

**Tool call count:** 1

**Answer:** 35 files total reference `tenant_id` (excluding `backend/app/db/models.py` which doesn't exist as a file):

Production: `backend/app/rbac/middleware.py`, `backend/app/auth/plone_bridge.py`, `backend/app/auth/dependencies.py`, `backend/app/plugins/runtime.py`, `backend/app/plugins/manager.py`, `backend/app/audit/service.py`, `backend/app/db/models/user.py`, `backend/app/db/models/tenant.py`, `backend/app/db/models/audit.py`, `backend/app/api/v1/auth.py`, `backend/app/quota/quota_service.py`, `backend/app/quota/rate_limiter.py`, `backend/alembic/versions/001_initial_schema.py`, `ai/context/builder.py`, `ai/mcp/registry.py`, `ai/rag/store.py`, `ai/rag/pipeline.py`

Tests: `backend/tests/conftest.py`, `backend/tests/test_rag_pipeline.py`, `backend/tests/test_plugin_manager.py`, `backend/tests/test_security_review.py`, `backend/tests/test_auth.py`, `backend/tests/test_rbac.py`, `backend/tests/test_schema.py`, `backend/tests/test_mcp_full.py`, `backend/tests/test_plugin_runtime.py`, `backend/tests/test_e2e_mock.py`, `backend/tests/test_plugin_lifecycle.py`, `backend/tests/test_quota.py`, `backend/tests/test_mcp.py`, `backend/tests/test_rag.py`, `backend/tests/test_context_builder.py`

**Accuracy score:** 3/3 — complete list, single tool call

---

#### T4 — Class method enumeration (`CostAwarePlanner`)

**Tools called:** `mcp__serena__search_for_pattern` (×2), `mcp__serena__get_symbols_overview`, `mcp__serena__find_symbol` with body

**Tool call count:** 4

**Answer:** `CostAwarePlanner` does not exist. The planner class is `Planner` in `ai/planner/planner.py`. One public method:

```python
async def plan(
    self,
    prompt: str,
    context: str,
    quota_remaining: int,
    settings,
    _primary_adapter: Optional[ModelAdapter] = None,
) -> ExecutionPlan
```

**Accuracy score:** 2/3 — class name mismatch (task uses wrong name), but Serena found the correct class and returned the full method signature

---

#### T5 — Import graph (`ai/mcp/registry.py`)

**Tools called:** `mcp__serena__search_for_pattern` (×2)

**Tool call count:** 2

**Answer:** Modules importing from `ai/mcp/registry.py`:

Production: `ai/mcp/__init__.py`, `ai/context/builder.py`

Tests: `backend/tests/test_mcp.py`, `backend/tests/test_context_builder.py`, `backend/tests/test_mcp_full.py`, `backend/tests/test_e2e_mock.py`, `backend/tests/test_plone_mcp.py`

**Accuracy score:** 3/3 — complete with production + test separation

---

### Run A Summary Table

| Task | Serena tokens | Serena tool calls | Serena acc (1-3) | Notes |
|------|--------------|-------------------|------------------|-------|
| T1   | ~9,000 est.  | 7                 | 2                | Class name mismatch (`Plugin` → `TenantPlugin`), full fields found |
| T2   | ~7,000 est.  | 4                 | 2                | Route doesn't exist, nearest path found |
| T3   | ~10,000 est. | 1                 | 3                | Perfect: 35 files in 1 call |
| T4   | ~8,000 est.  | 4                 | 2                | Class name mismatch, correct class found with signature |
| T5   | ~5,000 est.  | 2                 | 3                | Complete import graph |
| **Total** | **46,978** | **18**        | **12/15**        | |

*Per-task token estimates are approximations; total from agent usage metadata.*

---

## Run B — CBM (PENDING — BUILD FAILED)

**Build command:** `docker compose -f infra/docker-compose.ai-tools.yml build codebase-memory-mcp`

**Failure:** The CBM install script downloads `codebase-memory-mcp-linux-arm64.tar.gz` but the binary fails to execute after extraction:

```
#6 7.845 error: installed binary failed to run
#7 0.084 ERROR: cbm binary not found after install
failed to solve: process "/bin/sh -c cbm --version ..." did not complete successfully: exit code: 1
```

**Root cause hypothesis:** Pre-built linux/arm64 binary from `github.com/DeusData/codebase-memory-mcp` is incompatible with the Debian bookworm-slim container (possible glibc version mismatch, or the binary targets a different arm64 variant).

**Run B rows:** Pending CBM build fix.

| Task | CBM tokens | CBM tool calls | CBM acc (1-3) |
|------|-----------|----------------|---------------|
| T1   |           |                |               |
| T2   |           |                |               |
| T3   |           |                |               |
| T4   |           |                |               |
| T5   |           |                |               |
| **Total** |    |                |               |

> **Run B requires CBM build fix, then Claude Code restart — use Prompt B after resolving the build issue.**
