#!/usr/bin/env bash
# measure-agent-injection.sh — Measures per-agent rule injection overhead.
# Shows how many bytes/tokens of rules each agent type would receive
# under baseline (all rules) vs optimized (scoped rules) strategies.
#
# Usage: ./benchmark/measure-agent-injection.sh [--detail]

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
RULES_DIR="$PROJECT_ROOT/.claude/rules/project"
DETAIL="${1:-}"

# ── Rule file sizes ───────────────────────────────────────────────────────────
rule_size() {
  local rule="$1"
  local path="$RULES_DIR/rule-${rule}.md"
  if [ -f "$path" ]; then
    wc -c < "$path" | tr -d ' '
  else
    echo "0"
  fi
}

all_rules_size() {
  find "$RULES_DIR" -name "rule-*.md" -exec cat {} + 2>/dev/null | wc -c | tr -d ' '
}

# ── Agent rule mappings (optimized) ──────────────────────────────────────────
# Format: "agent_name:rule1,rule2,..."
AGENT_RULES=(
  "Backend Dev:001-tenant-isolation,002-migration-before-model"
  "AI/ML Engineer:001-tenant-isolation,011-eu-ai-act-data-boundary"
  "Security Engineer:001-tenant-isolation,011-eu-ai-act-data-boundary"
  "DevOps/Infra:008-pre-edit-read-docker-baked-files"
  "DocWriter:005-docwriter-no-multiline-bash"
  "QA Engineer:005-docwriter-no-multiline-bash,006-no-qa-mode-a-subagents"
  "Frontend Dev:001-tenant-isolation"
)

# ── Measurement ───────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  AGENT INJECTION OVERHEAD COMPARISON"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════"
echo ""

BASELINE_TOTAL=$(all_rules_size)
BASELINE_TOKENS=$((BASELINE_TOTAL / 4))

echo "── Baseline: ALL rules injected per agent ───────────────────"
printf "  All rules total:  %'8d bytes  (~%'6d tokens)\n" "$BASELINE_TOTAL" "$BASELINE_TOKENS"
echo ""

echo "── Optimized: Scoped rules per agent ────────────────────────"
echo ""

TOTAL_BASELINE_ACROSS_AGENTS=0
TOTAL_OPTIMIZED_ACROSS_AGENTS=0

printf "  %-22s  %10s  %10s  %10s  %8s\n" "Agent" "Baseline" "Optimized" "Saved" "Saving%"
printf "  %-22s  %10s  %10s  %10s  %8s\n" "─────" "────────" "─────────" "─────" "───────"

for entry in "${AGENT_RULES[@]}"; do
  agent="${entry%%:*}"
  rules_csv="${entry#*:}"

  # Optimized: sum only scoped rules
  opt_bytes=0
  IFS=',' read -ra RULES <<< "$rules_csv"
  rule_list=""
  for rule in "${RULES[@]}"; do
    size=$(rule_size "$rule")
    opt_bytes=$((opt_bytes + size))
    rule_list="${rule_list}${rule_list:+, }$rule"
  done

  opt_tokens=$((opt_bytes / 4))
  saved=$((BASELINE_TOTAL - opt_bytes))
  if [ "$BASELINE_TOTAL" -gt 0 ]; then
    pct=$((saved * 100 / BASELINE_TOTAL))
  else
    pct=0
  fi

  printf "  %-22s  %'8d B  %'8d B  %'8d B  %6d%%\n" "$agent" "$BASELINE_TOTAL" "$opt_bytes" "$saved" "$pct"

  if [ "$DETAIL" = "--detail" ]; then
    printf "    Rules: %s\n" "$rule_list"
  fi

  TOTAL_BASELINE_ACROSS_AGENTS=$((TOTAL_BASELINE_ACROSS_AGENTS + BASELINE_TOTAL))
  TOTAL_OPTIMIZED_ACROSS_AGENTS=$((TOTAL_OPTIMIZED_ACROSS_AGENTS + opt_bytes))
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL_SAVED=$((TOTAL_BASELINE_ACROSS_AGENTS - TOTAL_OPTIMIZED_ACROSS_AGENTS))
if [ "$TOTAL_BASELINE_ACROSS_AGENTS" -gt 0 ]; then
  TOTAL_PCT=$((TOTAL_SAVED * 100 / TOTAL_BASELINE_ACROSS_AGENTS))
else
  TOTAL_PCT=0
fi
printf "  TOTAL across %d agents:\n" "${#AGENT_RULES[@]}"
printf "    Baseline:  %'8d bytes  (~%'6d tokens)\n" "$TOTAL_BASELINE_ACROSS_AGENTS" "$((TOTAL_BASELINE_ACROSS_AGENTS / 4))"
printf "    Optimized: %'8d bytes  (~%'6d tokens)\n" "$TOTAL_OPTIMIZED_ACROSS_AGENTS" "$((TOTAL_OPTIMIZED_ACROSS_AGENTS / 4))"
printf "    Saved:     %'8d bytes  (~%'6d tokens)  [%d%%]\n" "$TOTAL_SAVED" "$((TOTAL_SAVED / 4))" "$TOTAL_PCT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
