> These rules are **ALWAYS ACTIVE** for every agent, every session, no exceptions.
> Speed 2 workflow: load `.claude/skills/speed2-workflow.md` on demand.

<!-- compaction directive -->
When compacting, preserve: (1) current phase + US status, (2) all modified file paths, (3) test commands and results, (4) open blockers, (5) agent delegation queue.

---

<part_1 title="Token Optimization (5 Core Rules)">

**Rule 1: NO AUTONOMOUS EXPLORATION**
Forbidden: `ls`, `find`, `tree`, `glob`, `du` to discover files. Forbidden: `Read` on files not explicitly provided.
Exception: `Read` at most ONCE for a completely missing critical import dependency.
Mechanically enforced in main session and all sub-agents via `.claude/hooks/block-exploration.sh` (PreToolUse Bash hook).

**Rule 2: SILENCE VERBOSE OUTPUTS**
```bash
pip install -q >/dev/null 2>&1
pytest -q --tb=short
npm install --silent 2>/dev/null
docker build -q .
alembic upgrade head 2>&1 | tail -5
```
Never pipe raw install/build/migration output into context.

**Rule 3: TARGETED EDITING ONLY**
Use the `Edit` tool for precise string replacements. Use `grep -n` to locate lines before editing.
Never rewrite a file from scratch when modifying <30% of its content.

**Rule 4: CIRCUIT BREAKER — MAX 2 DEBUGGING ATTEMPTS**
```
Attempt 1 → ONE targeted fix → re-run
Attempt 2 → ONE targeted fix → re-run
Attempt 3 → STOP. Report: (a) exact error (≤10 lines), (b) what was tried, (c) root cause hypothesis.
```


</part_1>

---

<part_2 title="Tool Paradigms">

**AST Structural Search**
Find patterns by syntax, not text matching. Use AST structural code search and replace (e.g. `ast_grep`) instead of raw `sed`/`awk` when matching syntactic constructs (function signatures, class hierarchies, import patterns). AST search is refactor-safe — it won't match comments or strings that happen to contain the pattern.

**LSP Integration (Serena-First Navigation)**
When Serena MCP is available, enforce semantic navigation before reading files:
1. `mcp__serena__get_symbols_overview(file)` — signatures only (~200 tokens vs ~2,000 per file)
2. `mcp__serena__find_symbol(name)` — file + line number (~50 tokens)
3. `mcp__serena__replace_symbol_body` — preferred method for editing a named symbol in-place
4. Full `Read`/`Glob`/`Grep` — last resort: only for `<file>` XML injection into sub-agent prompts
   - `read_file` is disabled in `--context claude-code`; use `Read` + line range after `find_symbol`
   - `get_diagnostics` does not exist in Serena; use `get_errors` tool instead

If Serena is not available, fall back to Read/Grep/Glob directly.

**Context7 for Library Documentation**
Before writing code that depends on a specific external library or API:
1. `mcp__context7__resolve-library-id` — map library name to its Context7 ID
2. `mcp__context7__query-docs` — fetch current docs for that library
⚠️ Do NOT pass source code, schema, or file paths to Context7 queries (rule-011).

**Python REPL**
Use the persistent Python REPL for complex scripts instead of multiline `bash -c 'python ...'`. REPL preserves state between calls.

</part_2>

---

<part_3 title="Active Project Rules">

@.claude/rules/project/rule-011-eu-ai-act-data-boundary.md

</part_3>

---

<part_4 title="Primary References">

| Reference | Purpose |
|---|---|
| `docs/AI_REFERENCE.md` | Stack, ports, make targets, test commands — ground truth. Read at every Speed 2 session start. If missing: run `/init-ai-reference` BEFORE anything else. |
| `docs/ORCHESTRATION_GUIDE.md` | Agent delegation patterns, model routing, anti-patterns — load when planning |
| `docs/backlog/BACKLOG.md` | Current phase and US status |
| `.claude/skills/speed2-workflow.md` | Speed 2 workflow, delegation, phase gates (load on demand) |
| `.claude/agents/product-owner.md` | Task Complexity Matrix, US format (load when creating US) |

</part_4>

---

<part_5 title="Hard Rules (never break)">

1. **FILE CONTENT INJECTION**: When delegating to sub-agents, inject raw file content via `<file path="...">` XML tags for files requiring exact implementation detail. For structural navigation, sub-agents self-navigate via Serena MCP (`mcp__serena__get_symbols_overview`). Orchestrator `<file>` injection reserved for algorithm-level edits and DocWriter (which cannot Read files).
2. **EXPLICIT MODEL ASSIGNMENT**: Never delegate with `model: dynamic`. Resolve the model at delegation time: `claude-haiku-4-5-20251001` (LOW) or `claude-sonnet-4-6` (MEDIUM/HIGH). Agent frontmatter declares typed fallback models — `model: dynamic` is not a valid identifier and silently breaks agent spawning. Speed 2 orchestrators MUST still always override per Task Complexity Matrix; frontmatter defaults are only for non-orchestrated fallback.
3. **EU AI ACT COMPLIANCE**: No code/schema/session data to third-party services. Phase-gate checkpoints mandatory.

</part_5>