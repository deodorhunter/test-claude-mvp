#!/usr/bin/env bash
# report-session-costs.sh
# Prints a markdown summary table of all captured session metrics.
# Optionally compares against the last estimate in docs/SESSION_COSTS.md.
# Data stays local — no network calls (EU AI Act rule-011 compliant).

set -euo pipefail

METRICS_DIR="$(dirname "${BASH_SOURCE[0]}")/session-metrics"

if [[ ! -d "${METRICS_DIR}" ]] || [[ -z "$(ls -A "${METRICS_DIR}"/*.json 2>/dev/null)" ]]; then
  echo "No sessions captured yet. Run: make benchmark-session"
  exit 0
fi

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is not installed. Install with: brew install jq" >&2
  exit 1
fi

# --- Print table header ---
echo ""
echo "## Session Cost Report"
echo ""
printf "| %-16s | %8s | %7s | %10s | %7s | %11s | %5s |\n" \
  "Date" "Input" "Output" "Cache Read" "Cache%" "Cost (est.)" "Drift"
printf "|%s|%s|%s|%s|%s|%s|%s|\n" \
  "------------------" "----------" "---------" "------------" "---------" "-------------" "-------"

# Accumulators
total_input=0
total_output=0
total_cache_read=0
total_cache_creation=0
total_cost=0
total_drift=0
count=0

for f in $(ls -t "${METRICS_DIR}"/*.json); do
  date_val=$(jq -r '.session_date' "${f}")
  input=$(jq -r '.input_tokens' "${f}")
  output=$(jq -r '.output_tokens' "${f}")
  cache_read=$(jq -r '.cache_read_tokens' "${f}")
  cache_pct=$(jq -r '.cache_read_ratio_pct' "${f}")
  cost=$(jq -r '.estimated_cost_usd' "${f}")
  drift=$(jq -r '.drift_signals_count' "${f}")

  printf "| %-16s | %8s | %7s | %10s | %6s%% | \$%10s | %5s |\n" \
    "${date_val}" "${input}" "${output}" "${cache_read}" "${cache_pct}" "${cost}" "${drift}"

  total_input=$((total_input + input))
  total_output=$((total_output + output))
  total_cache_read=$((total_cache_read + cache_read))
  total_drift=$((total_drift + drift))
  total_cost=$(echo "${total_cost} ${cost}" | awk '{printf "%.4f", $1 + $2}')
  count=$((count + 1))
done

# Totals row
avg_cost=$(echo "${total_cost} ${count}" | awk '{if ($2>0) printf "%.4f", $1/$2; else print "0.0000"}')
avg_cache_pct=$(echo "${total_input} ${total_cache_read}" | awk '{
  total = $1 + $2
  if (total == 0) { printf "0.0" }
  else { printf "%.1f", ($2 / total) * 100 }
}')

echo "|------------------|----------|---------|------------|---------|-------------|-------|"
printf "| %-16s | %8s | %7s | %10s | %6s%% | \$%10s | %5s |\n" \
  "TOTAL (${count} sess)" "${total_input}" "${total_output}" "${total_cache_read}" \
  "${avg_cache_pct}" "${total_cost}" "${total_drift}"
printf "| %-16s | %8s | %7s | %10s | %7s | \$%10s | %5s |\n" \
  "AVG per session" \
  "$(echo "${total_input} ${count}" | awk '{if ($2>0) printf "%d", $1/$2; else print 0}')" \
  "$(echo "${total_output} ${count}" | awk '{if ($2>0) printf "%d", $1/$2; else print 0}')" \
  "$(echo "${total_cache_read} ${count}" | awk '{if ($2>0) printf "%d", $1/$2; else print 0}')" \
  "${avg_cache_pct}%" \
  "${avg_cost}" \
  "$(echo "${total_drift} ${count}" | awk '{if ($2>0) printf "%d", $1/$2; else print 0}')"

# --- Compare against SESSION_COSTS.md ---
SESSION_COSTS_FILE="$(dirname "${BASH_SOURCE[0]}")/../docs/SESSION_COSTS.md"
if [[ -f "${SESSION_COSTS_FILE}" ]]; then
  # Grep for the most recent ~N pattern in the Cost column (e.g. ~$0.42 or ~0.42)
  last_estimate=$(grep -oE '~\$?[0-9]+(\.[0-9]+)?' "${SESSION_COSTS_FILE}" | tail -1 | tr -d '~$')
  if [[ -n "${last_estimate}" ]]; then
    delta=$(echo "${total_cost} ${last_estimate} ${count}" | awk '{
      if ($3 > 0) avg = $1 / $3; else avg = 0
      diff = avg - $2
      if (diff >= 0) sign = "+"
      else sign = ""
      printf "%s%.4f", sign, diff
    }')
    echo ""
    echo "**SESSION_COSTS.md last estimate:** ~\$${last_estimate}  |  **Actual avg:** \$${avg_cost}  |  **Delta:** ${delta}"
  fi
fi

echo ""
