#!/bin/bash
# Enforce Rule 1: No autonomous filesystem exploration
INPUT=$(cat)
CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Block patterns: ls alone, ls with flags but no specific path, find from root/dot, tree
if echo "$CMD" | grep -qE '^\s*(ls\s*$|ls\s+-[a-zA-Z]+\s*$|find\s+[./]|tree\s*$|tree\s+-|du\s+-|locate\s)'; then
  echo "BLOCKED (Rule 1): Autonomous filesystem exploration forbidden. Use mcp__serena__get_symbols_overview or mcp__serena__find_file instead." >&2
  exit 2
fi
