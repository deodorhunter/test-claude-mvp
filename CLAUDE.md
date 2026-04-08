> These rules are **ALWAYS ACTIVE** for every agent, every session, no exceptions.
> Speed 2 workflow: load `.claude/skills/speed2-workflow.md` on demand.

<!-- compaction directive -->
When compacting, preserve: (1) current phase + US status, (2) all modified file paths, (3) test commands and results, (4) open blockers, (5) agent delegation queue.

---

<part_1 title="Token Optimization (5 Core Rules)">

**R1: NO-EXPLORE** ❌ ls/find/tree/glob/du/unsolicited-Read ^R:Read×1 for missing-critical-import (hook:.claude/hooks/block-exploration.sh)

**R2: SILENCE-OUTPUTS** — use flags below; never pipe raw output to context.
```bash
pip install -q >/dev/null 2>&1
pytest -q --tb=short
npm install --silent 2>/dev/null
docker build -q .
alembic upgrade head 2>&1 | tail -5
```
Never pipe raw install/build/migration output into context.

**R3: TARGETED-EDIT** — E for replacements; grep -n first; no rewrite-from-scratch when <30% changed.

**R4: CIRCUIT-BREAKER** — 2 attempts max:
```
Attempt 1 → ONE targeted fix → re-run
Attempt 2 → ONE targeted fix → re-run
Attempt 3 → STOP. Report: (a) exact error (≤10 lines), (b) what was tried, (c) root cause hypothesis.
```


</part_1>

---

<part_2 title="Tool Paradigms">

<!-- R=Read G=Grep Gl=Glob E=Edit B=Bash S=Serena | ^=exception ❌=forbidden ✅=correct -->

**AST-SEARCH** — ast_grep over sed/awk for fn/class/import patterns; refactor-safe.

**SERENA-FIRST** (when available) — semantic nav before file reads:
0. `mcp__serena__list_memories` → read relevant memories for project context BEFORE navigating code
1. `mcp__serena__get_symbols_overview(file)` — signatures only (~200 tokens vs ~2,000 per file)
2. `mcp__serena__find_symbol(name)` — file + line number (~50 tokens)
3. `mcp__serena__replace_symbol_body` — preferred method for editing a named symbol in-place
4. Full `Read`/`Glob`/`Grep` — last resort: only for `<file>` XML injection into sub-agent prompts
   - `read_file` is disabled in `--context claude-code`; use `Read` + line range after `find_symbol`
   - `get_diagnostics` does not exist in Serena; use `get_errors` tool instead

If Serena is not available, fall back to Read/Grep/Glob directly.

**CONTEXT7** — before using external lib/API:
1. `mcp__context7__resolve-library-id` — map library name to its Context7 ID
2. `mcp__context7__query-docs` — fetch current docs for that library
⚠️ Never pass source/schema/paths (rule-011).

**PY-REPL** — complex scripts only; preserves state; not `bash -c 'python ...'`.

</part_2>

---

<part_3 title="Active Project Rules">

@.claude/rules/project/rule-003-no-explore-agents-for-file-reading.md
@.claude/rules/project/rule-009-serena-first-navigation.md
@.claude/rules/project/rule-011-eu-ai-act-data-boundary.md

</part_3>

---

<part_4 title="Primary References">

| Reference | When to load |
|---|---|
| `docs/AI_REFERENCE.md` | Fallback: env vars, health endpoints only (rule-004: memories first) |
| `docs/ORCHESTRATION_GUIDE.md` | Delegation + model routing |
| `docs/backlog/BACKLOG.md` | Current phase + US status |
| `.claude/skills/speed2-workflow.md` | Speed 2 orchestration (load on demand) |
| `.claude/agents/product-owner.md` | Task Complexity Matrix + US format |

</part_4>

---

<part_5 title="Hard Rules (never break)">

1. **FILE-INJECT**: When delegating to sub-agents, inject raw file content via `<file path="...">` XML tags for files requiring exact implementation detail. For structural navigation, sub-agents self-navigate via Serena MCP (`mcp__serena__get_symbols_overview`). Orchestrator `<file>` injection reserved for algorithm-level edits and DocWriter (which cannot Read files).
2. **EXPLICIT MODEL ASSIGNMENT**: Never delegate with `model: dynamic`. Resolve the model at delegation time: `claude-haiku-4-5-20251001` (LOW) or `claude-sonnet-4-6` (MEDIUM/HIGH). Agent frontmatter declares typed fallback models — `model: dynamic` is not a valid identifier and silently breaks agent spawning. Speed 2 orchestrators MUST still always override per Task Complexity Matrix; frontmatter defaults are only for non-orchestrated fallback.
3. **EU-AI-ACT**: Phase-gate checkpoints mandatory. No autonomous bypass. (Detail: rule-011.)

</part_5>