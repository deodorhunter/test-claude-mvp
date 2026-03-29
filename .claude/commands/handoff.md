---
name: handoff
description: "Runs git diff on the current or specified branch, parses the diff without reading raw source files, and appends a metrics row and 3-line summary to docs/ARCHITECTURE_STATE.md using append-only echo >>. Use after merging a User Story to keep the architecture state current."
version: "1.0.0"
model: claude-haiku-4-5-20251001
destructive: false
output: docs/ARCHITECTURE_STATE.md  # append-only
speed: 2
trigger: "/handoff US-NNN"
parallel_safe: true
requires: [docs/ARCHITECTURE_STATE.md]
---

# Command: /handoff
> After a US is merged, run this to append a summary + metrics row to `docs/ARCHITECTURE_STATE.md`.
> Uses git diff — never reads raw source files.
> Invocation: type `/handoff US-NNN` in the chat (replace NNN with the US number).

---

## What This Command Does

1. Gets the diff of what was just merged
2. Parses the diff (no raw file reads) to extract the key changes
3. Appends a metrics row and a 3-line summary to `docs/ARCHITECTURE_STATE.md` using `>>`
4. Never overwrites the state file — append-only

---

## Instructions for Claude

You will be given a US number (e.g. `US-010`). Execute these steps:

### Step 1 — Get the Diff

```bash
# If the US branch is already merged to main:
git log --oneline -10

# Get the diff of the last merge commit (or specify a commit range)
git diff HEAD~1..HEAD --stat 2>/dev/null
git diff HEAD~1..HEAD -- '*.py' '*.ts' '*.tsx' '*.yml' '*.yaml' '*.toml' 2>/dev/null | head -200
```

If the branch is not yet merged (reviewing before merge), use:
```bash
git diff main...HEAD --stat 2>/dev/null
git diff main...HEAD -- '*.py' '*.ts' '*.tsx' '*.yml' '*.yaml' 2>/dev/null | head -200
```

**Do NOT use the `Read` tool on source files. The diff is the only source of truth.**

### Step 2 — Parse the Diff

From the diff output, extract:
- Files created or modified (from `+++ b/...` lines)
- Key function/class names added (from `+def `, `+class `, `+async def `, `+export ` lines)
- Tables or migrations added (from `+op.create_table`, `+CREATE TABLE`, `+class.*Model` patterns)
- Endpoints added (from `+@router.`, `+@app.` patterns)
- Tests added (from `+def test_` patterns and file names)

Do NOT read the full file for any path in the diff. The diff hunks contain everything needed.

### Step 3 — Collect Metrics

Check if the user provided token metrics in their message (input/output/cache tokens from the agent invocation). If provided, use them. If not, use "N/A".

Expected format from user (optional):
```
input: 4821  output: 1203  cache_read: 12400  cache_creation: 0
model: claude-haiku-4-5-20251001
```

### Step 4 — Append to `docs/ARCHITECTURE_STATE.md`

Use Bash with `>>` (NEVER `>`). Execute these two commands:

```bash
# Verify the file exists first
test -f docs/ARCHITECTURE_STATE.md && echo "exists" || echo "MISSING — create it first"
```

```bash
# Append metrics row (fill in values from steps 2-3)
echo "| US-NNN | [Agent Name] | [model-id] | [input] | [output] | [cache_read] | [cache_creation] | $(date +%Y-%m-%d) |" >> docs/ARCHITECTURE_STATE.md
```

```bash
# Append 3-line summary
printf '\n### US-NNN — [US Title]\n**Date:** %s | **Agent:** [name] | **What was built:** [one sentence from the diff]\n' "$(date +%Y-%m-%d)" >> docs/ARCHITECTURE_STATE.md
```

Replace `[US-NNN]`, `[US Title]`, `[Agent Name]`, `[model-id]`, and the token values with real data.

### Step 5 — Verify and Report

```bash
tail -10 docs/ARCHITECTURE_STATE.md
```

Confirm:
- ✅ Metrics row appended to the table
- ✅ 3-line summary appended to the Completed User Stories section
- ✅ `docs/ARCHITECTURE_STATE.md` was NOT rewritten — only appended

Report a 3-line summary to the user of what was recorded.

---

## Hard Constraints

- **NEVER use `>` — only `>>`**
- **NEVER use the `Write` tool on `docs/ARCHITECTURE_STATE.md`**
- **NEVER use the `Edit` tool to rewrite the whole file**
- Do NOT read raw source files — parse the diff only
- If `docs/ARCHITECTURE_STATE.md` does not exist, stop and tell the user to create it first using the scaffold in `CLAUDE.md`
