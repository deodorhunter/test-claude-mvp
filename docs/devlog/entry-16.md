← [Back to DEVLOG index](../DEVLOG.md)

## Entry 16 — The Governance Paradox: Framework v4.0 Simplification — 2026-04-03

> After Phases 3a-3c demonstrated escalating governance failures, the framework underwent a full audit and simplification. The core diagnosis: governance complexity had exceeded the model's reliable execution capacity. The fix: reduce to what actually gets followed.

#### The problem

Between Phases 1-2d, the framework worked. Phase 2d was the high point: minimal waste (~4%), zero rule violations, direct implementation pattern. Then Phase 3 was repurposed for framework governance upgrades, and the framework began governing itself.

Each incident produced a new rule. Each rule violation produced a more specific rule. The framework grew from 6 principles to 819 lines of always-loaded governance text (CLAUDE.md + orchestrator.md + product-owner.md + 17 rules), plus 3 hooks emitting system warnings on routine operations. The model could no longer follow all of it.

Symptoms across Phases 3a-3c:
- **Consistency checks abandoned**: CONSISTENCY_LOG.md had exactly 2 entries, both from Phase 2d. Zero from any delegated US.
- **Phase Gates treated as optional**: Violated in Phase 2c, 3b, and 3c despite rule-007 and rule-020 both explicitly prohibiting it.
- **Sub-agent spawns failed**: DocWriter launched without file content (Entry 15), DevOps launched with `model: dynamic` (Entry 15).
- **compress-state + /clear caused chaos**: Full context resets lost tool outputs, error context, and work state. The worst session results correlated with compress+clear cycles.
- **Hook noise polluted context**: `<system_warning>` on every 12th tool call, every Agent spawn, every SubagentStop.

#### The diagnosis

**Governance paradox**: adding rules to prevent rule violations creates more rules to violate. The model has finite attention. 819 lines of governance consume attention that should go to the actual task. The hooks meant to remind about rules became noise that competed with the rules themselves.

**Architectural mismatch**: orchestrator.md was loaded as a project instruction via `@` import (always-on, 169 lines), but had agent frontmatter (`model: claude-sonnet-4-6`, `allowed_tools`, `forbidden` paths) that was never enforced — it's the top-level instance, not a spawned sub-agent. This created identity confusion and wasted context on every session, including Speed 1 fixes.

**Serena was never working**: The `~/.claude/mcp.json` entry named "serena" was actually running `@orama/orama` — Orama (a search engine from `oramasearch` org), not Serena (LSP navigation from `oraios` org). Every reference to "Serena-first navigation" in the framework was dead code. Rule-009 fired warnings about Serena not being configured, but the pre-prompt hook checked `settings.json` instead of `mcp.json` — so it warned even when *something* was configured.

#### What was removed (Framework v4.0)

**Deleted** (8 files):
- `/compress-state` command + `auto-compress.sh` hook + rule-010 — the entire compress-state ecosystem. Claude Code's built-in `/compact` is strictly better.
- `/consistency-check` command — replaced by `/judge` (git-diff based, more reliable).
- rule-003 (no Explore agents) — redundant with CLAUDE.md Rule 1.
- rule-006 (no QA subagents) — operational procedure moved to workflow skill.
- rule-020 (phase gate auto-proceed) — merged into rule-007.

**Converted**:
- orchestrator.md: from always-loaded agent to on-demand skill (`.claude/skills/speed2-workflow.md`). Speed 1 sessions no longer load 169 lines of Speed 2 workflow.
- product-owner.md: removed from `@` imports. Still available as agent definition.

**Simplified**:
- CLAUDE.md: from 111 lines (plus ~700 from imports) to ~95 lines with 5 rule imports (down from 8).
- Post-US workflow: from 8 steps to 4.
- Phase Gate workflow: from 8 steps to 5.
- Delegation checklist: from 6+ prose items to 4 structured items.
- SESSION_COSTS.md: dropped per-agent token breakdown (never accurate).
- settings.json hooks: from 6 registrations to 2.

**Fixed**:
- pre-prompt.sh: now checks `mcp.json` for Serena, not `settings.json`.
- rule-007: absorbs rule-020 content (mandatory + auto-proceed in one rule).

#### The principle

**Reduce to what gets followed.** A framework that the model can't reliably execute is worse than no framework — it creates a false sense of governance while the actual behaviour diverges. The DEVLOG documents this divergence across 4 entries (12-15).

Framework v4.0 applies the same lesson that Entry 2 applied to agents: explicit constraints beat implicit assumptions, and fewer constraints followed reliably beat many constraints followed intermittently.

#### Open items

- **Serena**: Needs proper installation via `uvx --from git+https://github.com/oraios/serena`. Orama (current `@orama/orama`) should be renamed correctly in mcp.json.
- **Docker ai-tools**: compose broken (missing external network). Separate infra task.
- **Orchestrator.md**: Kept as reference but no longer auto-loaded. May be archived later if speed2-workflow.md proves sufficient.
- **TodoWrite enforcement**: The plan recommends using TodoWrite for post-US and Phase Gate workflows. First validation: Phase 3d or Phase 4.

---
