# GitHub Copilot Instructions

> Global rules for all Copilot Chat and Copilot Edits interactions in this repository.
> For Claude Code orchestration, see `.claude/`. These two setups coexist — do not mix their conventions.

---

## Operating Model: Two Speeds

### Speed 1 — Copilot Mode (you drive)

Use for bug fixes, small refactors, config changes, adding a field, quick doc edits.

**The contract:**
- User attaches the specific file(s) the change lives in
- You read only those files
- You make a targeted edit and show what changed
- You do not open, read, or suggest changes to other files

**Good Speed 1 prompts:**
- "Fix the KeyError on line 47 of quota_service.py — file attached"
- "Add `updated_at` to the Tenant model — see models.py"

**Bad Speed 1 prompts (require more context, not Copilot's job):**
- "Look through the codebase and find all quota checks"
- "Refactor the entire auth layer"

### Speed 2 — Orchestration Mode (Claude Code only)

Speed 2 involves multi-step planning, sub-agent delegation, and phase gates. This is handled exclusively through Claude Code (`.claude/agents/`). **Do not attempt Speed 2 workflows in Copilot Chat.**

Note: GitHub added agent support to Copilot Chat (late 2024), but Copilot agents are tool-wrapper *personas*, not governance systems. See [COPILOT_GAP_NOTES.md#why-copilot-chat-agents-dont-solve-this](COPILOT_GAP_NOTES.md#why-copilot-chat-agents-dont-solve-this) for details on architectural differences and why they cannot replace Claude Code's multi-agent orchestration.

---

## Token Anti-Patterns: Never Do These

1. **No autonomous exploration** — do not suggest running `ls`, `find`, `tree`, or `glob`. Do not read files the user did not attach.
2. **Silence verbose outputs** — any bash command you suggest should suppress noise: `pip install -q`, `pytest -q --tb=short`, `npm install --silent`, build output piped to `/dev/null`.
3. **Circuit breaker** — if a test or command fails twice with targeted fixes, stop. Report: (a) exact error, (b) what was tried, (c) root cause hypothesis. Do not keep retrying.
4. **Targeted editing** — never rewrite an entire file to change 3 lines. Use surgical edits. If more than 30% of the file would change, ask the user to confirm scope first.
5. **Atomic changes** — make the smallest correct change that satisfies the request. Do not refactor adjacent code. Do not add features not in the request.

---

## Serena Code Navigation (when Serena MCP is loaded)

Serena is configured in `.vscode/mcp.json`. Use it instead of asking the user to attach files for context gathering.

- **Before reading any file for structure**: call `mcp_oraios_serena_get_symbols_overview(path)` — full symbol signatures at ~200 tokens vs ~2,000 for the whole file
- **To locate a function or class**: call `mcp_oraios_serena_find_symbol(name)` before using grep or asking the user to search
- **Before running tests or editing a file**: call `mcp_oraios_serena_get_diagnostics(path)` to catch type errors before they become test failures
- **Full `#file:` attachment**: appropriate only when you need entire file context for an edit spanning multiple functions

Context7 is also configured via `.vscode/mcp.json`. Use `mcp_context7_query_docs` for current library documentation. Never include source code or schema in Context7 queries — library name and question only.

---

## Project Ground Truth

Stack, ports, make targets, and test commands are in `docs/AI_REFERENCE.md`. Read it if attached; do not guess the stack.

The backlog and US status are in `docs/backlog/BACKLOG.md`.

---

## Security Constraints (always active)

- Every SQLAlchemy query on tenant-owned data must include `.where(Model.tenant_id == tenant_id)`. The `tenant_id` comes from the JWT token — never from the request body. A query without tenant scope is a data breach, not a bug.
- Do not generate or suggest code that transmits source code, schema, or session data to third-party services.
- Do not suggest bypassing security controls (`--no-verify`, disabling auth middleware, skipping RBAC checks).
