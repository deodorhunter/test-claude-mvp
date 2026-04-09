#!/usr/bin/env bash
# cbm-mcp.sh — stdio MCP wrapper for codebase-memory-mcp
#
# Architecture (Daemonized Mode):
#   - codebase-memory-mcp runs 24/7 as a daemon in docker-compose to serve the UI.
#   - Claude Code spawns this script as an MCP server subprocess.
#   - This script `docker exec`s into the running daemon to spawn a headless MCP worker.
#   - Both processes securely share the SQLite cache volume.

set -euo pipefail

# ── Gate: only start if CBM is the active backend ─────────────────────────────
case "${NAVIGATION_BACKEND:-serena}" in
  cbm|both)
    ;;
  *)
    echo "cbm-mcp: not starting (NAVIGATION_BACKEND=${NAVIGATION_BACKEND:-serena})." \
         "Set to 'cbm' or 'both' in .claude/settings.json to activate." >&2
    exit 1
    ;;
esac

# ── Ensure Daemon is Running ──────────────────────────────────────────────────
if ! docker ps --format '{{.Names}}' | grep -q "^codebase-memory-mcp$"; then
    echo "Error: codebase-memory-mcp daemon is not running." >&2
    echo "Please run: docker compose -f infra/docker-compose.ai-tools.yml up -d codebase-memory-mcp" >&2
    exit 1
fi

# ── Spawn Headless Worker ─────────────────────────────────────────────────────
# -i : Passes stdin/stdout through to the exec process (required for MCP).
# Note: We execute `cbm` directly (bypassing the entrypoint wrapper) without UI flags.
# This creates a zero-overhead, headless worker thread just for the AI conversation.
exec docker exec -i codebase-memory-mcp codebase-memory-mcp