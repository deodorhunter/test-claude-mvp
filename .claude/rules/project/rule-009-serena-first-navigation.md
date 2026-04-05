---
description: "Before reading any file for structure or symbol location"
---

<metadata>
  id: rule-009
  updated: "2026-04-04"
</metadata>

# Rule 009 — Serena-First Navigation

<constraint>
Before reading any file for structure, use Serena: `get_symbols_overview` (~200 tokens) → `find_symbol` (~50 tokens) → targeted `read_file` range. Full `Read`/`cat` ONLY for `<file>` XML injection.

Scope: Python and TypeScript files only (`.serena/project.yml`). Markdown, YAML, JSON, Dockerfile → use Read/Grep directly.

Sub-agents: Serena tool calls are NOT available in Agent-spawned sub-sessions (Claude Code limitation — confirmed 2026-04-04). See rule-010: orchestrator must run Serena pre-flight and inject `<symbols>` blocks before delegating.
</constraint>

<why>
Full-file reads cost ~2,000 tokens each. Serena overviews give the same structural info at 10% cost. Sub-agent Serena limitation costs ~1,800 tokens per file if orchestrator skips pre-flight injection.
</why>

<pattern>
✅ Main session: `mcp__serena__get_symbols_overview(file)` → inject `<symbols>` in delegation prompt → delegate
✅ Main session: `mcp__serena__find_symbol(name)` → targeted Read range
❌ Sub-agent prompt: "Use Serena to navigate before editing" — tool unavailable, wastes tokens on full Read
❌ `Read(whole_file)` in main session when Serena symbol overview suffices
</pattern>
