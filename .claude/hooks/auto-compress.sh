#!/usr/bin/env bash
# auto-compress.sh — Advisory compression hook (rule-010 automation).
# Fires on PostToolUse and PreToolUse to track tool-call counts and detect
# parallel sub-agent spawn patterns. Emits <system_warning> guidance when
# thresholds are crossed. NEVER blocks session flow (advisory only).
#
# Registered in .claude/settings.json:
#   PostToolUse  (all matchers) — increment tool-call counter
#   PreToolUse   (matcher: "Agent") — detect parallel wave spawn
#   SubagentStop (all matchers) — detect ≥2 parallel agent completions
#
# Configurable via env var:
#   COMPRESS_THRESHOLD — tool-call count before advisory fires (default: 12)

set -uo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
COMPRESS_THRESHOLD="${COMPRESS_THRESHOLD:-12}"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
STATE_DIR="${TMPDIR:-/tmp}/claude-compress-state"
mkdir -p "$STATE_DIR"

# Read hook input from stdin
INPUT=$(cat 2>/dev/null || echo "{}")

# Extract fields via python3 (available in all macOS/Linux environments)
HOOK_EVENT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('hook_event_name',''))" 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Sanitize session_id for use as filename (strip path traversal characters)
SESSION_SAFE=$(echo "$SESSION_ID" | tr -cd '[:alnum:]-_' | head -c 64)

COUNTER_FILE="$STATE_DIR/tool-count-${SESSION_SAFE}"
SUBAGENT_FILE="$STATE_DIR/subagent-count-${SESSION_SAFE}"

# ── PostToolUse: increment tool-call counter ──────────────────────────────────
if [ "$HOOK_EVENT" = "PostToolUse" ]; then
  # Read current count, default 0
  COUNT=0
  if [ -f "$COUNTER_FILE" ]; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null | tr -cd '[:digit:]' || echo 0)
  fi
  COUNT=$((COUNT + 1))
  echo "$COUNT" > "$COUNTER_FILE"

  if [ "$COUNT" -ge "$COMPRESS_THRESHOLD" ]; then
    echo "<system_warning>rule-010: Tool-call count has reached $COUNT (threshold: $COMPRESS_THRESHOLD). Run /compress-state → /clear before spawning parallel agents to avoid ${COMPRESS_THRESHOLD}0k+ token waste. Reset: delete $COUNTER_FILE or run /clear. (auto-compress.sh)</system_warning>"
    # Reset counter after warning to avoid repeated noise every tool call
    echo "0" > "$COUNTER_FILE"
  fi
  exit 0
fi

# ── PreToolUse (Agent): detect parallel wave about to be spawned ──────────────
if [ "$HOOK_EVENT" = "PreToolUse" ] && [ "$TOOL_NAME" = "Agent" ]; then
  # Read current count, default 0
  COUNT=0
  if [ -f "$COUNTER_FILE" ]; then
    COUNT=$(cat "$COUNTER_FILE" 2>/dev/null | tr -cd '[:digit:]' || echo 0)
  fi
  if [ "$COUNT" -ge 5 ]; then
    echo "<system_warning>rule-010: Agent spawn detected with $COUNT tool calls in context. If spawning ≥2 parallel agents, run /compress-state → /clear first to prevent multi-agent context multiplication. (auto-compress.sh)</system_warning>"
  fi
  exit 0
fi

# ── SubagentStop: track completed sub-agents, warn at ≥2 ─────────────────────
if [ "$HOOK_EVENT" = "SubagentStop" ]; then
  # Increment completed subagent count
  SA_COUNT=0
  if [ -f "$SUBAGENT_FILE" ]; then
    SA_COUNT=$(cat "$SUBAGENT_FILE" 2>/dev/null | tr -cd '[:digit:]' || echo 0)
  fi
  SA_COUNT=$((SA_COUNT + 1))
  echo "$SA_COUNT" > "$SUBAGENT_FILE"

  if [ "$SA_COUNT" -ge 2 ]; then
    echo "<system_warning>rule-010: $SA_COUNT parallel sub-agents have completed. Run /compress-state → /clear before reviewing results or spawning the next wave to prevent context bloat. (auto-compress.sh)</system_warning>"
    # Reset after warning
    echo "0" > "$SUBAGENT_FILE"
  fi
  exit 0
fi

# ── UserPromptSubmit: Phase Gate keyword detection ────────────────────────────
if [ "$HOOK_EVENT" = "UserPromptSubmit" ]; then
  PROMPT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('prompt','').lower())" 2>/dev/null || echo "")

  # Detect Phase Gate keywords per rule-010
  if echo "$PROMPT" | grep -qE "(phase gate|phase [0-9]+ gate|proceed to phase|mini.gate|phase gate opening)"; then
    echo "<system_warning>rule-010: Phase Gate detected in prompt. Complete ALL gate steps (orchestrator.md Phase 4) including /compress-state → /clear before starting the next phase. (auto-compress.sh)</system_warning>"
  fi
  exit 0
fi

exit 0
