#!/bin/bash
# Enforce Rule 1: No autonomous filesystem exploration (exit 2 = hard block)
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Block patterns: ls alone, ls with flags but no specific path, find from root/dot, tree
if echo "$CMD" | grep -qE '^\s*(ls\s*$|ls\s+-[a-zA-Z]+\s*$|find\s+[./]|tree\s*$|tree\s+-|du\s+-|locate\s)'; then
  # Suggest the correct tool for the active navigation backend
  PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  _SB=$(python3 -c "
import json
try:
    d = json.load(open('${PROJECT_ROOT}/.claude/settings.json'))
    print(d.get('mcpServers',{}).get('codebase-memory-mcp',{}).get('env',{}).get('NAVIGATION_BACKEND','serena'))
except: print('serena')
" 2>/dev/null || echo "serena")
  BACKEND="${NAVIGATION_BACKEND:-$_SB}"
  case "$BACKEND" in
    cbm|both) NAV="mcp__codebase-memory-mcp__search_codebase or mcp__codebase-memory-mcp__find_files" ;;
    *) NAV="mcp__serena__get_symbols_overview, find_symbol, or find_file" ;;
  esac
  echo "BLOCKED (Rule 1): Autonomous filesystem exploration forbidden. Use ${NAV} instead. If MCP unavailable, use Grep/Read/Glob tools." >&2
  exit 2
fi
