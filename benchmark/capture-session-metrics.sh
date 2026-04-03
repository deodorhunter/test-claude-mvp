#!/usr/bin/env bash
# capture-session-metrics.sh
# Reads the most recent Claude Code session JSONL for this project,
# extracts token usage, estimates cost, and counts drift signals.
# Output: benchmark/session-metrics/YYYY-MM-DD-HH-MM.json
# Data never leaves the local machine (EU AI Act rule-011 compliant).

set -euo pipefail

# --- Prerequisites ---
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is not installed. Install with: brew install jq" >&2
  exit 1
fi

# --- Locate session JSONL ---
# Claude Code uses leading - for absolute paths: /Users/... → -Users-...
PROJECT_KEY=$(pwd | sed 's|/|-|g')
CLAUDE_PROJECTS_DIR="${HOME}/.claude/projects/${PROJECT_KEY}"

if [[ ! -d "${CLAUDE_PROJECTS_DIR}" ]]; then
  # Fallback: strip leading dash (older Claude Code versions)
  ALT_KEY=$(echo "${PROJECT_KEY}" | sed 's|^-||')
  CLAUDE_PROJECTS_DIR="${HOME}/.claude/projects/${ALT_KEY}"
fi

if [[ ! -d "${CLAUDE_PROJECTS_DIR}" ]]; then
  echo "ERROR: No Claude session directory found." >&2
  echo "  Tried: ${HOME}/.claude/projects/${PROJECT_KEY}" >&2
  echo "  Tried: ${HOME}/.claude/projects/${ALT_KEY}" >&2
  exit 1
fi

# Get newest JSONL file
JSONL_FILE=$(ls -t "${CLAUDE_PROJECTS_DIR}"/*.jsonl 2>/dev/null | head -1)

if [[ -z "${JSONL_FILE}" ]]; then
  echo "ERROR: No .jsonl session files found in ${CLAUDE_PROJECTS_DIR}" >&2
  exit 1
fi

# --- Extract token sums ---
# Entries may nest usage under .message.usage or directly under .usage
INPUT_TOKENS=$(jq -s '
  [ .[]
    | (.message.usage.input_tokens // .usage.input_tokens // 0)
  ] | add // 0
' "${JSONL_FILE}")

OUTPUT_TOKENS=$(jq -s '
  [ .[]
    | (.message.usage.output_tokens // .usage.output_tokens // 0)
  ] | add // 0
' "${JSONL_FILE}")

CACHE_CREATION_TOKENS=$(jq -s '
  [ .[]
    | (.message.usage.cache_creation_input_tokens // .usage.cache_creation_input_tokens // 0)
  ] | add // 0
' "${JSONL_FILE}")

CACHE_READ_TOKENS=$(jq -s '
  [ .[]
    | (.message.usage.cache_read_input_tokens // .usage.cache_read_input_tokens // 0)
  ] | add // 0
' "${JSONL_FILE}")

# --- Calculate cache read ratio ---
# cache_read_ratio = cache_read / (input + cache_read) * 100
CACHE_READ_RATIO=$(echo "${INPUT_TOKENS} ${CACHE_READ_TOKENS}" | awk '{
  total = $1 + $2
  if (total == 0) { printf "0.0" }
  else { printf "%.1f", ($2 / total) * 100 }
}')

# --- Estimate cost (Sonnet rates, conservative) ---
# Input:          $3.00 / 1M
# Output:        $15.00 / 1M
# Cache read:     $0.30 / 1M
# Cache creation: $3.75 / 1M
ESTIMATED_COST=$(echo "${INPUT_TOKENS} ${OUTPUT_TOKENS} ${CACHE_READ_TOKENS} ${CACHE_CREATION_TOKENS}" | awk '{
  cost = ($1 * 3.00 / 1000000) \
       + ($2 * 15.00 / 1000000) \
       + ($3 * 0.30 / 1000000) \
       + ($4 * 3.75 / 1000000)
  printf "%.4f", cost
}')

# --- Count drift signals ---
# Budget Cap proxy: tool result entries where any content[].text length < 100
DRIFT_SIGNALS=$(jq -s '
  [ .[]
    | select(.type == "tool_result" or .role == "tool")
    | .content
    | if type == "array" then .[]
      elif type == "string" then {text: .}
      else empty
      end
    | select(type == "object" and .text != null)
    | select((.text | length) < 100)
  ] | length
' "${JSONL_FILE}")

# --- Write output ---
SESSION_DATE=$(date '+%Y-%m-%d %H:%M')
OUTPUT_FILENAME=$(date '+%Y-%m-%d-%H-%M')
OUTPUT_DIR="$(dirname "${BASH_SOURCE[0]}")/session-metrics"
mkdir -p "${OUTPUT_DIR}"
OUTPUT_FILE="${OUTPUT_DIR}/${OUTPUT_FILENAME}.json"

# Shorten source_file path for readability
SHORT_SOURCE=$(echo "${JSONL_FILE}" | sed "s|${HOME}|~|")

jq -n \
  --arg session_date "${SESSION_DATE}" \
  --arg source_file "${SHORT_SOURCE}" \
  --argjson input_tokens "${INPUT_TOKENS}" \
  --argjson output_tokens "${OUTPUT_TOKENS}" \
  --argjson cache_read_tokens "${CACHE_READ_TOKENS}" \
  --argjson cache_creation_tokens "${CACHE_CREATION_TOKENS}" \
  --argjson cache_read_ratio_pct "${CACHE_READ_RATIO}" \
  --argjson estimated_cost_usd "${ESTIMATED_COST}" \
  --argjson drift_signals_count "${DRIFT_SIGNALS}" \
  '{
    session_date: $session_date,
    source_file: $source_file,
    input_tokens: $input_tokens,
    output_tokens: $output_tokens,
    cache_read_tokens: $cache_read_tokens,
    cache_creation_tokens: $cache_creation_tokens,
    cache_read_ratio_pct: $cache_read_ratio_pct,
    estimated_cost_usd: $estimated_cost_usd,
    drift_signals_count: $drift_signals_count,
    note: "Cost estimated using Sonnet rates (conservative). Drift signals = tool result entries with content < 100 chars."
  }' > "${OUTPUT_FILE}"

echo "Session metrics captured: cost=\$${ESTIMATED_COST} cache=${CACHE_READ_RATIO}% drift=${DRIFT_SIGNALS} → ${OUTPUT_FILE}"
