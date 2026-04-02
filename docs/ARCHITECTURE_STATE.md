# Architecture State

> Single source of truth for completed work and token metrics.
> DocWriter appends after every US. Do not edit manually.
> Uses append-only operations (`>>`) — never overwrite.

## Token Metrics

| US | Agent | Model | Input Tokens | Output Tokens | Cache Read | Cache Creation | Date |
|---|---|---|---|---|---|---|---|

## Completed User Stories

<!-- DocWriter appends 3-line summaries below, newest last -->
| US-013 | AI/ML Engineer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-03-29 |

### US-013 — Cost-Aware Planner
**Date:** 2026-03-29 | **Agent:** AI/ML Engineer | **What was built:** Quota-guarded model selection with primary→Claude fallback chain, ExecutionPlan artifact for cost tracking.
| US-014 | AI/ML Engineer | claude-haiku-4-5-20251001 | ~55000 | ~6000 | unavailable | unavailable | 2026-03-29 |

### US-014 — MCP Registry + Trust Scoring
**Date:** 2026-03-29 | **Agent:** AI/ML Engineer | **What was built:** MCPRegistry with trust-score filtering, two stub servers (internal_docs/web), audit logging per server, 17 tests green.
| US-015 | AI/ML Engineer | claude-haiku-4-5-20251001 | ~54000 | ~6300 | unavailable | unavailable | 2026-03-29 |

### US-015 — Context Builder + Prompt Injection Defense
**Date:** 2026-03-29 | **Agent:** AI/ML Engineer | **What was built:** MCP query aggregation with source attribution, prompt injection blocking (9 patterns), HTML stripping, 3s per-server timeout, audit logging.
| US-016 | AI/ML Engineer | claude-haiku-4-5-20251001 | ~57000 | ~6000 | N/A | N/A | 2026-03-29 |

### US-016 — RAG Pipeline: Qdrant + Embedding Service
**Date:** 2026-03-29 | **Agent:** AI/ML Engineer | **What was built:** Multi-tenant RAG pipeline with EmbeddingService (Ollama nomic-embed-text), QdrantStore with per-tenant vector collections, RAGPipeline orchestrator, 30 tests passing, tenant isolation verified.
| US-017 | Backend Dev | claude-haiku-4-5-20251001 | ~85000 | ~9833 | 0 | 0 | 2026-03-30 |

### US-017 — Token Quota Tracking + Rate Limiting
**Date:** 2026-03-30 | **Agent:** Backend Dev | **What was built:** RateLimiter (Redis sliding window, 10 req/60s) + QuotaService (PostgreSQL tracking, fail-open on DB error), 8 tests green, 186 total.
| 2026-03-30 | US-018 | Security Engineer | claude-sonnet-4-6 | ~55000 | ~8643 | 0 | 0 | Token rotation JTI + 10 injection patterns + 27 security tests; 213 tests green |

### US-018 — Security Hardening: Token Rotation & Injection Patterns
**Date:** 2026-03-30 | **Agent:** Security Engineer | **What was built:** Refresh token JTI-based replay prevention + 10 new injection pattern signatures + 27-test security suite
| US-019 | QA Engineer (direct) | claude-sonnet-4-6 | ~15k | ~8k | 0 | 0 | 2026-03-31 |

### US-019 — Phase 2 Test Coverage
**Date:** 2026-03-31 | **Agent:** Tech Lead direct | **What was built:** 61 tests across 6 files covering plugin lifecycle, model layer, MCP trust filtering, RAG pipeline, planner integration, E2E mock flow. All verdi su 286 totali.
| US-020 | Tech Lead direct | claude-sonnet-4-6 | ~25k | ~12k | 0 | 0 | 2026-03-31 |

### US-020 — plone-mcp Self-Hosted Integration
**Date:** 2026-03-31 | **Agent:** Tech Lead direct | **What was built:** plone-mcp Node.js upstream clonato in infra/plone-mcp/, SSE transport patch (~25 righe in run()), Dockerfile.plone-mcp multi-stage Node.js 20-alpine, servizio docker-compose porta 9120, PloneMCPServer Python adapter (Plone REST API /@search), MCP_ALLOWLIST in registry.py, 12 test nuovi + 0 regressioni su 286.

---

## Phase 2 Architecture Summary (DocWriter Mode B — 2026-03-31)

### What Phase 2 Built

Phase 2 ha realizzato il core platform completo su cui si basa Phase 3 (API + Frontend):

**Plugin System (2a):** Hot-plug manifest-based plugin manager con subprocess isolation, resource limits, e tenant isolation. Plugin caricabili a runtime per singolo tenant.

**Model Layer (2b):** Adapter unificato (Ollama locale + Claude cloud) con interfaccia `generate()` stabile. Cost-aware planner con quota enforcement, fallback chain primario→Claude, e ExecutionPlan per tracking costo.

**MCP + RAG (2c):** MCPRegistry con trust-score filtering e audit logging. ContextBuilder con source attribution, prompt injection defense (10 pattern), HTML stripping, timeout 3s/server. RAG pipeline multi-tenant su Qdrant con EmbeddingService (nomic-embed-text).

**Quota + Security + Tests (2d):** RateLimiter Redis sliding-window, QuotaService PostgreSQL, refresh token JTI rotation, 17 injection pattern signatures. 286 test verdi. plone-mcp self-hosted su porta 9120 (SSE transport), Python adapter integrato nel MCP registry.

### Key Architectural Decisions

| Decisione | Rationale |
|---|---|
| plone-mcp doppia architettura (Node.js + Python adapter) | Node.js per Claude Desktop esterno; Python per registry interno senza proxy overhead |
| MCPRegistry allowlist opt-in (`allowlist=` param) | Backward compat test esistenti; prod istanzia con `allowlist=MCP_ALLOWLIST` |
| PloneMCPServer chiama Plone REST API direttamente | Evita latenza proxy Node.js→Python; Node.js è per client esterni |
| SSE patch minima a upstream index.ts (~25 righe) | `TRANSPORT=sse` env var; stdio originale invariato; no fork |

### Interface Contracts (stable, Phase 3 consumes)

```python
# Planner
plan = await planner.plan(query, tenant_id, context)  # → ExecutionPlan
response = await planner.execute(plan)                 # → ModelResponse

# MCP Registry
results = await registry.query_all(text, audit_service, tenant_id)  # → list[MCPResult]

# RAG Pipeline
await pipeline.index_document(tenant_id, doc_id, text)
chunks = await pipeline.query(tenant_id, query, top_k=5)  # → list[RAGChunk]

# Quota
await quota_service.check_and_consume(tenant_id, tokens)  # raises QuotaExceededError

# PloneMCPServer (new)
result = await plone_server.query(input_text)  # → MCPResult(data, source, confidence=0.85)
```

### Phase 3 Entry Conditions (all met)

- [x] `make test` → 286 passed, 0 failed
- [x] `make migrate` → no pending migrations
- [x] API health → 200 OK
- [x] plone-mcp SSE → stream aperto porta 9120
- [x] Tutti US Phase 2 ✅ Done
| US-067 | doc-writer | claude-haiku-4-5-20251001 | 15000 | 3500 | 0 | 0 | 2026-04-02 |

### US-067 — Optimize File Context Injection for Doc Tasks
**Date:** 2026-04-02 | **Agent:** doc-writer | **What was built:** Updated doc-writer agent prompt with symbol-based context injection guidance and added AI_REFERENCE.md subsection with token savings estimates.

| US-054 | Doc Writer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-054 — Cognitive Patterns Documentation
**Date:** 2026-04-02 | **Agent:** Doc Writer | **What was built:** Catalog of 5 cognitive patterns (learn, judge, notepad, reflexion, deep-interview) with trigger conditions, token costs, and automation potential assessment.

| US-055 | QA Engineer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-055 — Doc Verification CI Script
**Date:** 2026-04-02 | **Agent:** QA Engineer | **What was built:** Bash-only `benchmark/verify-docs.sh` validates HTTP links, port mappings, US file references, rule frontmatter; `make verify-docs` target added.

| US-056 | AI/ML Engineer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-056 — Context Compression Hook Automation
**Date:** 2026-04-02 | **Agent:** AI/ML Engineer | **What was built:** `.claude/hooks/auto-compress.sh` advisory triggers on tool-call threshold and parallel waves; rule-010 updated; docs integrated.

| US-066 | DevOps/Infra | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-066 — Serena MCP .git/ Ignore Configuration
**Date:** 2026-04-02 | **Agent:** DevOps/Infra | **What was built:** `.claude/settings.json` configured to ignore `.git/`, `node_modules/`, `__pycache__/` paths; rule-019 operational; index.lock contention resolved.

| US-067 | Doc Writer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-067 — Symbol-First Context Injection Guidance
**Date:** 2026-04-02 | **Agent:** Doc Writer | **What was built:** doc-writer.md delegation template updated with serena__get_symbols_overview pattern vs. full Read; estimated 10k tokens/phase savings documented.

| US-068 | Product Owner | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-068 — Pre-Collected Command Catalog Reference
**Date:** 2026-04-02 | **Agent:** Product Owner | **What was built:** `docs/.command-catalog.md` pre-collected from `.claude/commands/` audit; delegation templates updated to reference (not regenerate); estimated 3k tokens/delegation savings.

| US-065 | Doc Writer | claude-haiku-4-5-20251001 | N/A | N/A | N/A | N/A | 2026-04-02 |

### US-065 — Backlog Refinement Ceremony + Skill + Rule-018
**Date:** 2026-04-02 | **Agent:** Doc Writer | **What was built:** `/refine-backlog` command + skill, rule-018 (pre-sprint yes-man filter), refinement ceremony operational for Phase 3c+.
