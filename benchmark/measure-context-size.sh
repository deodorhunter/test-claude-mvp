#!/usr/bin/env bash
# measure-context-size.sh — Measures total auto-loaded context size for Claude Code sessions.
# Usage: ./benchmark/measure-context-size.sh [baseline|optimized]
# Output: Itemized byte counts + estimated tokens for all auto-loaded files.
# Token estimation: 1 token ≈ 4 bytes (Anthropic Claude tokenizer approximation).

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
MODE="${1:-baseline}"
OUTPUT_FILE="$PROJECT_ROOT/benchmark/results/${MODE}.txt"
TOTAL=0

# ── Helpers ───────────────────────────────────────────────────────────────────
print_file() {
  local label="$1" path="$2"
  if [ -f "$path" ]; then
    local bytes
    bytes=$(wc -c < "$path" | tr -d ' ')
    local tokens=$(( bytes / 4 ))
    printf "  %-35s %8d bytes  (~%6d tokens)\n" "$label" "$bytes" "$tokens"
    TOTAL=$((TOTAL + bytes))
  else
    printf "  %-35s %8s\n" "$label" "MISSING"
  fi
}

print_dir() {
  local label="$1" dir="$2" pattern="${3:-*.md}"
  if [ -d "$dir" ]; then
    local bytes
    bytes=$(find "$dir" -maxdepth 1 -name "$pattern" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    local count
    count=$(find "$dir" -maxdepth 1 -name "$pattern" 2>/dev/null | wc -l | tr -d ' ')
    local tokens=$(( bytes / 4 ))
    printf "  %-35s %8d bytes  (~%6d tokens)  [%d files]\n" "$label" "$bytes" "$tokens" "$count"
    TOTAL=$((TOTAL + bytes))
  else
    printf "  %-35s %8s\n" "$label" "MISSING"
  fi
}

# ── Main ──────────────────────────────────────────────────────────────────────
{
  echo "═══════════════════════════════════════════════════════════════"
  echo "  CONTEXT SIZE MEASUREMENT — $(echo "$MODE" | tr '[:lower:]' '[:upper:]')"
  echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
  echo "  Project: $PROJECT_ROOT"
  echo "═══════════════════════════════════════════════════════════════"
  echo ""

  echo "── Auto-loaded instruction files ──────────────────────────────"
  echo ""
  print_file "CLAUDE.md" "$PROJECT_ROOT/CLAUDE.md"
  print_file "orchestrator.md" "$PROJECT_ROOT/.claude/agents/orchestrator.md"
  print_file "product-owner.md" "$PROJECT_ROOT/.claude/agents/product-owner.md"
  print_dir  "Rules (project/)" "$PROJECT_ROOT/.claude/rules/project" "rule-*.md"
  print_file "Rules README" "$PROJECT_ROOT/.claude/rules/README.md"

  echo ""
  echo "── Referenced files (loaded per session) ──────────────────────"
  echo ""
  print_file "workflow.md" "$PROJECT_ROOT/.claude/workflow.md"
  print_file "AI_REFERENCE.md" "$PROJECT_ROOT/docs/AI_REFERENCE.md"

  echo ""
  echo "── Hooks ──────────────────────────────────────────────────────"
  echo ""
  print_dir  "Hook scripts (.claude/hooks/)" "$PROJECT_ROOT/.claude/hooks" "*.sh"

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  TOTAL_TOKENS=$((TOTAL / 4))
  printf "  TOTAL AUTO-LOADED:                 %8d bytes  (~%6d tokens)\n" "$TOTAL" "$TOTAL_TOKENS"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

} 2>&1 | tee "$OUTPUT_FILE"

echo ""
echo "Results saved to: $OUTPUT_FILE"
