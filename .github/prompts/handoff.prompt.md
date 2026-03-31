---
description: Generate a structured handoff document for a completed task
---

Generate a handoff document for the work just completed. Include:

## Structure

**Header:** US or task ID, date, implementing agent or developer, model used if relevant.

**Summary (3 lines max):** What was built, what changed, what it enables.

**Files changed:** List with one-line description of what changed in each file. Do not include full diffs — use `git diff --stat` output as the basis.

**Acceptance criteria status:** For each AC item in the User Story, mark PASS or FAIL with one line of evidence (test name, curl output, or observation).

**Manual test instructions:** Step-by-step commands a reviewer can run to verify the feature works end-to-end. No multiline `python -c` — write scripts to files and execute them.

**Token metrics (if available):** input tokens | output tokens | cache read tokens | cache creation tokens.

**Residual risks:** Anything not fully covered, known edge cases, follow-up US needed.

---

Append a 3-line summary to `docs/ARCHITECTURE_STATE.md` in this format:
```
[date] [US-NNN] [agent/dev] — [what was built]. Key files: [list]. AC: [N/N passed].
```
