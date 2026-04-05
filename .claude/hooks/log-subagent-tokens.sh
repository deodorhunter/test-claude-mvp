#!/bin/bash
# Log sub-agent completion events for per-agent cost analysis
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
INPUT=$(cat)
AGENT_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_name', 'unknown'))" 2>/dev/null || echo "unknown")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id', 'unknown'))" 2>/dev/null || echo "unknown")

LOG_FILE=".claude/subagent-token-log.txt"
echo "{\"timestamp\": \"$TIMESTAMP\", \"agent_name\": \"$AGENT_NAME\", \"session_id\": \"$SESSION_ID\"}" >> "$LOG_FILE"
