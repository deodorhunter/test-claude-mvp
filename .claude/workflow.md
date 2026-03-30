# MVP Workflow — Phase Dependency Graph

> Phase details and US status: see `docs/backlog/BACKLOG.md`
> Delegation workflow, parallelism rules, QA: see `.claude/agents/orchestrator.md`
> Git branching: orchestrator.md "Git Branching" section

## Phase Dependencies

```
Phase 1 (Foundation) ✅
  └→ Phase 2a (Plugin System) ✅
  └→ Phase 2b (Model Layer) ✅
  └→ Phase 2c (MCP + RAG) ✅
  └→ Phase 2d (Quota + Security + Tests) 🔄
       └→ Phase 3 (API & Frontend)
            └→ Phase 4 (Production Infra)
```

## Mini-Gate Checklists

### Mini-gate 2a (Plugin System) ✅
- Plugin loadable from manifest YAML
- Enable/disable per tenant (no restart)
- Subprocess isolation: cross-tenant test passes
- Timeout 10s enforcement tested

### Mini-gate 2b (Model Layer) ✅
- `OllamaAdapter.generate()` works in container
- `ClaudeAdapter.generate()` tested with mock
- Planner selects model by quota + availability
- Fallback Ollama → Claude functional (with mock)

### Mini-gate 2c (MCP + RAG) ✅
- RAG query returns results with source attribution
- MCP trust scoring filters below threshold
- Prompt injection patterns blocked
- Cross-tenant RAG isolation tested

### Mini-gate 2d (Phase Gate 2)
- Rate limiting blocks excess requests
- Monthly quota enforced (no quota → 429)
- Audit log integrated: login, denial, quota_exceeded, mcp_query, model_query
- Refresh token rotation implemented
- Test suite ≥80% coverage on Phase 2 modules
- Full Service Verification passes

## Smoke Test Quick Reference

```bash
# Per-US
curl -s http://localhost:8000/health   # → 200
pytest -q --tb=short                   # US tests pass

# Phase Gate
make down && make up && make migrate
curl -s http://localhost:8000/health && curl -s http://localhost:8080 && curl -s http://localhost:6333/health
make test
make logs 2>&1 | grep -i error
```

## Parallelism Classification

Before parallel agents: classify destructive (writes files) vs non-destructive (reads only).
Non-destructive → parallel freely. Destructive → only if different file domains. See orchestrator.md.
