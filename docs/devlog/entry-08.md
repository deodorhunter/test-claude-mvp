← [Back to DEVLOG index](../DEVLOG.md)

## Entry 8 — Token Optimization Benchmarks

After implementing the governance layer, we measured actual token usage:

| Configuration | Auto-loaded bytes | Notes |
|---|---|---|
| Baseline (monolithic CLAUDE.md) | ~68,000 (pre-benchmark estimate) | All rules inline |
| v1 (agents extracted) | ~60,764 | Agents loaded per-invocation |
| v2 (path-scoped rules + skills) | 36,878 | Conditional loading |
| Effective (unconditional only) | 32,936 | What actually loads for most tasks |

Result: **−46% from baseline** (60,764 → 32,936 bytes — see benchmark/results/) for typical tasks. For tasks that don't touch the specialized domains (auth, migrations, MCP), the saving is higher.

The CLAUDE.md itself went from ~450 lines to ~120 lines. The orchestrator agent went from a monolithic 2,500-token file to a 2,147-token core with a 745-token delegation skill loaded on demand.

Prompt caching (Claude's `cache_control` on system blocks) provides an additional 60–90% reduction on repeated context across a session — measured via `cache_read_tokens` tracking in the model layer.

---
