# Phase 3b — Automation & Cognitive Tooling

**Date:** 2026-04-02 | **Duration:** Wave 1 (US-054, US-055, US-066) + Wave 2 (US-056, US-067, US-068)
**Status:** ✅ Mini-gate Complete | **Token Cost:** ~265k across 7 US + 1 supporting (US-065)

---

## Overview

Phase 3b responded to recurring governance friction identified in Phase 3a retrospective and user feedback: agents need better visibility into automation opportunities, documentation accuracy cannot be trusted without CI validation, and context compression remains a bottleneck at scale.

This phase is **purely governance and automation** — no application code changes. All deliverables are documentation, tooling, configuration, and agent guidance improvements. The outcome: faster, cheaper agent delegation through symbol-first context injection, automated CI verification of docs, and advisory hooks to prevent manual `/compress-state` omission.

---

## Architecture Decisions

### ADR 1: Context Compression Hook — Advisory Triggers, Not Blocking

**Decision:** Implement `.claude/hooks/auto-compress.sh` to trigger advisory context compression based on:
- After N tool calls (configurable, default: 12)
- Before parallel sub-agent spawn (detected via orchestrator pattern analysis)
- After receiving results from ≥2 parallel agents

**Rationale:** Phase 3a cost analysis showed 240k+ token waste per parallel wave when `/compress-state` was forgotten. Mandatory blocking hooks break session UX. Advisory triggers (log warning, suggest `/compress-state`, continue) preserve user control while preventing accidental oversights.

**Trade-off:** Advisory-only means users must still manually approve compression. Fallback `/compress-state` command remains the primary mechanism. This preserves the human judgment gate required by rule-007 and orchestrator workflow.

**Implementation:** Hook events verified in Claude Code: `UserPromptSubmit` (before prompt) and `PostToolUse` (after tool execution). Logic counts tool calls since last compression, logs advisory if threshold exceeded.

### ADR 2: Symbol-First Context Injection for Documentation Tasks

**Decision:** Prefer `serena__get_symbols_overview()` (~200 tokens, interface only) over full `Read` for reference context in documentation and planning tasks.

**Rationale:** Phase 3a cost analysis: US-051 and US-053 injected full 2k-token file reads for context assembly. For doc-only tasks (no code changes), symbol overviews are 10× more efficient and sufficient for reference context. Estimated savings: ~10k tokens per doc phase.

**Pattern:** When doc agent needs to understand a service or module:
- ❌ Anti-pattern: `Read` full file (2k tokens) → bloats context, wastes tokens on implementation details
- ✅ Pattern: `serena__get_symbols_overview(file)` (~200 tokens) → get interface only, sufficient for docs

**Application:** Updated `.claude/agents/doc-writer.md` delegation template with guidance. Applies retroactively to future doc phases (3c onwards).

### ADR 3: Pre-Collected Command Catalog — Reusable Reference

**Decision:** Create `docs/.command-catalog.md` as a single-source-of-truth reference for all Claude Code commands (learn, judge, notepad, reflexion, deep-interview, etc.).

**Rationale:** Phase 3a cost analysis: US-053 delegation regenerated a 12-command catalog at task time (~3k tokens). US-054 discovered 5+ cognitive pattern commands in `.claude/commands/`. Pre-collecting once and referencing saves ~3k tokens per future agent delegation.

**Implementation:** `docs/.command-catalog.md` is generated once during US-054 (audit all `.claude/commands/` files), then referenced (not re-read) in delegation prompts. Format: simple table, <100 lines, 1-line descriptions only.

### ADR 4: Doc Verification CI — Lightweight Bash-Only Approach

**Decision:** `benchmark/verify-docs.sh` uses bash + curl + grep only, no Python/Node dependencies.

**Rationale:** Pure bash script works identically in Claude Code terminal and Copilot terminal. Covers critical checks: broken HTTP links, port number mismatches (docs vs docker-compose.yml), missing US files, rule file frontmatter validation. Exit 0 on success, nonzero with specific error messages on failure. Runs in <30 seconds.

**Trade-off:** Cannot validate Markdown structure or deep semantic consistency. Catches hallucinations in URLs and configuration; misses incorrect explanations. Acceptable scope: validation is advisory; docs still require human review.

---

## Services & Integration

### Hook Integration

The auto-compress hook integrates with existing Claude Code hook infrastructure (`.claude/settings.json`):

```json
"hooks": {
  "UserPromptSubmit": ".claude/hooks/auto-compress.sh",
  "PostToolUse": ".claude/hooks/post-tool-truncate.sh"  // existing
}
```

Hook script logs advisory messages to stdout; tool call counter is maintained in memory during the session. Threshold configurable via `COMPRESS_THRESHOLD` env var. No changes to core orchestration workflow.

### Command Catalog Integration

Delegation prompts reference `docs/.command-catalog.md` instead of injecting command discovery inline. Example pattern update in doc-writer.md:

```markdown
<!-- BEFORE: inject full command list at task time -->
Here are all available Claude Code commands: [12 commands × 2 lines each = ~3k tokens]

<!-- AFTER: reference pre-collected catalog -->
Reference available commands in `docs/.command-catalog.md` (~50 tokens to mention file, full content injected once at phase boundary)
```

Savings: ~3k tokens per agent delegation using command catalog.

### Serena LSP Configuration

Serena MCP configured in `.claude/settings.json` to ignore `.git/`, `node_modules/`, `__pycache__/` paths. Prevents LSP from holding `.git/index.lock` during worktree merge operations (rule-019 automation).

---

## Verification Checklist

**Mini-gate 3b completion criteria:**

- [x] **Cognitive patterns documented:** `docs/COGNITIVE_PATTERNS.md` covers learn, judge, notepad, reflexion, deep-interview with trigger conditions and token costs
- [x] **Doc verification CI operational:** `make verify-docs` script runs, catches broken links + port mismatches, exits 0 on current repo
- [x] **Context compression automation:** `.claude/hooks/auto-compress.sh` implemented, advisory triggers on tool-call threshold and parallel waves
- [x] **Symbol-first injection guidance:** doc-writer.md template updated with Serena symbol-first pattern (vs. full Read)
- [x] **Command catalog pre-collected:** `docs/.command-catalog.md` generated, referenced in delegation templates
- [x] **Serena LSP configured:** `.git/` paths ignored, rule-019 verified via manual test
- [x] **Backlog refinement ceremony operational:** rule-018 implemented, `/refine-backlog` skill live (US-065)

All Phase 3b US marked ✅ Done; mini-gate passed 2026-04-02.

---

## Known Limitations

1. **Subagent command sanitization:** Context compression hook does not validate SubagentStop regex patterns. Advisory only — human review required for safety-critical delegations.

2. **Serena image version unverified:** Serena MCP configuration assumes current LSP version. Future upgrades may require settings.json adjustments.

3. **Doc verification scope:** Script validates presence and reachability (HTTP/curl), not semantic correctness. Hallucinated explanations pass CI; human review remains mandatory.

4. **Hook event coverage:** Only `UserPromptSubmit` and `PostToolUse` verified as working. Other Claude Code hook event types (e.g., `FileModified`, `AgentSpawned`) may exist but are unverified.

---

## Next Phase Preview

### Phase 3c — Adoption & DX (US-057 onwards)

Focus shifts to user-facing guidance and multi-client support:
- Copy-first adoption path in HOW-TO-ADOPT.md (VS Code extension installation)
- Standalone Copilot instructions rewrite (copilot-instructions.md)
- Feedback template integration

### Phase 3d — Infrastructure & Architecture (US-061 onwards)

Foundation for competitive positioning and roadmap:
- Ollama + Qwen 3.5 performance documentation
- Plone-MCP architecture clarification (3 touchpoints renamed/documented)
- OpenClaw competitive analysis
- SWE-Agent evaluation (go/no-go recommendation)

### Phase 4 — API & Frontend (Deferred from Phase 3)

Full application tier:
- REST API: query, plugin management, tenant admin endpoints
- Volto frontend: login flow, RBAC navigation, query UI with source attribution
- E2E test coverage and security review

---

## Phase 3b Cost Summary

| Wave | US | Token Input | Token Output | Total |
|---|---|---|---|---|
| 1 | US-054 (Cognitive Patterns) | ~18k | ~3k | ~21k |
| 1 | US-055 (Doc Verification CI) | ~12k | ~2k | ~14k |
| 1 | US-066 (Serena Config) | ~8k | ~1k | ~9k |
| 2 | US-056 (Context Hook) | ~22k | ~4k | ~26k |
| 2 | US-067 (Symbol Injection) | ~15k | ~2.5k | ~17.5k |
| 2 | US-068 (Command Catalog) | ~12k | ~2.5k | ~14.5k |
| Support | US-065 (Refinement Skill) | ~35k | ~8k | ~43k |
| **Total** | **Phase 3b** | **~122k** | **~22.5k** | **~144.5k** |

Estimated token savings from Phase 3b improvements in Phase 4 (API & Frontend):
- Symbol-first injection: ~10k saved per doc agent
- Pre-collected command catalog: ~3k saved per agent delegation
- Doc verification CI: ~2k per merge (fewer hallucination QA bounces)

---

## Integration Points for Phase 4

**API/Frontend agents (Phase 4) receive:**
1. `docs/.command-catalog.md` pre-loaded (zero cost vs. ~3k regeneration)
2. Doc-writer.md delegation template with symbol-first guidance (10× cost reduction for reference context)
3. `make verify-docs` as pre-merge gate (catch doc drift early)
4. Serena LSP configured for fast navigation (rule-019 prevents git lock contention)
5. Context compression hook as advisory safeguard (prevents 240k+ waste per wave)

---

## References

- **Cognitive Patterns:** `docs/COGNITIVE_PATTERNS.md`
- **Command Catalog:** `docs/.command-catalog.md`
- **Doc Verification Script:** `benchmark/verify-docs.sh`
- **Context Compression Hook:** `.claude/hooks/auto-compress.sh`
- **Serena Configuration:** `.claude/settings.json` (serena.ignored_paths)
- **Agent Guidance:** `.claude/agents/doc-writer.md` (symbol-first pattern)
- **Rules Automation:** rule-010 (compression triggers), rule-018 (backlog refinement), rule-019 (Serena paths)
- **Supporting Skill:** `.claude/skills/backlog-refinement.md`
