---
version: "3.0"
type: framework-governance
framework: oh-my-claudecode-enterprise
updated: "2026-03-30"
default_model: claude-haiku-4-5-20251001
escalation_model: claude-sonnet-4-6
peak_model: claude-opus-4-6
---

# CLAUDE.md — Global Physics
> These rules are **ALWAYS ACTIVE** for every agent, every session, no exceptions.
> Workflow: see @.claude/agents/orchestrator.md · Planning & US format: see @.claude/agents/product-owner.md

---

## Part 1 — Token Optimization (5 Core Rules)

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

---

## Part 2 — Tool Paradigms

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
Never use multiline `bash -c 'python ...'` for complex scripts. Use the persistent Python REPL environment (with pandas, numpy, and matplotlib available) for:
- Data analysis and exploration
- Complex script execution that requires state between steps
- Integration testing that requires async setup/teardown
- Generating charts or structured output from data
The REPL preserves variables between calls — use it for iterative workflows instead of re-running entire scripts.

---

## Part 3 — Active Project Rules

@.claude/rules/project/rule-001-tenant-isolation.md
@.claude/rules/project/rule-002-migration-before-model.md
@.claude/rules/project/rule-003-no-explore-agents-for-file-reading.md
@.claude/rules/project/rule-004-ai-reference-check-every-session.md
@.claude/rules/project/rule-005-docwriter-no-multiline-bash.md
@.claude/rules/project/rule-006-no-qa-mode-a-subagents.md
@.claude/rules/project/rule-007-phase-gate-proceed-means-gate-steps.md
@.claude/rules/project/rule-008-pre-edit-read-docker-baked-files.md
@.claude/rules/project/rule-009-serena-first-navigation.md
@.claude/rules/project/rule-010-compress-state-before-parallel-waves.md
@.claude/rules/project/rule-011-eu-ai-act-data-boundary.md

---

## Part 4 — Primary References

| Reference | Purpose |
|---|---|
| `docs/AI_REFERENCE.md` | Stack, ports, make targets, test commands — ground truth. Read at every Speed 2 session start. If missing: run `/init-ai-reference` BEFORE anything else. |
| `docs/backlog/BACKLOG.md` | Current phase and US status |
| `.claude/agents/orchestrator.md` | Full Speed 2 workflow, delegation, phase gates, agent routing |
| `.claude/agents/product-owner.md` | Speed 1/2 mode selection, Task Complexity Matrix, US format |
| `.claude/workflow.md` | Phase dependency graph |

---

## Part 5 — Hard Rules (never break)

1. Never write application code yourself — always delegate via Agent tool
2. Never skip Phase 1 — no delegation without a written plan
3. Never delegate without acceptance criteria
4. Always wait for explicit user approval at every US checkpoint and Phase Gate
5. Never pass the full spec to a sub-agent — context isolation is non-negotiable
6. Never pass bare file paths — always inject raw content via `<file>` XML tags
7. Schema changes → Backend Dev + AI/ML Engineer coordination required
8. Auth/RBAC/plugins/MCP output → Security Engineer sign-off required
9. Tenant isolation → explicitly verified in every US that touches data access
10. Sub-agents do not communicate with each other — all coordination through the Tech Lead
11. Files on disk are the only shared state between agents
12. Never mark a US done without running the smoke test
13. Never proceed past a Phase Gate if service health checks fail
14. Never spawn DocWriter Mode A without injecting `<git_diff>` and `<metrics>` XML blocks
15. After every `/phase-retrospective`: append one cost row to `docs/SESSION_COSTS.md`
16. Never close a Phase Gate without running `/phase-retrospective` and presenting the full report
17. NEVER SELF-APPROVE: The implementing agent for a US and the judge/verifier must always be different agents
18. EU AI ACT (rule-011): No code or session data transmitted outside project directory boundary
