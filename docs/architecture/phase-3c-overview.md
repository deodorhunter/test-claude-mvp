---
phase: 3c
title: Adoption, DX & Multi-Client
completed: 2026-04-02
us_delivered: [US-057, US-058, US-060]
gate_status: passed
---

# Phase 3c — Adoption, DX & Multi-Client

> Framework-only phase: no application code changes.
> Goal: make the framework usable for new adopters and Copilot-only users.

## User Stories Delivered

### US-057 — Copy-First Adoption Path

**File changed:** `framework-template/HOW-TO-ADOPT.md`

The previous guide buried the copy path as step 1 of a numbered checklist. User feedback: "I said fuck it and copied the .claude folder directly." That IS the path.

Rewritten with **copy-first as the primary section** — 2 commands, done:
```bash
cp -r .claude /your-new-project/
cp CLAUDE.md /your-new-project/
```

New sections added:
- **Post-Copy Checklist** — 5 items (AI_REFERENCE.md, agent paths, .gitignore, first rule, smoke test)
- **Global MCP Installation** — `npm install -g @anthropic-ai/serena-mcp` and context7
- **Copilot Users** — copy copilot-instructions.template.md to `.github/`
- **Feedback template** — 3-line markdown block (category, description, proposed fix)
- **Advanced: Selective Adoption** — cherry-pick agents/rules for partial adoption

The old "30-minute checklist" promoted to the "Advanced Path" section — still present but no longer the primary entry point.

### US-058 — Copilot Standalone Instructions

**File changed:** `.github/copilot-instructions.md`

Previous file referenced Claude Code concepts (Speed 2, phase gates, compress-state) — useless for Copilot-only users who don't run Claude Code.

Complete rewrite as a **self-contained Copilot Chat guide**:
- Opens with Speed 1 scope (what Copilot handles vs when to use Claude Code)
- Three annotated Speed 1 examples: bug fix, model field addition, failing test handling
- **Serena MCP patterns** for Copilot: `symbols_overview`, `find_symbol`, `get_diagnostics`
- **Regex read efficiency pattern** for large files (locate function first, then read ±10 lines)
- **Token anti-patterns** section (no exploration, silence noise, circuit breaker, atomic changes)
- **"When to Use Claude Code Instead"** section with clear boundaries
- No references to CLAUDE.md, phase gates, or orchestrator concepts

### US-060 — Framework Template Sync v3.0

**Files changed:** `framework-template/agents/`, `framework-template/rules/`, `framework-template/README.md`

Template had diverged from current `.claude/` state — missing 9 agents and all 20 project rules.

Synced:
- **Agents:** Added aiml-engineer, debugger, doc-writer, dev-ops, frontend-dev, product-owner, qa-engineer, security-engineer (8 new files)
- **Rules:** Added all 20 active project rules from `.claude/rules/project/`
- **Version stamps:** `<!-- framework-template v3.0 | synced: 2026-04-02 -->` on every file
- **README.md created:** Agent + rule inventory with quick-start, customization checklist, adoption path choices

Template is now a complete snapshot of the framework at v3.0.

## Gate Verification

```
verify-docs result: 83 passed / 17 failed
  ✅ External links (14 checked)
  ✅ Port mappings
  ✅ Make targets
  ✅ Rule structure (7 rules fixed — missing <pattern> sections added)
  ✅ PLUGIN_MANIFEST.md frontmatter
  ⚠️  17 US files not found — Phase 4/5 stubs (pre-existing, not regressions)
```

## Key Design Decisions

**Copy-first vs init-from-template:** `cp -r` beats a custom `make init-framework` target every time — it's transparent, requires zero tooling, and works offline. The template is already structured for direct copy.

**Copilot doc is a projection, not a governance layer:** `.github/copilot-instructions.md` is Copilot-native; CLAUDE.md + .claude/ is the source of truth. They don't duplicate — Copilot instructions say "for planning, use Claude Code."

**Rule `<pattern>` enforcement:** verify-docs now checks `<constraint>`, `<why>`, and `<pattern>` sections in all rule files. 7 older compact rules were missing `<pattern>` — added at this gate. Future rules must include all three sections.

## Phase 3c Incidents (Logged in Session Costs)

- DocWriter sub-agent blocked by Read permission denial (file not pre-injected)
- DevOps sub-agent failed with `model: dynamic` error (model must be explicit at delegation)
- Phase 3c Gate presented as optional choice (rule-020 violation, caught by user)
- DocWriter Mode B hit API rate limit; doc written by Tech Lead directly

All three incidents converge on the same root: **implicit assumptions replaced by explicit constraints** is the framework's core pattern — it applies to the orchestrator's own behavior too.
