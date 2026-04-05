> Load this file when planning agent delegation. Not auto-loaded — read on demand.

## Model Routing

**Routing mechanism:** Each agent's `model:` key in its `.md` frontmatter is the **ONLY** routing mechanism for Claude Code. Model selection happens at agent initialization, not runtime.

### Per-Agent Model Assignment

| Agent | Default Model | Tier | When overridden |
|---|---|---|---|
| doc-writer | `claude-haiku-4-5-20251001` | LOW | Never — docs are always LOW complexity |
| qa-engineer | `claude-haiku-4-5-20251001` | LOW | Never — QA Mode A is always LOW |
| critic | `claude-haiku-4-5-20251001` | LOW | Never — plan review is LOW |
| debugger | `claude-haiku-4-5-20251001` | LOW | Never — debugging is LOW |
| product-owner | `claude-haiku-4-5-20251001` | LOW | Never — backlog work is LOW |
| orchestrator | `claude-sonnet-4-6` | MEDIUM | Never — coordination requires MEDIUM thinking |
| aiml-engineer | `claude-sonnet-4-6` | MEDIUM/HIGH default | Promote to Opus for codebase-wide AI refactors only |
| backend-dev | `claude-haiku-4-5-20251001` | LOW default | Promote to Sonnet for new abstractions, auth, complex logic |
| dev-ops | `claude-haiku-4-5-20251001` | LOW default | Promote to Sonnet for multi-service orchestration changes |
| frontend-dev | `claude-haiku-4-5-20251001` | LOW default | Promote to Sonnet for architectural UI decisions |
| security-engineer | `claude-sonnet-4-6` | HIGH default | Never demote — security always warrants Sonnet minimum |

### Task Complexity Matrix (Source of Truth)

**Used by orchestrator to set `model:` for `dynamic` agents at delegation time:**

| Tier | Criteria | Model | ultrathink? |
|---|---|---|---|
| LOW → Haiku | Simple CRUD, minor config, DocWriter (all modes), QA Mode A, formatting | `claude-haiku-4-5-20251001` | No |
| MEDIUM/HIGH → Sonnet | New abstractions, complex business logic, security impl, core architecture, auth/RBAC, full test suite (QA Mode B) | `claude-sonnet-4-6` | **Yes** — prepend `ultrathink` to agent system prompt |
| FULL-CODEBASE → Opus | Phase Gate security review >200K context, multi-phase dependency analysis | `claude-opus-4-6` | Yes |

### Typed Fallbacks + Orchestrator Override

Specialist agents declare typed fallback models in their frontmatter. These are safe defaults for non-orchestrated (ad-hoc Speed 1) spawning. In Speed 2, the orchestrator ALWAYS overrides via the Agent tool's `model` parameter per the Task Complexity Matrix — the frontmatter value is ignored when an override is provided.

**Speed 2 orchestrators must never skip the explicit override step.** Frontmatter defaults exist for fallback safety only, not as a substitute for Task Complexity Matrix decisions. The Agent tool's `model` parameter always takes precedence over frontmatter.

Previous pattern used `model: dynamic` as a sentinel value. This was replaced because `dynamic` is not a recognized Claude Code model identifier — it silently breaks agent spawning when no orchestrator override is provided (e.g. ad-hoc tests, Speed 1 direct invocations).

### Limitations & Constraints

- **No `smallFastModel` global setting:** Claude Code does not support a configuration key for "prefer Haiku everywhere". Model routing is per-agent via frontmatter only.
- **GitHub Models API:** GitHub Models has no Claude Code adapter. Model routing is not available when using GitHub Models as the underlying provider.
- **GitHub Copilot:** Copilot's model selection is tied to the user's subscription tier, not per-task. Individual agents cannot override the tier. Use Claude Code for per-US model control.
- **`model: dynamic` is invalid:** Claude Code does not recognize `dynamic` as a model name. Agents with this value fail at spawn time when no orchestrator override is provided. All specialist agents now use typed fallback defaults (see table above).

## Orchestration Patterns

### Speed 1 vs Speed 2 Decision Tree

**Speed 1 (Copilot Mode):** Use for bug fixes, minor config changes, simple CRUD, small refactors, quick doc updates.
- Criteria: ≤2 files modified, no new abstractions, single-domain work (e.g., fix DB config or add validation rule)
- No User Story created, no branching, no QA phase gate
- Model: Always `claude-haiku-4-5-20251001`

**Speed 2 (Orchestrator Mode):** Use for new features, new abstractions, multi-file changes, security work, architectural decisions.
- Criteria: ≥3 files touched, new abstractions introduced, multi-domain work (≥2 specialist domains)
- Mandatory: User Story, branch per US, phase gates, smoke tests
- Model: Per Task Complexity Matrix (Haiku for LOW, Sonnet for MEDIUM/HIGH, Opus for full-codebase security)

**Decision heuristic:** "Does this change introduce new patterns or touch ≥3 files across different layers?" If yes → Speed 2. If no → Speed 1.

### Model Comparison

See `docs/MODEL_COMPARISON.md` for a detailed comparison of Claude API vs Copilot vs local Ollama setups, including cost, latency, compliance, and use case recommendations.

### Prompt Templates

**Front-load file locations:** Write "Edit `backend/app/auth/jwt.py` to add refresh token logic" instead of "I need help with the auth module".

**Always name exact files:** Include paths in the first sentence so Claude doesn't explore to find them:
```
Add user_id column to Plugin model in backend/app/db/models.py,
then add a query helper in backend/app/db/crud.py to filter by user.
```

**Specify model tier explicitly:** "This is LOW complexity (config tweak) — use Haiku" or "This is HIGH complexity (auth + RBAC) — use Sonnet with ultrathink".

**Separate plan from implementation:** Ask for planning first ("Write a brief plan for fixing the rate limiter"), wait for output, then ask for implementation. Avoids 20k tokens of unused plan context bleeding through.

### Anti-patterns (Token Cost Estimates)

1. **Vague prompt without file references** — "Help me fix the API" forces Claude to explore endpoints, models, config files. Wasted ~15k tokens per missing file ref. **Fix:** Name 3–5 exact files upfront.

2. **Missing file context — Read storm** — Delegating without injecting existing code forces agent to `Read` every candidate file. ~3k tokens per unneeded file read (8–10 reads per session typical). **Fix:** Use `cat` + `<file>` XML injection before delegating; use Serena for symbols-only when full code not needed.

3. **Wrong mode for complexity** — Asking Sonnet to fix a typo in config (~3× unnecessary cost). **Fix:** Use Task Complexity Matrix; Speed 1 Copilot for single-file work.

4. **Plan + implementation in one message** — Asking "Plan the refactor AND show me the code" loads 20k tokens of plan context that gets carried through all subsequent implementation work (unused). **Fix:** Request plan, wait for response, then request implementation in a separate prompt.

### Slash Command Catalog

Pre-generated command reference: see `docs/.command-catalog.md` for all 12 commands + descriptions. This avoids re-generating command metadata during agent delegations (~3k tokens saved per delegation).


### File Context Injection (Rules 009 + 010: Symbol-First Navigation)

**Critical constraint:** Serena MCP tool calls are NOT available in sub-agent sessions — confirmed 2026-04-04. Sub-agents receive Serena's system instructions but cannot call `mcp__serena__*` functions (Claude Code MCP bridge limitation). The orchestrator is the sole Serena proxy.

**Mandatory orchestrator pre-flight for any US touching Python or TypeScript files:**
1. Identify files the delegated agent will need to read or edit
2. For each Python/TypeScript file: call `mcp__serena__get_symbols_overview` in the main session
3. Inject results as `<symbols path="...">` blocks in the delegation prompt
4. For implementation files needing full content: add `<file path="...">` blocks (targeted Read)
5. Never write "use Serena to navigate" in sub-agent instructions — the tool is unavailable

| Approach | Cost | When to use |
|---|---|---|
| Symbol overview (`mcp__serena__get_symbols_overview`) | ~200 tokens/file | Interfaces, class/function names — sub-agent doesn't need implementation details |
| Full Read injection (`<file>` blocks) | ~2000 tokens/file | Implementation changes, algorithm details, full context required |

**Cost comparison (typical 8-file delegation):**
- ❌ No pre-flight: sub-agent reads 8 files via Read = ~16,000 tokens
- ✅ Orchestrator pre-flight: symbol overviews × 8 = ~1,600 tokens + targeted reads for 1–2 key files = ~2,500 total

**Scope:** Python and TypeScript files only. Markdown, YAML, JSON → inject via `<file>` blocks or Grep output.

**Reference:** `.claude/agents/doc-writer.md` includes delegation prompt examples with `<symbols>` blocks.

### Speed 1 with Copilot

Attach all relevant files explicitly in the Copilot sidebar. Keep edits surgical — modify one function or method at a time, not entire files.

Reference `.github/copilot-instructions.md` for project-specific context (tenant isolation, no exploration, no hallucinations).

Copilot has no Phase 2 orchestration equivalent — no agents, no delegations, no hand-off docs. For complex features requiring planning or cross-domain coordination, switch to Speed 2 (CLI mode).
