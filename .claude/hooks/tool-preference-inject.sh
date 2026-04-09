#!/usr/bin/env bash
# tool-preference-inject.sh — UserPromptSubmit hook (non-blocking, always exits 0)
#
# PURPOSE: Inject a strict navigation dispatch table into Claude's context at the
# start of every prompt. This is Layer 1 of the 3-layer navigation enforcement:
#
#   Layer 1 (this file) — UserPromptSubmit: session-level dispatch announcement
#   Layer 2 (tool-routing-guard.sh) — PreToolUse: per-call redirect at decision point
#   Layer 3 (block-exploration.sh) — PreToolUse/Bash: hard block on filesystem exploration
#
# Source of truth: .claude/settings.json → mcpServers.codebase-memory-mcp.env.NAVIGATION_BACKEND
# Developer override: export NAVIGATION_BACKEND=cbm before launching Claude Code

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read NAVIGATION_BACKEND from settings.json (committed team default)
_SETTINGS_BACKEND=$(python3 -c "
import json, sys
try:
    d = json.load(open('${PROJECT_ROOT}/.claude/settings.json'))
    val = d.get('mcpServers', {}).get('codebase-memory-mcp', {}).get('env', {}).get('NAVIGATION_BACKEND', 'serena')
    print(val)
except Exception:
    print('serena')
" 2>/dev/null || echo "serena")

# Shell env var overrides settings.json (developer per-session override)
BACKEND="${NAVIGATION_BACKEND:-$_SETTINGS_BACKEND}"

case "$BACKEND" in
  cbm)
    cat <<'MSG'
<system_warning>Navigation backend: CBM (codebase-memory-mcp) — auto-indexed, cross-session SQLite.
DISPATCH (follow strictly):
  search / find / cross-session queries → mcp__codebase-memory-mcp__* tools
  symbol body editing only             → mcp__serena__replace_symbol_body (permitted)
DO NOT call mcp__serena__get_symbols_overview or find_symbol — use CBM search instead.
tool-routing-guard.sh monitors every MCP call and will redirect if wrong tool used.</system_warning>
MSG
    ;;
  both)
    cat <<'MSG'
<system_warning>Navigation backend: BOTH (Serena + CBM active) — strict dispatch required.
DISPATCH (follow strictly):
  SERENA ONLY → replace_symbol_body, get_errors  (symbol editing + error checking)
  CBM ONLY    → search_codebase, get_symbol, find_files, call_path  (search / memory / analysis)
  Read/Grep/Glob → forbidden except as final fallback after both MCP tools miss
Mixing backends for the same task wastes tokens. tool-routing-guard.sh enforces this.</system_warning>
MSG
    ;;
  *)
    # Default: serena
    cat <<'MSG'
<system_warning>Navigation backend: SERENA (session-scoped AST navigation).
DISPATCH (follow strictly):
  list_memories → get_symbols_overview → find_symbol → replace_symbol_body → Read (targeted)
DO NOT call mcp__codebase-memory-mcp__ search tools — Serena is the active backend.
tool-routing-guard.sh monitors every MCP call and will redirect if wrong tool used.</system_warning>
MSG
    ;;
esac

exit 0
