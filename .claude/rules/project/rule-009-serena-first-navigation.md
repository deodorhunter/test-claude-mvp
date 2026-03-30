# Rule 009 — Serena-First Code Navigation

## Constraint

When the Tech Lead needs to understand code structure, locate a symbol, or map a module before planning or delegating, use Serena MCP tools first. Fall back to full-file `Read`/`cat` ONLY when injecting raw content into a sub-agent `<file>` XML block, or when Serena is unavailable.

## Serena Tool Priority Order

1. `serena__get_symbols_overview(file)` — class/method names + signatures only (~200 tokens vs ~2,000 for full file). Use for "what does this file contain?"
2. `serena__find_symbol(name)` — file path + line number only (~50 tokens). Use for "where is X defined?"
3. `serena__read_file(file, start_line, end_line)` — only the lines needed after locating the symbol
4. `serena__search_semantic(query)` — find related code by meaning without knowing exact symbol names
5. `serena__get_diagnostics(file)` — real-time type errors BEFORE running tests (circuit breaker prevention)
6. Full `Read` / `cat` — last resort: only for full-file `<file>` XML injection, or when Serena is unavailable

## Context

In Phase 2c–2d planning, two Explore agents were spawned to map the codebase. They returned 63k + 68k = 131k tokens for what amounted to class names and file locations. `serena__get_symbols_overview` returns the same information in ~200 tokens per file. This rule eliminates the Explore-agent pattern entirely for structural mapping.

## When This Rule Does NOT Apply

- When assembling `<file>` XML blocks to inject into a sub-agent prompt: full file content is required. Serena summaries must not be used in place of raw file content for agent injection.
- When editing < 10 lines at a known location.

## Examples

✅ Correct:
```
serena__get_symbols_overview("ai/planner/planner.py")
→ 180 tokens: class CostAwarePlanner + 3 method signatures
→ Tech Lead knows the interface without reading 450 lines
```

✅ Correct (need one method body):
```
serena__find_symbol("CostAwarePlanner.select_model") → line 87
serena__read_file("ai/planner/planner.py", 87, 120) → 33 lines = ~400 tokens
(vs full file Read = ~5,500 tokens)
```

❌ Avoid:
```
Read("ai/planner/planner.py")                                    # 5,500 tokens to find one method
Agent(subagent_type="Explore", prompt="Summarize ai/planner/")   # 63,000 tokens
```
