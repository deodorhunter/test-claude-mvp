#!/usr/bin/env bash
# compare.sh — Compares baseline vs optimized context measurements.
# Usage: ./benchmark/compare.sh
# Prerequisite: Run measure-context-size.sh for both baseline and optimized first.

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
BASELINE="$PROJECT_ROOT/benchmark/results/baseline.txt"
OPTIMIZED="$PROJECT_ROOT/benchmark/results/optimized.txt"

if [ ! -f "$BASELINE" ]; then
  echo "ERROR: Baseline results not found. Run: ./benchmark/measure-context-size.sh baseline"
  exit 1
fi

if [ ! -f "$OPTIMIZED" ]; then
  echo "ERROR: Optimized results not found. Run: ./benchmark/measure-context-size.sh optimized"
  exit 1
fi

# Extract total bytes from result files
extract_total() {
  grep "TOTAL AUTO-LOADED:" "$1" | grep -o '[0-9]*' | head -1
}

BASELINE_BYTES=$(extract_total "$BASELINE")
OPTIMIZED_BYTES=$(extract_total "$OPTIMIZED")

if [ -z "$BASELINE_BYTES" ] || [ "$BASELINE_BYTES" -eq 0 ]; then
  echo "ERROR: Could not parse baseline total."
  exit 1
fi

SAVED=$((BASELINE_BYTES - OPTIMIZED_BYTES))
PCT=$((SAVED * 100 / BASELINE_BYTES))
BASELINE_TOKENS=$((BASELINE_BYTES / 4))
OPTIMIZED_TOKENS=$((OPTIMIZED_BYTES / 4))
SAVED_TOKENS=$((SAVED / 4))

echo "═══════════════════════════════════════════════════════════════"
echo "  CONTEXT SIZE COMPARISON"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════"
echo ""
printf "  Baseline:   %'8d bytes  (~%'6d tokens)\n" "$BASELINE_BYTES" "$BASELINE_TOKENS"
printf "  Optimized:  %'8d bytes  (~%'6d tokens)\n" "$OPTIMIZED_BYTES" "$OPTIMIZED_TOKENS"
printf "  Saved:      %'8d bytes  (~%'6d tokens)\n" "$SAVED" "$SAVED_TOKENS"
echo ""

if [ "$PCT" -ge 35 ]; then
  echo "  RESULT: ${PCT}% reduction — TARGET MET (≥35%)"
else
  echo "  RESULT: ${PCT}% reduction — TARGET NOT MET (need ≥35%)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Per-agent savings (if agent injection results exist)
echo ""
echo "Run ./benchmark/measure-agent-injection.sh for per-agent breakdown."
