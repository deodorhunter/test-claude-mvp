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
