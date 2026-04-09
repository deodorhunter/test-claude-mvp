#!/usr/bin/env bash
# tool-routing-guard.sh — PreToolUse hook (non-blocking, always exits 0)
#
# PURPOSE: Intercept MCP navigation tool calls at decision time and redirect to the
# correct backend tool if the wrong one was selected. This is Layer 2 of the 3-layer
# navigation enforcement system. Fires for every mcp__serena__* and mcp__codebase-memory-mcp__* call.
#
# Why non-blocking (exit 0):
#   Blocking would prevent legitimate cross-backend calls (e.g. using Serena's
#   replace_symbol_body when backend=cbm is correct for editing). Advisory redirect
#   at call time is the right intervention — firm message, Claude retains discretion
#   for edge cases.
#
# Source of truth: .claude/settings.json → mcpServers.codebase-memory-mcp.env.NAVIGATION_BACKEND

INPUT=$(cat)

# Extract tool name from PreToolUse hook JSON input
TOOL=$(echo "$INPUT" | python3 -c \
  "import sys, json; d=json.load(sys.stdin); print(d.get('tool_name', ''))" \
  2>/dev/null || echo "")

# Only act on MCP navigation tools — bail early on everything else
if ! echo "$TOOL" | grep -qE "^mcp__(serena|codebase-memory-mcp)__"; then
  exit 0
fi

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Read NAVIGATION_BACKEND from settings.json; shell env overrides
_SETTINGS_BACKEND=$(python3 -c "
import json
try:
    d = json.load(open('${PROJECT_ROOT}/.claude/settings.json'))
    val = d.get('mcpServers', {}).get('codebase-memory-mcp', {}).get('env', {}).get('NAVIGATION_BACKEND', 'serena')
    print(val)
except Exception:
    print('serena')
" 2>/dev/null || echo "serena")
BACKEND="${NAVIGATION_BACKEND:-$_SETTINGS_BACKEND}"

# ── backend=serena: warn if CBM search tool called ────────────────────────────
if [ "$BACKEND" = "serena" ] && echo "$TOOL" | grep -q "^mcp__codebase-memory-mcp__"; then
  echo "<system_warning>ROUTING REDIRECT: backend=serena but called ${TOOL}. "\
"Use mcp__serena__find_symbol or get_symbols_overview for this query instead. "\
"CBM tools are not the active backend.</system_warning>"
  exit 0
fi

# ── backend=cbm: warn if Serena search/overview called (editing tools OK) ─────
if [ "$BACKEND" = "cbm" ] && \
   echo "$TOOL" | grep -qE "^mcp__serena__(get_symbols_overview|find_symbol|search_for_pattern|find_referencing_symbols|list_dir|find_file)"; then
  echo "<system_warning>ROUTING REDIRECT: backend=cbm but called ${TOOL}. "\
"Use mcp__codebase-memory-mcp__search_codebase (or equivalent CBM tool) for search tasks. "\
"Serena editing tools (replace_symbol_body, get_errors) remain permitted.</system_warning>"
  exit 0
fi

# ── backend=both: warn if Serena used for wide search (editing OK) ────────────
if [ "$BACKEND" = "both" ] && \
   echo "$TOOL" | grep -qE "^mcp__serena__(search_for_pattern|find_referencing_symbols|find_file|list_dir)"; then
  echo "<system_warning>ROUTING REDIRECT (both): Wide search called via Serena (${TOOL}). "\
"Use mcp__codebase-memory-mcp__ for search/memory tasks. "\
"Reserve Serena for: replace_symbol_body, get_symbols_overview (targeted), get_errors.</system_warning>"
  exit 0
fi

exit 0
