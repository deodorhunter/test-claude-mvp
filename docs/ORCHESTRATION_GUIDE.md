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
| aiml-engineer | `dynamic` | Per-US | Orchestrator sets per Task Complexity Matrix |
| backend-dev | `dynamic` | Per-US | Orchestrator sets per Task Complexity Matrix |
| dev-ops | `dynamic` | Per-US | Orchestrator sets per Task Complexity Matrix |
| frontend-dev | `dynamic` | Per-US | Orchestrator sets per Task Complexity Matrix |
| security-engineer | `dynamic` | Per-US | Orchestrator sets per Task Complexity Matrix |

### Task Complexity Matrix (Source of Truth)

**Used by orchestrator to set `model:` for `dynamic` agents at delegation time:**

| Tier | Criteria | Model | ultrathink? |
|---|---|---|---|
| LOW → Haiku | Simple CRUD, minor config, DocWriter (all modes), QA Mode A, formatting | `claude-haiku-4-5-20251001` | No |
| MEDIUM/HIGH → Sonnet | New abstractions, complex business logic, security impl, core architecture, auth/RBAC, full test suite (QA Mode B) | `claude-sonnet-4-6` | **Yes** — prepend `ultrathink` to agent system prompt |
| FULL-CODEBASE → Opus | Phase Gate security review >200K context, multi-phase dependency analysis | `claude-opus-4-6` | Yes |

### Dynamic Agents Explained

Agents with `model: dynamic` have their model set by the orchestrator **at delegation time**. The orchestrator reads the US complexity (via Task Complexity Matrix) and injects the appropriate model into the agent's system prompt. This enables cost optimization: a backend-dev agent handles both simple config changes (Haiku) and complex distributed tracing (Sonnet) without code changes.

### Limitations & Constraints

- **No `smallFastModel` global setting:** Claude Code does not support a configuration key for "prefer Haiku everywhere". Model routing is per-agent via frontmatter only.
- **GitHub Models API:** GitHub Models has no Claude Code adapter. Model routing is not available when using GitHub Models as the underlying provider.
- **GitHub Copilot:** Copilot's model selection is tied to the user's subscription tier, not per-task. Individual agents cannot override the tier. Use Claude Code for per-US model control.

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

**Quick reference (full catalog in `.command-catalog.md`):**

| Command | Use case |
|---|---|
| `/consistency-check` | Scores agent output against US acceptance criteria; blocks at ≤2 |
| `/deep-interview` | Extracts testable requirements from fuzzy intent via Socratic questioning |
| `/handoff` | Appends metrics + summary to ARCHITECTURE_STATE.md after merging a US |
| `/init-ai-reference` | Scans repo, writes AI_REFERENCE.md; run when stack changes |
| `/judge` | Post-implementation pre-QA: checks git diff against US acceptance criteria |
| `/learn` | Distills hard-won session insight into reusable note in .session-notes.md |
| `/notepad` | Appends timestamped entry to .session-notes.md (Learnings/Decisions/Issues) |
| `/phase-retrospective` | End-of-phase report; appends cost row to SESSION_COSTS.md |
| `/refine-backlog` | Pre-sprint yes-man filter on all Backlog US; produces verdicts |
| `/reflexion` | Phase-gate ritual: extracts 1–3 durable rules into .claude/rules/project/ |
| `/review-session` | End-of-session quality audit (audience, EU AI Act, links, ADAPT) |

### File Context Injection (Rule-009: Symbol-First Navigation)

**Principle:** For documentation-only tasks (no code changes), use Serena symbol overviews instead of full file reads. Reduces bloat, improves token efficiency.

| Approach | Cost | When to use |
|---|---|---|
| Symbol overview (`serena__get_symbols_overview`) | ~200 tokens/file | Writing handoff docs, mode B architecture summaries, reference context |
| Full Read injection (`<file>` blocks) | ~2000 tokens/file | Code changes, implementation details, algorithm explanation required |

**Cost comparison (typical 8-file doc task):**
- ❌ Anti-pattern: Full Read × 8 files = ~16,000 tokens wasted (10–15k per doc phase)
- ✅ Pattern: Symbol overview × 8 files = ~1,600 tokens + targeted reads for 1–2 critical sections = ~2,500 total

**Orchestrator checklist before delegating a doc task:**
1. Identify files referenced (API routes, models, configs, etc.)
2. For each file: "Does the doc need implementation details or just interfaces?" → Yes/implementation: full Read | No/interfaces only: symbol overview
3. Inject `<symbols>` blocks for 6–8 overview files
4. Inject `<file>` blocks for 1–2 critical sections (if needed)
5. Expected savings per doc task: ~10–12k tokens

**Reference:** `.claude/agents/doc-writer.md` includes detailed pattern examples.

### Speed 1 with Copilot

Attach all relevant files explicitly in the Copilot sidebar. Keep edits surgical — modify one function or method at a time, not entire files.

Reference `.github/copilot-instructions.md` for project-specific context (tenant isolation, no exploration, no hallucinations).

Copilot has no Phase 2 orchestration equivalent — no agents, no delegations, no hand-off docs. For complex features requiring planning or cross-domain coordination, switch to Speed 2 (CLI mode).

---

## Context Management

Context compression prevents token multiplication when parallel agent waves share a large planning context (80k × 3 agents = 240k wasted tokens).

### Automated Hook: `auto-compress.sh`

Registered in `.claude/settings.json`. Fires advisory warnings — never blocks session flow.

| Trigger | Hook Event | Condition | Advisory |
|---|---|---|---|
| Tool-call threshold | `PostToolUse` (all tools) | count ≥ `COMPRESS_THRESHOLD` (default: 12) | Run `/clear` |
| Sub-agent spawn | `PreToolUse` (Agent) | context count ≥ 5 tool calls | Check if ≥2 agents → clear first |
| Parallel results received | `SubagentStop` (all) | ≥2 sub-agents completed | Clear before next wave |
| Phase Gate keyword | `UserPromptSubmit` | prompt matches `phase gate` / `proceed to phase` | Complete all gate steps |

### Configuration

```bash
# Override compression threshold (default: 12 tool calls)
export COMPRESS_THRESHOLD=8
```

### Manual Fallback

```bash
# Clear session to free context window before next wave
/clear
```

### Example Hook Warning Output

```
<system_warning>Tool-call count has reached 12 (threshold: 12).
Run /clear before spawning parallel agents to avoid 120k+ token waste.
(auto-compress.sh)</system_warning>
```

### Copilot Compatibility

Not applicable. Copilot Chat is stateless per conversation — no compression mechanism exists or is needed.
