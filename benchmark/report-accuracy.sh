#!/bin/bash
# report-accuracy.sh — Print per-phase and per-agent accuracy summary from benchmark/accuracy-log.jsonl

set -e

LOGFILE="benchmark/accuracy-log.jsonl"

if [ ! -f "$LOGFILE" ] || [ ! -s "$LOGFILE" ]; then
    echo "Accuracy log not found or empty: $LOGFILE"
    echo "Run /judge US-NNN after implementations to populate the log."
    exit 1
fi

echo "## Accuracy Report — Phase Summary"
echo ""
echo "| Phase | US Count | ACs Total | ACs Pass | Pass Rate | Bouncebacks |"
echo "|---|---|---|---|---|---|"

# Aggregate per phase
jq -r '[.[] | select(.phase) | {phase: .phase, us_count: 1, ac_total: .ac_total, ac_pass: .ac_pass, failures: (if .verdict == "fail" then 1 else 0 end)}] | group_by(.phase) | .[] | {phase: .[0].phase, us_count: (map(.us_count) | add), ac_total: (map(.ac_total) | add), ac_pass: (map(.ac_pass) | add), failures: (map(.failures) | add)} | "\(.phase)|\(.us_count)|\(.ac_total)|\(.ac_pass)|\(.ac_total != 0 ? ((.ac_pass / .ac_total) * 100 | floor) : 0)%|\(.failures)"' "$LOGFILE" 2>/dev/null | while IFS='|' read -r phase us_count ac_total ac_pass rate failures; do
    [ -z "$phase" ] && continue
    echo "| $phase | $us_count | $ac_total | $ac_pass | $rate | $failures |"
done

echo ""
echo "## Per-Agent Breakdown"
echo ""
echo "| Agent | US Count | Pass Rate | Status |"
echo "|---|---|---|---|"

# Aggregate per agent
jq -r '[.[] | select(.agent) | {agent: .agent, us_count: 1, pass: (if .verdict == "pass" then 1 else 0 end)}] | group_by(.agent) | .[] | {agent: .[0].agent, us_count: (map(.us_count) | add), pass_count: (map(.pass) | add)} | "\(.agent)|\(.us_count)|\(.pass_count)"' "$LOGFILE" 2>/dev/null | while IFS='|' read -r agent us_count pass_count; do
    [ -z "$agent" ] && continue
    pass_rate=$((pass_count * 100 / us_count))
    if [ "$pass_rate" -lt 80 ]; then
        status="⚠️ Below 80%"
    else
        status="✅ OK"
    fi
    echo "| $agent | $us_count | $pass_rate% | $status |"
done

echo ""
echo "## Overall Totals"
echo ""

# Overall stats
stats=$(jq -r '{us_total: (. | length), us_passed: (map(select(.verdict == "pass")) | length), us_failed: (map(select(.verdict == "fail")) | length), ac_total: (map(.ac_total) | add), ac_pass: (map(.ac_pass) | add), ac_fail: (map(.ac_fail) | add)}' "$LOGFILE" 2>/dev/null)

us_total=$(echo "$stats" | jq '.us_total')
us_passed=$(echo "$stats" | jq '.us_passed')
us_failed=$(echo "$stats" | jq '.us_failed')
ac_total=$(echo "$stats" | jq '.ac_total')
ac_pass=$(echo "$stats" | jq '.ac_pass')
ac_fail=$(echo "$stats" | jq '.ac_fail')

us_rate=$((us_passed * 100 / us_total))
ac_rate=$((ac_pass * 100 / ac_total))

echo "- **User Stories evaluated:** $us_total ($us_passed passed, $us_failed failed) — $us_rate% pass rate"
echo "- **Acceptance Criteria:** $ac_total total ($ac_pass passed, $ac_fail failed) — $ac_rate% pass rate"
echo ""
echo "**Last updated:** $(date +%Y-%m-%d)"
