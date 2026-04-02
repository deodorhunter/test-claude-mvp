# Rule 009 — Serena-First Code Navigation

## Constraint

Before reading any file for structure or symbol location, use Serena MCP tools. Fall back to full-file `Read`/`cat` ONLY when injecting raw content into a sub-agent `<file>` XML block.

## Serena Priority Order

1. `serena__get_symbols_overview(file)` — signatures only (~200 tokens vs ~2,000 per file)
2. `serena__find_symbol(name)` — file path + line number (~50 tokens)
3. `serena__read_file(file, start_line, end_line)` — targeted range after locating symbol
4. `serena__get_diagnostics(file)` — type errors BEFORE running tests (prevents circuit breaker)
5. Full `Read`/`cat` — ONLY for `<file>` XML injection into sub-agent prompts

## Context

Two Explore agents in Phase 2c–2d returned 63k + 68k = 131k tokens for what were class names and file locations. `serena__get_symbols_overview` returns the same in ~200 tokens per file. This rule eliminates Explore agents for structural mapping entirely.
