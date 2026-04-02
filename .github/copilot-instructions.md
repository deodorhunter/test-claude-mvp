# Copilot Chat Instructions — Standalone Guide

> **For this repository:** Copilot Chat operates in Speed 1 mode only.
> **For multi-step features, orchestration, or planning:** Use Claude Code CLI (see "When to Use Claude Code" section).

---

## What Copilot Does (Speed 1 Mode)

Copilot is fast, interactive, and stateful within a conversation. Use it for:

- Bug fixes with clear error messages
- Small refactors (1–3 files, <100 lines changed)
- Config updates, adding fields to models, quick doc edits
- Quick tests of small code changes

**The contract:**
- User attaches the specific file(s) the change lives in
- You read only those files (+ optional MCP lookups for context)
- You make targeted edits and show what changed
- You do not explore the codebase autonomously

---

## Speed 1 Workflow — Annotated Examples

**Example 1: Bug fix with clear error**
```
User: "KeyError on line 47 of quota_service.py (attached) — tenant_id not in dict"
Copilot:
  1. Read attached file
  2. Locate the error (line 47)
  3. Identify root cause: dict key missing
  4. Propose fix (check key before access OR provide default)
  5. Show edited lines only
  6. Explain: "The error happens because... The fix guards against..."
```

**Example 2: Add a field to a model**
```
User: "Add `updated_at` timestamp to Tenant model (models.py attached). Auto-update on save."
Copilot:
  1. Read models.py
  2. Find Tenant class
  3. Add datetime import (if missing)
  4. Add `updated_at: datetime = Field(default_factory=datetime.utcnow)`
  5. For auto-update: "You'll need to add a SQLAlchemy event listener to models.py or a pre-commit hook. Show me the existing pattern?"
  6. If user provides the pattern: implement it. If not: suggest the two common approaches + point to a minimal example.
```

**Example 3: When you can't fix it**
```
User: "This test is failing. I don't understand why. File attached."
Copilot:
  1. Read the test + attached context
  2. Run the test (if you can, via terminal)
  3. See the actual error
  4. First attempt: targeted fix based on error
  5. If that doesn't work: suggest "This looks like a dependency issue or schema mismatch. Can you run: make migrate && pytest tests/test_file.py -v"
  6. If that still doesn't work (second failure): STOP. Report: (a) exact error (≤10 lines), (b) what you tried, (c) hypothesis ("could be schema, fixture setup, async timing..."). Suggest the user attach conftest.py or the fixture definition, or use Claude Code for deeper diagnosis.
```

---

## Project Ground Truth

**Stack, ports, make targets, test commands:**
Read `docs/AI_REFERENCE.md` if attached. Do not guess the stack.

**Backlog and Sprint Status:**
Read `docs/backlog/BACKLOG.md` if attached to understand dependencies and priorities.

**Security Rules** (always enforced):
- Every SQLAlchemy query on tenant-owned data: `.where(Model.tenant_id == tenant_id)`. Tenant_id comes from JWT token, never from request body.
- No code suggesting transmission of source, schema, or session data to third parties.
- No bypassing security (`--no-verify`, disabling auth, skipping RBAC).

---

## Token Anti-Patterns — Never Do These in Copilot

1. **No exploration** — Do not suggest `ls`, `find`, `tree`, `glob`, or reading unattached files. Work with what the user provides.
2. **Silence noise** — Any bash command: `pip install -q`, `pytest -q --tb=short`, `npm --silent`. No build spam.
3. **Circuit breaker** — If a fix fails twice, stop. Report exact error + what you tried + hypothesis. Don't retry endlessly.
4. **Surgical edits** — Don't rewrite entire files to change 3 lines. If >30% of the file changes, ask the user to confirm scope first.
5. **Atomic changes** — Smallest correct change. Don't refactor adjacent code or add features not requested.

---

## Serena Code Navigation (MCP Integration)

If Serena MCP is loaded in `.vscode/mcp.json` (Copilot's MCP tools), use it to reduce context load:

**Serena functions:**
- `serena_get_symbols_overview(file_path)` — Function/class signatures (~200 tokens vs ~2,000 for full file)
- `serena_find_symbol(name)` — Locate a function/class by name + get file + line number
- `serena_get_diagnostics(file_path)` — Type errors, linting issues before you edit

**When to use Serena:**
- User asks about a function: use `find_symbol` instead of grepping
- Before reading a large file for structure: use `symbols_overview` first
- Before editing a file with type annotations: run `get_diagnostics` to catch errors early

**When NOT to use Serena:**
- User provides the file attached — just read it directly
- You need the full function body for context — Serena gives signatures only

---

## Regex-based Targeted Reads (Optional Efficiency Pattern)

Copilot's strengths: fast file reading, regex search. Consider this pattern for large files:

1. Ask user: "Is there a specific function/section you're changing?"
2. If yes: search for that function definition using regex, read just that section
3. If no: "The whole file is needed for this change. Is it OK to read the full file?"

This avoids loading 5,000-line files when you only need 50 lines.

**Example regex pattern:**
User: "Fix the authenticate() function in auth_handler.py (attached). It has a bug on line 42."
Copilot: Use regex `def authenticate` → find the function → read just that function + surrounding context (±10 lines).

---

## When to Use Claude Code Instead of Copilot

**Multi-step features** (requires planning):
- "Add a complete feature that touches models, API routes, and frontend"
- "Refactor 5 related modules to implement a new pattern"

**Complex planning or review needed** (requires criticism before implementation):
- "Design a new auth flow for multi-tenant scenarios"
- "Plan a migration from MongoDBto PostgreSQL"

**Integration of many pieces** (requires orchestration):
- "Implement a full quote system from schema to API to UI"

**See the Claude Code section of this repo's docs for setup and mode selection.**

---

## Instructions for Specific Tasks

Read the files in `.github/instructions/` for patterns on:
- How to structure Speed 1 prompts
- Copilot + MCP patterns for your stack
- Common anti-patterns for your project

Each instruction file is standalone — you don't need to cross-reference CLAUDE.md or Claude Code docs.

---

## Feedback & Updates

If you find a bug in these instructions or have a suggestion:

1. Create a GitHub issue with label `[copilot-instructions]`
2. Or comment in `HOW-TO-ADOPT.md` feedback section

These instructions are maintained separately from Claude Code governance and can be updated without affecting the orchestration layer.
