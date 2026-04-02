# Session Cost Log
> Append-only. Updated by Tech Lead after each `/phase-retrospective` (phase gate).
> Estimates where actuals are unavailable — marked with `~`.
> Actuals come from agent invocation reports (input_tokens, output_tokens, cache_read_tokens).

| Data | Fase | Sessione | Agenti spawned | Token input (est.) | Token output (est.) | Token totali (est.) | Spreco evitabile | Note |
|---|---|---|---|---|---|---|---|---|
| 2026-03-29 | Phase 2b | US-013 Cost-Aware Planner + Ollama integration | 6 (Explore×2, AI/ML, DevOps, DocWriter, QA) | ~320,000 | ~90,000 | ~460,000 | ~145,000 (~32%) | Spreco: Explore agents×2 (~60k) + no AI_REFERENCE.md (~45k) + DocWriter multiline bash (~15k) + debug probe timeout (~25k). Fix applicati: rule-003/004/005 + 4 patch governance. |
| 2026-03-29 | Phase-2c | MCP Registry + Context Builder + RAG Pipeline (US-014/015/016) | 9 (AI/ML×3, DocWriter×3, QA×3-stalled) | ~520k | ~60k | ~580k | ~115k | Waste: QA sub-agents stalled×3 (~112k) + circuit breaker violation on docker exec loop + Phase Gate skip (jumped to 2d without retro). Fixes: skip QA sub-agents entirely (use Write+docker cp direct), circuit breaker discipline, Phase Gate 'proceed' means Gate steps first. |
| 2026-03-31 | Phase-2d | Test Coverage + Plone-MCP integration (US-019/020) | 0 sub-agents (direct impl) | ~snapshot: 109.5k active window | — | ~109.5k window snapshot | ~0 identified | ⚠️ snapshot only — not comparable to cumulative 2b/2c totals. Signal density 78.2% (vs ~55% 2b/2c). Zero rule violations detected. Gate completed 2026-03-31 — see row below for actuals. |
| 2026-03-31 | Phase-2d Gate | US-019 closure + US-020 plone-mcp + Phase Gate 2 | 2 Explore agents (direct impl per tutto il resto) | ~96k | ~29k | ~125k | ~4k (<4%) | Zero rule violations. 4 bugs introdotti e risolti entro 1 fix ciascuno. Direct implementation pattern: -82% tokens vs 2c. 286 test verdi. plone-mcp self-hosted funzionante. |
| 2026-04-02 | Phase-3a | Token optimization (US-051 model routing + US-053 orchestration patterns) | 2 (Doc Writer ×2) | ~45k | ~57k | ~102k | ~20k | Over-contextualization on doc tasks; reduced file injection + pre-collect commands for Phase 3b; rule-019 Serena-git isolation extracted |
