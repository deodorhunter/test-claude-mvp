# Navigation Benchmark Tasks

Standard tasks for comparing Serena vs codebase-memory-mcp (CBM).
Run identically for both backends. See `benchmark/results/` for results.

## Methodology

- Each run uses a sub-agent forced to use **only** the target backend's tools
- Sub-agent prompt: "Answer tasks T1–T5 below. Use ONLY [backend] MCP tools for navigation — no Read/Grep/Glob except as last resort after MCP miss. Report every tool call made and its output size."
- Tokens measured via `.claude/subagent-token-log.txt` (SubagentStop hook)
- Accuracy scored manually: 3=correct+complete, 2=partial/missing fields, 1=wrong
- Run B (CBM) requires warm-up: run `cbm index` on the workspace before benchmark tasks

## Tasks

**T1 — Class definition with fields**
> Find the `Plugin` model class definition. List all its fields and their types.
- Expected: SQLAlchemy model fields (id, tenant_id, name, etc.) with types
- Serena strength: AST-level field extraction
- CBM strength: persistent symbol index

**T2 — Call path tracing**
> Trace the call path from the `/api/plugins` GET route handler down to the database query layer. List each function in order.
- Expected: route → service → repository → SQLAlchemy query chain
- Both tools tested: CBM has explicit call_path tool; Serena uses find_referencing_symbols

**T3 — Cross-file reference search**
> Find all Python files (outside of `backend/app/db/models.py`) that reference `tenant_id`.
- Expected: list of files with line references
- CBM strength: wide codebase search without file-by-file reading
- Serena strength: find_referencing_symbols

**T4 — Class method enumeration**
> What public methods does `CostAwarePlanner` expose? Include method signatures.
- Expected: method names + parameter types from `ai/planner/planner.py`
- Serena strength: get_symbols_overview gives signatures directly

**T5 — Import graph**
> Which Python modules import from `ai/mcp/registry.py`?
- Expected: list of files that have `from ai.mcp.registry import ...` or equivalent
- CBM strength: impact analysis / import graph
- Serena strength: find_referencing_symbols

## Scoring Template

| Task | Serena tokens | CBM tokens | Serena tool calls | CBM tool calls | Serena acc (1-3) | CBM acc (1-3) |
|------|--------------|-----------|-------------------|----------------|------------------|---------------|
| T1   |              |           |                   |                |                  |               |
| T2   |              |           |                   |                |                  |               |
| T3   |              |           |                   |                |                  |               |
| T4   |              |           |                   |                |                  |               |
| T5   |              |           |                   |                |                  |               |
| **Total** |         |           |                   |                |                  |               |

## Run Instructions

### Run A — Serena
1. Verify `NAVIGATION_BACKEND=serena` in `.claude/settings.json`
2. Spawn sub-agent with tasks T1–T5, constraint: Serena tools only
3. Record tokens from `.claude/subagent-token-log.txt`

### Run B — CBM
1. Build image: `docker compose -f infra/docker-compose.ai-tools.yml build codebase-memory-mcp`
2. Change `NAVIGATION_BACKEND` to `cbm` in `.claude/settings.json`
3. Restart Claude Code (MCP servers reload on restart)
4. Warm up CBM index (run CBM MCP once with a simple query before benchmark)
5. Spawn sub-agent with tasks T1–T5, constraint: CBM tools only
6. Record tokens from `.claude/subagent-token-log.txt`
7. Revert `NAVIGATION_BACKEND` to `serena` when done
