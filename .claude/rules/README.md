# Rules Architecture

Rules are discrete behavioral constraints in `.claude/rules/project/`. Activated via `@` imports in CLAUDE.md.
Compact format: `## Constraint` + `## Why` (1 line) + `## Pattern` (1 example). Verbose originals in `archive/`.
Survival test: "Would this rule have prevented at least one circuit-breaker trigger or QA bounce-back?"

---

## Choosing the Right Format

| Question | Answer | Use |
|---|---|---|
| Could *any* agent violate this? | Yes — it's a behavioral red line | **Rule** (always-loaded constraint) |
| Is this a procedure for a *specific task*? | Yes — it's a how-to | **Skill** (loaded on-demand at task start) |
| Does a *human* invoke this explicitly? | Yes — it's a macro | **Command** (zero cost until `/command` called) |

**Token cost model:**
- Rule: loaded every session where the path matches — keep small, keep few
- Skill: 0 tokens until the trigger condition is met
- Command: 0 tokens until the user runs `/command`

**Example:** Hart's Rules for audience-aware writing is a **Skill**, not a Rule. Only `doc-writer` uses it, only during Mode B. A path-scoped Rule on `docs/**` would load for *any* agent touching a doc file — taxing sessions where writing quality is irrelevant. See `.claude/skills/writing-audience.md`.
