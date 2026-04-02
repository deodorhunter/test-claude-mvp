# Handoff: US-019 — Test Coverage Phase 2: Planner, MCP, RAG, Plugin Lifecycle

**Completed by:** Tech Lead direct (QA Engineer role)
**Date:** 2026-03-31 (tests written 2026-03-30; verified 2026-03-31)
**Files created:** 6 test files (1,000 total lines, 61 tests)

## What was built

Full Phase 2 test coverage filling gaps left by unit tests already present in US-010 through US-018. Six test files covering the five core systems: plugin lifecycle, model layer adapters, MCP registry, RAG pipeline, planner integration, and end-to-end mock pipeline.

All external I/O mocked — no real Qdrant, Ollama, Claude API, Redis, or DB required. Tests run in-container via `pytest -q --tb=short`.

## Test files and coverage

| File | Classes | Tests | What it covers |
|---|---|---|---|
| `backend/tests/test_plugin_lifecycle.py` | 3 | 7 | enable/disable cycle, cross-tenant plugin isolation, semaphore key scoping |
| `backend/tests/test_model_layer.py` | 4 | 9 | MockAdapter, OllamaAdapter, ClaudeAdapter contracts, factory AI_MODE selection |
| `backend/tests/test_mcp_full.py` | 5 | 11 | registry register/get_all, trust filtering, source attribution format, server timeout, multi-server |
| `backend/tests/test_rag_pipeline.py` | 4 | 8 | index_document tenant_id pass-through, query tenant_id, cross-tenant collection isolation, empty store |
| `backend/tests/test_planner_integration.py` | 3 | 5 | quota exceeded path, fallback_used=True on OllamaUnavailable, 10 concurrent no-deadlock |
| `backend/tests/test_e2e_mock.py` | 5 | 11 | full pipeline happy path, consume_quota wiring, quota exceeded, cross-tenant quota, concurrent 2-tenant load |

## Manual test instructions

```bash
# Run all US-019 tests
docker exec -e PYTHONPATH=/app ai-platform-api pytest -q --tb=short \
  tests/test_plugin_lifecycle.py \
  tests/test_model_layer.py \
  tests/test_mcp_full.py \
  tests/test_rag_pipeline.py \
  tests/test_planner_integration.py \
  tests/test_e2e_mock.py

# Expected: 61 passed, 0 failed
```

## How to verify

```bash
# Full suite (no regressions)
docker exec -e PYTHONPATH=/app ai-platform-api pytest -q --tb=short
# Expected: 274 passed (Phase 2 baseline before US-020), 0 failed
```

## Integration points

**No new production code** — this US adds tests only. No existing files were modified.

**Key import paths verified by these tests:**
- `ai.planner.planner.Planner` — quota + fallback behavior
- `ai.mcp.registry.MCPRegistry` — trust filtering + audit logging
- `ai.mcp.base.MCPServer`, `MCPResult` — server contract
- `ai.rag.pipeline.RAGPipeline`, `RAGChunk` — tenant isolation
- `ai.rag.store.QdrantStore` — collection naming
- `app.plugins.manager.PluginManager` — enable/disable/tenant scoping
- `ai.models.factory.ModelFactory` — AI_MODE routing

**Regression gate:** any Phase 3 implementation must pass all 61 tests here before merge. They are the lowest-cost signal for Phase 2 regressions.

## File ownership

| File | Owner | Notes |
|---|---|---|
| `backend/tests/test_plugin_lifecycle.py` | QA Engineer | gate for US-010/011 plugin changes |
| `backend/tests/test_model_layer.py` | QA Engineer | gate for US-012 model adapter contract |
| `backend/tests/test_mcp_full.py` | QA Engineer | gate for US-014/015 registry + attribution |
| `backend/tests/test_rag_pipeline.py` | QA Engineer | gate for US-016 RAG pipeline + tenant isolation |
| `backend/tests/test_planner_integration.py` | QA Engineer | gate for US-013 planner quota/fallback |
| `backend/tests/test_e2e_mock.py` | QA Engineer | full pipeline integration gate |

## Residual risks

None critical. `backend/tests/` is not volume-mounted in Docker — new test files require `docker cp` or a container rebuild to be picked up by `make test`.
