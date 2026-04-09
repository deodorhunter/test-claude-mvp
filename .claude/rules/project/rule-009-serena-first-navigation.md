---
description: "Navigation backend selection: Serena-first (default) or CBM, controlled by NAVIGATION_BACKEND in .claude/settings.json"
---

<metadata>
  id: rule-009
  updated: "2026-04-08"
</metadata>

# Rule 009 — Navigation Backend

<constraint>
Active navigation backend is set in `.claude/settings.json` → `mcpServers.codebase-memory-mcp.env.NAVIGATION_BACKEND` (values: `serena` | `cbm` | `both`, default: `serena`). The active dispatch table is injected by `tool-preference-inject.sh` at every prompt. Follow it strictly.

**Backend: `serena` (default)**
Before reading any file for structure: `get_symbols_overview` (~200 tokens) → `find_symbol` (~50 tokens) → targeted `read_file` range. Full `Read`/`cat` ONLY for `<file>` XML injection into DocWriter or algorithm-level detail.

**Backend: `cbm`**
Use `mcp__codebase-memory-mcp__*` for all search, navigation, and cross-session queries. Serena permitted only for `replace_symbol_body` and `get_errors`.

**Backend: `both`**
Strict dispatch — CBM for search/memory/analysis; Serena only for `replace_symbol_body` + `get_errors`. Never use same tool type from both backends for the same task.

Scope (Serena): Python and TypeScript files only. Markdown, YAML, JSON, Dockerfile → use Read/Grep directly.

Sub-agents: Serena IS available in sub-agents when agent frontmatter uses `disallowedTools` + inline `mcpServers`. If Serena unavailable in sub-agent, STOP and request orchestrator `<file>` injection.
</constraint>

<why>
Full-file reads cost ~2,000 tokens each; Serena overviews give same info at 10% cost. CBM adds persistent, auto-updated cross-session indexing (no manual `update-memories` flush needed). Tool confusion when both MCPs active is prevented by `tool-routing-guard.sh` PreToolUse hook + strict dispatch table in CLAUDE.md.
</why>

<pattern>
✅ Check injected dispatch table at prompt start (from tool-preference-inject.sh)
✅ backend=serena: `get_symbols_overview` → `find_symbol` → targeted Read
✅ backend=cbm: `cbm__search_codebase` → targeted Read
✅ backend=both: cbm for search, serena for editing only
❌ `Read(whole_file)` when MCP overview suffices
❌ Mixing backends for the same task type (wastes tokens, confuses indexing)
❌ Sub-agent falling back to `ls`/`find` when MCP unavailable — STOP and escalate
</pattern>
