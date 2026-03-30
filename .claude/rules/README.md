# Rules Architecture

Rules are discrete behavioral constraints in `.claude/rules/project/`. Activated via `@` imports in CLAUDE.md.
Compact format: `## Constraint` + `## Why` (1 line) + `## Pattern` (1 example). Verbose originals in `archive/`.
Survival test: "Would this rule have prevented at least one circuit-breaker trigger or QA bounce-back?"
