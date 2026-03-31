---
description: Capture current session state before context gets too large
---

Produce a session state snapshot for `docs/.temp_context.md`. This is used to resume after clearing the context window.

## Snapshot must include

1. **Current phase and US status** — which phase, which US are done/in-progress/blocked
2. **All modified files** — paths only, one per line
3. **Last test commands run and their results** — exact commands, pass/fail, error summary if failing
4. **Open blockers** — any unresolved issues blocking next steps
5. **Next action** — the single next step to take after context is cleared

## Format

Write the snapshot as a concise markdown file (target: under 50 lines). Do not include full file contents or code — paths and status only.

After writing `docs/.temp_context.md`, tell the user: "State saved. You can now run `/clear` and resume by reading `docs/.temp_context.md`."

---

Note: This is the manual equivalent of the Claude Code `/compress-state` command. In Claude Code, the command also triggers context clearing automatically. In Copilot, that step is manual.
