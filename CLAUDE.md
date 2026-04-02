# CLAUDE.md — Global Physics
> These rules are **ALWAYS ACTIVE** for every agent, every session, no exceptions.
> Workflow: see @.claude/agents/orchestrator.md · Planning & US format: see @.claude/agents/product-owner.md

<!-- compaction directive -->
When compacting, preserve: (1) current phase + US status, (2) all modified file paths, (3) test commands and results, (4) open blockers, (5) agent delegation queue.

---

<part_1 title="Token Optimization (5 Core Rules)">

**Rule 1: NO AUTONOMOUS EXPLORATION**
Forbidden: `ls`, `find`, `tree`, `glob`, `du` to discover files. Forbidden: `Read` on files not explicitly provided.
Exception: `Read` at most ONCE for a completely missing critical import dependency.

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
Docker-specific: never `pip install` inside a running container. Update `pyproject.toml`, tell user to rebuild.

**Rule 5: BULK READING OVER SERIAL READING**
Use `cat file1 file2 file3` in one Bash call rather than three sequential `Read` calls.

</part_1>

---

<part_2 title="Tool Paradigms">

**AST Structural Search**
Find patterns by syntax, not text matching. Use AST structural code search and replace (e.g. `ast_grep`) instead of raw `sed`/`awk` when matching syntactic constructs (function signatures, class hierarchies, import patterns). AST search is refactor-safe — it won't match comments or strings that happen to contain the pattern.

**LSP Integration (Serena-First Navigation)**
Enforce semantic navigation. Before reading any file for structure, use the Language Server:
1. `serena__get_symbols_overview(file)` — signatures only (~200 tokens vs ~2,000 per file)
2. `serena__find_symbol(name)` — file + line number (~50 tokens)
3. `serena__read_file(file, start_line, end_line)` — targeted range after locating the symbol
4. `serena__get_diagnostics(file)` — type errors BEFORE running tests (circuit breaker prevention)
5. Full `Read`/`cat` — last resort: only for `<file>` XML injection into sub-agent prompts

Use Hover info, go-to-definition, find references, and project-wide type checking via the Language Server before modifying code. Never navigate by guessing file paths when Serena is available.

**Python REPL**
Use the persistent Python REPL for complex scripts instead of multiline `bash -c 'python ...'`. REPL preserves state between calls.

</part_2>

---

<part_3 title="Active Project Rules">

<!-- Unconditional rules: always loaded -->
@.claude/rules/project/rule-001-tenant-isolation.md
@.claude/rules/project/rule-003-no-explore-agents-for-file-reading.md
@.claude/rules/project/rule-004-ai-reference-check-every-session.md
@.claude/rules/project/rule-007-phase-gate-proceed-means-gate-steps.md
@.claude/rules/project/rule-009-serena-first-navigation.md
@.claude/rules/project/rule-010-compress-state-before-parallel-waves.md
@.claude/rules/project/rule-011-eu-ai-act-data-boundary.md
@.claude/rules/project/rule-017-no-direct-db-access.md

<!-- Path-scoped rules: auto-loaded only when working on matching files -->
<!-- rule-002 (migration): backend/app/db/**, backend/alembic/** -->
<!-- rule-005 (no bash -c): backend/tests/**, docs/handoffs/** -->
<!-- rule-006 (no QA subagents): backend/tests/** -->
<!-- rule-008 (docker fix): infra/**, backend/app/core/config.py, backend/Dockerfile -->
<!-- rule-012 (MCP trust + RAG): ai/mcp/**, ai/rag/** -->
<!-- rule-013 (docker COPY no shell ops): infra/**, infra/docker/** -->
<!-- rule-014 (registry enforcement opt-in): ai/mcp/**, backend/app/** -->
<!-- rule-015 (host execution air-gap): backend/**, ai/** -->
<!-- rule-016 (external content untrusted): .claude/agents/**, docs/handoffs/** -->

</part_3>

---

<part_4 title="Primary References">

| Reference | Purpose |
|---|---|
| `docs/AI_REFERENCE.md` | Stack, ports, make targets, test commands — ground truth. Read at every Speed 2 session start. If missing: run `/init-ai-reference` BEFORE anything else. |
| `docs/backlog/BACKLOG.md` | Current phase and US status |
| `.claude/agents/orchestrator.md` | Full Speed 2 workflow, delegation, phase gates, agent routing |
| `.claude/agents/product-owner.md` | Speed 1/2 mode selection, Task Complexity Matrix, US format |

</part_4>

---

<part_5 title="Hard Rules (never break)">

Full constraint list: see `@.claude/agents/orchestrator.md` `<hard_constraints>` section.
Key invariants: no self-approval (rule 17), no code exfiltration (rule-011), no delegation without acceptance criteria, no bare file paths (always `<file>` XML injection).

Audit files (`docs/ARCHITECTURE_STATE.md`, `docs/CONSISTENCY_LOG.md`, `docs/SESSION_COSTS.md`) are agent-forbidden-write paths. Only `/handoff` and `/phase-retrospective` commands may append to them via `echo >>`. The Write tool on these files is forbidden for all agents.

</part_5>
