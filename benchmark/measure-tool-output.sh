#!/usr/bin/env bash
# measure-tool-output.sh — Samples typical tool output sizes to quantify truncation savings.
# Usage: ./benchmark/measure-tool-output.sh
# This simulates the output volume of common noisy commands.

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TRUNCATE_LINES=10  # PostToolUse hook target

echo "═══════════════════════════════════════════════════════════════"
echo "  TOOL OUTPUT BLOAT ANALYSIS"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Truncation target: last $TRUNCATE_LINES lines"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── Simulate common noisy outputs ────────────────────────────────────────────
simulate() {
  local label="$1"
  local cmd="$2"

  # Capture output
  local output
  output=$(eval "$cmd" 2>&1 || true)
  local total_lines
  total_lines=$(echo "$output" | wc -l | tr -d ' ')
  local total_bytes
  total_bytes=$(echo "$output" | wc -c | tr -d ' ')
  local total_tokens=$((total_bytes / 4))

  # Truncated version
  local trunc_output
  trunc_output=$(echo "$output" | tail -n "$TRUNCATE_LINES")
  local trunc_bytes
  trunc_bytes=$(echo "$trunc_output" | wc -c | tr -d ' ')
  local trunc_tokens=$((trunc_bytes / 4))

  local saved_tokens=$((total_tokens - trunc_tokens))
  local pct=0
  if [ "$total_tokens" -gt 0 ]; then
    pct=$((saved_tokens * 100 / total_tokens))
  fi

  printf "  %-35s  %5d lines → %2d lines  (%'5d → %'4d tokens, -%d%%)\n" \
    "$label" "$total_lines" "$TRUNCATE_LINES" "$total_tokens" "$trunc_tokens" "$pct"
}

echo "── Simulated command outputs ────────────────────────────────"
echo ""

# pip install simulation (use pip list as proxy for verbose output)
simulate "pip install (simulated)" "pip3 list 2>/dev/null"

# docker compose config (proxy for docker build verbosity)
if [ -f "$PROJECT_ROOT/infra/docker-compose.yml" ]; then
  simulate "docker compose config" "docker compose -f $PROJECT_ROOT/infra/docker-compose.yml config 2>/dev/null"
fi

# git log (verbose)
simulate "git log --oneline -50" "git -C $PROJECT_ROOT log --oneline -50 2>/dev/null"

# npm list (proxy for npm install output)
simulate "npm list (simulated)" "npm list --all 2>/dev/null || echo 'npm not in this project'"

# alembic history (proxy for migration output)
if [ -d "$PROJECT_ROOT/backend/alembic" ]; then
  simulate "alembic versions listing" "find $PROJECT_ROOT/backend/alembic/versions -name '*.py' -exec head -3 {} +"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Hook: .claude/hooks/post-tool-truncate.sh"
echo "  Applied via: PostToolUse in .claude/settings.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
