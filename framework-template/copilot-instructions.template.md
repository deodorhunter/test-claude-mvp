<!-- framework-template v3.0 | synced: 2026-04-02 -->
# GitHub Copilot Instructions

> Global rules for Copilot Chat and Copilot Edits in this repository.
> For Claude Code orchestration, see `.claude/`.

## Speed 1 — Copilot Mode (you drive)

Use for bug fixes, small refactors, adding a field, quick doc edits.

- Attach the specific file(s) the change lives in
- You read only those files and make a targeted edit
- Do not open, read, or suggest changes to other files

## Token Anti-Patterns: Never Do These

1. **No autonomous exploration** — do not run or suggest `ls`, `find`, `tree`, `glob`
2. **Silence verbose outputs** — `pip install -q`, `pytest -q --tb=short`, `npm install --silent`
3. **Circuit breaker** — if a fix fails twice, stop: report (a) exact error, (b) what was tried, (c) hypothesis
4. **Targeted editing** — never rewrite a whole file to change 3 lines
5. **Atomic changes** — smallest correct change only; no adjacent refactors

## Project Ground Truth

Stack, ports, and test commands are in `docs/AI_REFERENCE.md`. Read it if attached; do not guess.

## Speed 2

Speed 2 orchestration is handled by Claude Code (`.claude/agents/`). Do not attempt it in Copilot Chat.

<!-- ADAPT: add project-specific security constraints (e.g. tenant isolation rule) here -->
