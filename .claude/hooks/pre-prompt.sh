#!/usr/bin/env bash
# pre-prompt.sh — State checks before any tokens are consumed.
# Registered as UserPromptSubmit hook in .claude/settings.json

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ── 1. AI_REFERENCE CHECK (hard gate) ─────────────────────────────────────────
if [ ! -f "$PROJECT_ROOT/docs/AI_REFERENCE.md" ]; then
  echo "ERROR: docs/AI_REFERENCE.md is missing."
  echo "Run /init-ai-reference before starting any Speed 2 session."
  exit 1
fi

# ── 2. SERENA MCP CHECK (soft warning) ────────────────────────────────────────
# Claude Code stores project MCP configs in ~/.claude.json under projects[path].mcpServers
if ! grep -q '"serena"' ~/.claude.json 2>/dev/null; then
  echo "<system_warning>Serena MCP not configured. Serena-first navigation (rule-009) will fall back to Read/Grep. To fix: claude mcp add serena -- uvx --from git+https://github.com/oraios/serena serena-mcp-server --context ide-assistant --project \$PROJECT_ROOT</system_warning>"
fi

# ── 3. GIT BLOAT CHECK (soft warning) ─────────────────────────────────────────
DIRTY_COUNT=$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
if [ "$DIRTY_COUNT" -gt 15 ]; then
  echo "<system_warning>Git state is dirty ($DIRTY_COUNT uncommitted changes). Commit or stash before spawning parallel agents.</system_warning>"
fi

# ── 4. .omc/ DIRECTORY GUARD (EU AI Act compliance) ──────────────────────────
if [ -d "$PROJECT_ROOT/.omc" ]; then
  echo "<system_warning>⚠️  .omc/ directory detected. oh-my-claudecode session sync features (replay JSONL, external notifications) are EU AI Act non-compliant for this project. See rule-011-eu-ai-act-data-boundary.md before proceeding.</system_warning>"
fi

exit 0
