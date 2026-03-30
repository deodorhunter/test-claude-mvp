#!/usr/bin/env bash
# post-tool-truncate.sh — PostToolUse hook that warns about verbose Bash outputs.
# Registered in .claude/settings.json as PostToolUse hook.
# Detects noisy tool outputs and emits a truncation reminder.
#
# Note: Claude Code hooks cannot modify tool output directly. This hook
# detects verbose patterns in the tool input (command) and emits guidance
# to remind the agent to use quiet flags. The actual output suppression
# happens via Rule 2 in CLAUDE.md (SILENCE VERBOSE OUTPUTS).

set -euo pipefail

# Read hook input from stdin (JSON with tool_name, tool_input, etc.)
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# Only intercept Bash tool calls
if [ "$TOOL_NAME" != "Bash" ]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Check for noisy commands that should use quiet flags
NOISY=false
SUGGESTION=""

case "$COMMAND" in
  *"pip install"*)
    if [[ "$COMMAND" != *"-q"* && "$COMMAND" != *"--quiet"* && "$COMMAND" != *">/dev/null"* ]]; then
      NOISY=true
      SUGGESTION="pip install -q ... >/dev/null 2>&1"
    fi
    ;;
  *"npm install"*)
    if [[ "$COMMAND" != *"--silent"* && "$COMMAND" != *">/dev/null"* ]]; then
      NOISY=true
      SUGGESTION="npm install --silent 2>/dev/null"
    fi
    ;;
  *"docker build"*)
    if [[ "$COMMAND" != *"-q"* && "$COMMAND" != *"--quiet"* ]]; then
      NOISY=true
      SUGGESTION="docker build -q ."
    fi
    ;;
  *"alembic upgrade"*)
    if [[ "$COMMAND" != *"tail"* && "$COMMAND" != *">/dev/null"* ]]; then
      NOISY=true
      SUGGESTION="alembic upgrade head 2>&1 | tail -5"
    fi
    ;;
  *"docker compose up"*)
    if [[ "$COMMAND" != *"-d"* ]]; then
      NOISY=true
      SUGGESTION="docker compose up -d --build (use detached mode)"
    fi
    ;;
  *"pytest"*)
    if [[ "$COMMAND" != *"-q"* && "$COMMAND" != *"--tb=short"* && "$COMMAND" != *"--tb=no"* ]]; then
      NOISY=true
      SUGGESTION="pytest -q --tb=short"
    fi
    ;;
esac

if [ "$NOISY" = true ]; then
  echo "<system_warning>Verbose command detected. Use quiet flags to reduce context tokens: $SUGGESTION (CLAUDE.md Rule 2)</system_warning>"
fi

exit 0
