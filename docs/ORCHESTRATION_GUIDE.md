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

2. **Missing file context — Read storm** — Delegating without injecting existing code used to force agents to `Read` every candidate file. **Fix:** Sub-agents now self-navigate via Serena MCP (`mcp__serena__get_symbols_overview`). Inject `<file>` blocks only for algorithm-level detail.

3. **Wrong mode for complexity** — Asking Sonnet to fix a typo in config (~3× unnecessary cost). **Fix:** Use Task Complexity Matrix; Speed 1 Copilot for single-file work.

4. **Plan + implementation in one message** — Asking "Plan the refactor AND show me the code" loads 20k tokens of plan context that gets carried through all subsequent implementation work (unused). **Fix:** Request plan, wait for response, then request implementation in a separate prompt.

### Slash Command Catalog

Pre-generated command reference: see `docs/.command-catalog.md` for all 12 commands + descriptions. This avoids re-generating command metadata during agent delegations (~3k tokens saved per delegation).


### File Context Injection (Rule 009: Serena-First Navigation)

**Sub-agents have Serena MCP** — confirmed working 2026-04-05. Root cause of prior failures was `tools:` allowlist silently blocking MCP tools (GitHub issue #25200). All implementing agents now use `disallowedTools` + inline `mcpServers`. Sub-agents self-navigate via `mcp__serena__get_symbols_overview`.

**Orchestrator delegation — what to inject:**
- `<user_story>` — always
- `<file>` blocks — **only** for algorithm-level detail or DocWriter (which cannot Read files)
- Symbol injection (`<symbols>`) — no longer needed; sub-agents call Serena directly
- Orchestrator Serena calls reserved for **cross-file architectural analysis during planning**

| Approach | Cost | When to use |
|---|---|---|
| Sub-agent self-navigates via Serena | ~200 tokens/file in sub-agent | Default — all Python/TS structure queries |
| Full Read injection (`<file>` blocks) | ~2000 tokens/file in orchestrator | Algorithm-level edits, DocWriter (no Read access) |

**Cost comparison (typical 8-file delegation):**
- ❌ Old (orchestrator pre-flight): symbol overviews × 8 = ~1,600 tokens in orchestrator context
- ✅ New (sub-agent self-navigates): ~0 tokens in orchestrator context; sub-agent pays ~200 tokens/file at Haiku rates

**Scope:** Python and TypeScript files only. Markdown, YAML, JSON → inject via `<file>` blocks or Grep output.

**Serena degradation:** If a sub-agent reports Serena unavailable, inject `<file>` blocks for the specific files requested. Do not revert to orchestrator pre-flight as default.

### Speed 1 — Main Session Serena Navigation

When implementing directly (vertical slices, ≥4 domains), use the same Serena-first pattern as sub-agents:
1. `mcp__serena__get_symbols_overview(file)` — never `ls` or `cat` speculatively
2. `mcp__serena__find_symbol(name)` → targeted `Read` with line range
3. `mcp__serena__replace_symbol_body` — preferred over `Edit` for named function/class edits

Token cost: ~200 tokens/file for Serena overview vs ~2,000 for full Read. Rule 1 exploration block is mechanically enforced via `.claude/hooks/block-exploration.sh` in both main session and all sub-agents.

### Speed 1 with Copilot

Attach all relevant files explicitly in the Copilot sidebar. Keep edits surgical — modify one function or method at a time, not entire files.

Reference `.github/copilot-instructions.md` for project-specific context (tenant isolation, no exploration, no hallucinations).

Copilot has no Phase 2 orchestration equivalent — no agents, no delegations, no hand-off docs. For complex features requiring planning or cross-domain coordination, switch to Speed 2 (CLI mode).
