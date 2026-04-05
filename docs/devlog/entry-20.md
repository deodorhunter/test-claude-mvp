# Entry 20 — MCP Fix: Strategy A (disallowedTools + inline mcpServers)

**Date:** 2026-04-05  
**Phase:** Governance improvement (cross-phase)  
**Session:** Fresh session, plan resumed from `/Users/martina/.claude/plans/rustling-dreaming-pine.md`

---

## Problem

Sub-agents could not call Serena or Context7 MCP tools, forcing the orchestrator to run Serena pre-flight (`mcp__serena__get_symbols_overview`) for every US delegation and inject `<symbols>` blocks — adding ~1,600 tokens/US to orchestrator context with zero benefit to the agent's actual task.

Previous session (2026-04-04) had confirmed the failure and formed the hypothesis: the `tools:` allowlist in agent frontmatter does not resolve `mcp__server_name` prefix entries to actual MCP tool functions. The allowlist silently excludes them.

---

## Root Cause

GitHub issue #25200 confirms: `mcp__server_name` entries in a `tools:` allowlist do not resolve to callable MCP tools. The allowlist is a permissive filter on Claude Code's native tools — it has no mechanism to inject external MCP connections. Sub-agents were receiving Serena's system instructions (via system-reminder) but the RPC bridge was never established.

**Two changes required to fix:**
1. Remove `tools:` allowlist (replace with `disallowedTools:` denylist)
2. Add inline `mcpServers:` definitions in agent frontmatter

---

## Gate Test Result — Strategy A Confirmed

Spawned `debugger` agent (already updated to `disallowedTools` in previous session) at session start:

- `mcp__serena__get_symbols_overview("ai/models/base.py")` → **SUCCESS** — returned `{"Class": ["ModelResponse", "ModelAdapter", "ModelError", "OllamaUnavailableError", "ClaudeConfigError"]}`
- `mcp__context7__resolve-library-id("fastapi")` → **SUCCESS** — returned library matches with score 84.63

Both MCP servers operational in sub-agent context. Strategy A confirmed.

---

## Changes Made

### Phase 1 — Agent Frontmatter (8 agents)

All implementing agents converted from `tools:` allowlist to `disallowedTools:` denylist + inline `mcpServers`:

| Agent | disallowedTools | mcpServers |
|---|---|---|
| backend-dev | Agent | serena + context7 |
| aiml-engineer | Agent | serena + context7 |
| frontend-dev | Agent | serena + context7 |
| security-engineer | Agent | serena + context7 |
| qa-engineer | Edit, Agent | serena + context7 |
| dev-ops | Agent | context7 only |
| debugger | Write, Glob, Agent | serena + context7 |
| orchestrator | *(tools: removed entirely — Agent must remain available)* | *(main session has MCP directly)* |

All agents also received:
- `hooks:` with PreToolUse (`block-exploration.sh`) + PostToolUse (`post-tool-truncate.sh`)
- Constraint #1 updated: self-navigate via Serena, STOP on degradation

### Phase 2 — Hook Files

- `.claude/hooks/block-exploration.sh` — PreToolUse Bash hook enforcing Rule 1 mechanically. Blocks `ls`, `find ./`, `tree`, `du -`, `locate` patterns. Allows targeted path verification.
- `.claude/hooks/log-subagent-tokens.sh` — SubagentStop hook logging `{timestamp, agent_name, session_id}` to `.claude/subagent-token-log.txt` (gitignored).
- `settings.json` — added `PreToolUse` Bash hook and `SubagentStop` hook for main session.

### Phase 3 — Governance

- `CLAUDE.md` `<part_3>`: removed `rule-001`, `rule-009`, `rule-010` from global load. Only `rule-011` (EU AI Act) remains global.
- `rule-009`: updated to reflect sub-agents self-navigate. Scope note extended to both Speed 1 and Speed 2.
- `rule-010`: retired → `docs/rules-archive/rule-010-retired.md`. Was a workaround for the now-fixed gap.
- `orchestrator.md` delegation section: simplified (Strategy A3). Orchestrator symbol injection no longer required. Rule 001 planning note added (Change 4).

### Phase 4 — TEMPLATE.md + ORCHESTRATION_GUIDE.md

- `TEMPLATE.md`: `disallowedTools` + `mcpServers` + `hooks` as default. Constraint #1 updated.
- `ORCHESTRATION_GUIDE.md`: Rules 009+010 section replaced with new self-navigation reality. Anti-pattern #2 updated. Speed 1 Serena guidance added.

---

## Token Savings (Estimated)

**Before:** Orchestrator ran `mcp__serena__get_symbols_overview` for each delegation file (~200 tokens/file × 3–5 files) + injected `<symbols>` blocks into delegation prompt (~200 tokens/file). Per-US cost in orchestrator context: ~1,200–2,000 tokens.

**After:** Sub-agents self-navigate. Orchestrator delegation prompt contains only `<user_story>` + targeted `<file>` blocks (algorithm-level only). Per-US orchestrator overhead: ~0–400 tokens for context injection.

Estimated reduction in orchestrator delegation prompt: **~60–80% for structure-navigation overhead**.

Additionally: Rule 1 exploration block now mechanically enforced — eliminates the class of bug where an agent falls back to `ls`/`find` after Serena fails silently.

---

## Residual Risks

- `block-exploration.sh` regex may need tuning — current pattern blocks `ls` with flags but no path (`ls -la`), but allows `ls backend/app/specific/`. Edge cases may need refinement in practice.
- `log-subagent-tokens.sh` parses SubagentStop event payload via python3 — payload schema not fully verified. May log "unknown" for agent_name if schema differs from assumed format.
- `mcpServers` inline definitions assume Serena at `http://localhost:9121/sse`. If Serena port changes, all agent files need updating. Consider centralizing in future.

---

## Rules Extracted

None new — this session was implementation of a previously extracted rule-set. Rule 009 and 010 updated/retired as planned.
