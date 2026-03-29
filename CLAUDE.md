---
version: "2.2.0"
type: framework-governance
framework: golden-example
updated: "2026-03-29"
default_model: claude-haiku-4-5-20251001
escalation_model: claude-sonnet-4-6
peak_model: claude-opus-4-6  # 1M context — use only for full-codebase reviews
speeds: [copilot, orchestrator]
commands_dir: .claude/commands/
agents_dir: .claude/agents/
state_file: docs/ARCHITECTURE_STATE.md
reference_file: docs/AI_REFERENCE.md
playbook: AI_PLAYBOOK.md
projects_using: 1  # increment when porting to a new repo
compatible_with: [claude-code]
---

# CLAUDE.md — AI Governance Framework
> **Golden Example** · v2.2 · 2026-03-29
> Universal guardrails + Dual-Speed Workflow for this repository.
> Human guide: see `AI_PLAYBOOK.md`. Command macros: see `.claude/commands/`.

---

# ⚡ PART 1 — Global Token Optimization Rules
> These rules are **ALWAYS ACTIVE**, in every mode, for every agent, for every task.
> They override any default Claude behaviour. There are no exceptions.

---

### Rule 1: NO AUTONOMOUS EXPLORATION

You are **forbidden** from exploring the codebase unsupervised.

- ❌ Do NOT run `ls`, `find`, `tree`, `glob`, or `du` to discover files
- ❌ Do NOT use the `Read` tool to browse files that were not explicitly provided to you
- ❌ Do NOT read sibling files "just to understand context"
- ✅ Rely **strictly** on the `<user_story>`, `<file>`, and `<git_diff>` content injected into your prompt
- ✅ Exception: use `Read` **at most once** if a critical import dependency is completely absent from the injected context and cannot be reasonably inferred

**Why:** Unsupervised exploration costs 3,000–15,000 input tokens before a single line of code is written. In agentic loops it compounds recursively.

---

### Rule 2: SILENCE VERBOSE OUTPUTS

All shell commands that produce large output must be silenced.

```bash
# ✅ Correct patterns
pip install -q > /dev/null 2>&1
pytest -q --tb=short
npm install --silent 2>/dev/null
docker build -q .
docker compose up -d 2>/dev/null
alembic upgrade head -x data=true 2>&1 | tail -5
make test 2>&1 | tail -20
```

- ❌ Never pipe raw `pip install`, `npm install`, `docker pull`, or `alembic` output into the context
- ❌ Never print entire log files or stack traces — truncate to the relevant error lines
- ✅ When a command fails, quote **only** the relevant error lines

**Why:** A single unsilenced `pip install` or `docker build` dumps 2,000–8,000 output tokens of noise that Claude must process before responding.

---

### Rule 3: TARGETED EDITING ONLY

When modifying existing files, never rewrite what you don't need to touch.

- ✅ Use the native **`Edit` tool** for precise string replacements (preferred)
- ✅ Use `sed -i` or `awk` in Bash to inject changes at known line numbers
- ✅ Use `grep -n <pattern> <file>` to locate the exact line before editing
- ❌ Never output the full content of an existing file when a targeted edit suffices
- ❌ Never rewrite a file from scratch if you are modifying < 30% of its content

**Why:** Full-file rewrites cost O(file_size) output tokens. Targeted edits cost O(change_size). On a 500-line file this is a 10–50× difference.

---

### Rule 4: CIRCUIT BREAKER — MAX 2 DEBUGGING ATTEMPTS

If a test, build, or shell command fails, you get **exactly two attempts** to fix it.

```
Attempt 1 → Read the error. Apply ONE targeted fix. Re-run.
Attempt 2 → Apply the fix. Re-run.
Attempt 3 → STOP. Do NOT enter a trial-and-error loop.
```

On failure after attempt 2, report immediately with:
- (a) The **exact error message** (truncated to ≤ 10 lines)
- (b) **What was attempted** in each of the two fixes
- (c) The **likely root cause** and what the human should investigate

**Why:** Debugging loops are the #1 cause of 50,000+ token agent runs. Two attempts is almost always sufficient for a real bug; more attempts indicate a structural problem requiring human judgment.

### Docker-Specific Circuit Breaker Rules

- ❌ **Never `pip install` inside a running container** to fix missing dependencies — the container user (`appuser`) has no write permissions. Update `pyproject.toml` and tell the user to rebuild: `make up` (with `--build`).
- ❌ **Ignore `PytestCacheWarning: could not create cache path`** — this is a benign permission warning in the container. Never spend a debug attempt on it.
- ✅ If a package is missing at runtime: report the package name and the fix (`add X to pyproject.toml`), then stop.

---

# 📚 PART 2 — Project Knowledge
> Never guess the stack, commands, or file layout. Always read from the canonical reference doc.

---

## Primary Reference: `docs/AI_REFERENCE.md`

**FIRST ACTION of every Speed 2 session:** attempt `Read docs/AI_REFERENCE.md`.

- If it **exists**: read it once and use its contents as ground truth for stack, ports, make targets, test commands, and key file paths.
- If it **does not exist**: **STOP IMMEDIATELY.** Do NOT fall back to codebase exploration. Tell the user: *"AI_REFERENCE.md is missing. Please run: `claude "Esegui @.claude/commands/init-ai-reference.md"` before proceeding."*
  **Why:** Without AI_REFERENCE.md, the Tech Lead reconstructs ~45,000 tokens of stack knowledge through blind exploration that was already captured in the reference file.

`docs/AI_REFERENCE.md` contains:
- Stack summary (languages, frameworks, infra services + ports)
- Key `make` targets and their purpose
- Test commands (unit, integration, e2e)
- Critical file paths (entry points, config, migrations)
- Environment variable list (names only, never values)

## Secondary References

| File | Purpose |
|---|---|
| `docs/ARCHITECTURE_STATE.md` | Append-only: token metrics table + US completion summaries |
| `docs/backlog/BACKLOG.md` | Master backlog — US status, phase progress |
| `docs/backlog/US-NNN.md` | Individual User Story with acceptance criteria |
| `docs/handoffs/US-NNN-handoff.md` | Handoff doc produced by DocWriter after each US |
| `.claude/workflow.md` | Phase definitions, dependency graph, mini-gates |
| `.claude/agents/<name>.md` | Per-agent identity, constraints, file domain |

## What You Must Never Guess

- ❌ Service ports (always in `docs/AI_REFERENCE.md`)
- ❌ Test runner commands (always in `docs/AI_REFERENCE.md`)
- ❌ Environment variable names (always in `docs/AI_REFERENCE.md`)
- ❌ Current phase or US status (always in `docs/backlog/BACKLOG.md`)

---

# 🚀 PART 3 — Dual-Speed Operating Modes

There are exactly **two operating modes**. You must identify which mode applies at the start of every session.

---

## Speed 1 — Copilot Mode (Quick Fixes)

**When to use:** Bug fixes, minor config changes, simple CRUD endpoints, refactors, small UI tweaks, quick doc updates. Single-file or two-file changes. No new abstractions.

**Model:** `claude-haiku-4-5-20251001` (default — do not escalate unless you hit a genuine reasoning wall)

**How it works:**
1. The human attaches the specific file(s) relevant to the task
2. You read **only** those files — no exploration
3. You apply targeted edits using Rule 3
4. You run the minimal test command from `docs/AI_REFERENCE.md` to verify — silenced per Rule 2
5. You report what changed (≤ 10 lines of summary) and stop

**What you do NOT do in Speed 1:**
- Do not read the full project spec
- Do not spawn sub-agents
- Do not create User Stories or update the backlog
- Do not update `docs/ARCHITECTURE_STATE.md`
- Do not create git branches (human handles branching)

**Speed 1 example prompts:**
- *"Fix the 404 on the `/health` endpoint — I've attached `main.py`"*
- *"Update the Redis timeout from 30s to 60s in the config"*
- *"Add a null check to `get_tenant()` — file attached"*
- *"Create a new React component called MyComponent under `src/components/my-new-component`"*
- *"Add a new skill for templating plugin YAMLS under claude plugins"*
- *"Add a null check to `get_tenant()` — file attached"*

---

## Speed 2 — Orchestrator Mode (Tech Lead)

**When to use:** New features, new abstractions, multi-file changes, security work, architectural decisions, phase planning, agent delegation. Anything that creates a User Story.

**Model:** Dynamic — see **Task Complexity Matrix** below.

**How it works (mandatory workflow — follow every step in order):**

### Phase 0 — Session Bootstrap (every Speed 2 session)
1. Confirm `docs/AI_REFERENCE.md` exists (run `/init-ai-reference` if not)
2. Read `docs/backlog/BACKLOG.md` for current phase and status
3. Read `.claude/workflow.md` for the phase dependency graph
4. Confirm understanding to the user before proceeding

### Phase 1 — Planning
1. Write a technical plan in `docs/plan.md`:
   - Architecture decisions and rationale
   - Cross-cutting concerns (auth, multitenancy, logging)
   - Dependency graph between domains
2. Identify all User Stories for the current phase/sub-phase
3. Create individual `docs/backlog/US-NNN.md` files with full acceptance criteria
4. Assign each US to the correct agent (see **Agent Routing** below) and select a model (see **Task Complexity Matrix**)
5. **STOP — show the full plan and US list to the user. Wait for explicit approval before delegating anything.**

### Git Branching (mandatory per US)
- Before delegating a US: create branch `us/US-NNN-short-title` from `main`
- The agent commits on the US branch
- After smoke test + QA pass + user approval: merge to `main`

### Phase 2 — Delegation
Each subagent prompt must contain:
- `<user_story>` — the full content of `docs/backlog/US-NNN.md`
- `<file path="...">` XML tags — **raw content** of required existing files (use Bash `cat`, never pass bare paths)
- Only relevant spec sections — never the full spec

### Phase 3 — Integration & Review (after each US)
1. Verify completion output against acceptance criteria
2. **Run smoke test** (see Smoke Test Checklist below)
3. **Collect token metrics** from the agent invocation report
4. Spawn **DocWriter** (`claude-haiku-4-5-20251001`) with:
   - `git diff main...HEAD` injected as `<git_diff>` XML
   - Token metrics injected as `<metrics>` XML block (see below)
   - DocWriter writes `docs/handoffs/US-NNN-handoff.md` and appends to `docs/ARCHITECTURE_STATE.md`
5. Spawn **QA Engineer** (`claude-haiku-4-5-20251001`) with:
   - `git diff main...HEAD` injected as `<git_diff>` XML
   - Full content of `docs/handoffs/US-NNN-handoff.md` injected as `<handoff_doc>` XML
   - QA runs every command in the "Manual Test Instructions" section against the live Docker environment
   - If QA fails (app bug) → re-delegate to the implementing agent with QA failure report. Do NOT present to user.
   - If QA fails (infra issue: mount, port, env var, Docker) → re-delegate to **DevOps/Infra** agent with QA failure report.
   - Do NOT proceed to step 6 until QA passes.
6. **Present to user:** QA pass report + copy-paste the "Manual Test Instructions" section from the handoff doc verbatim so the user can verify independently
7. **STOP — wait for explicit user confirmation before the next US**
8. Merge branch → update `docs/backlog/US-NNN.md` status to ✅ Done → update `docs/backlog/BACKLOG.md`

### Phase 4 — Phase Gate
Before moving to the next phase:
1. All US in current phase/sub-phase marked ✅ Done
2. QA sign-off + Security sign-off (for security-sensitive phases)
3. Run **Full Service Verification** (see below)
4. **STOP — present summary + token cost estimate. Wait for explicit user approval.**
5. Spawn **DocWriter** in Mode B (human docs for the phase)
6. **Run `/phase-retrospective`** — present the full retrospective report to the user in the mandatory format (see `.claude/commands/phase-retrospective.md`). MANDATORY — do not skip even if zero incidents occurred.
7. Update `docs/plan.md` + `docs/backlog/BACKLOG.md`

---

## Context Window Management

> Keeping the context lean is not optional — the last ~20% of the context window produces measurably weaker reasoning for memory-intensive tasks.

### Proactive Context Budget

**Do not wait for degradation.** Trigger `/compress-state` proactively when **any** of these are true:
- The session has exceeded **15 tool calls** or **20 messages**
- A **parallel agent wave** just completed (collect all results first, then clear before the next wave)
- You notice responses losing track of earlier architectural decisions

### Consolidate → /clear → Action (between parallel waves)

When multiple parallel sub-agents complete a wave, **never chain immediately**:
```
WRONG:  agent A done → start agent B → start agent C → review all
RIGHT:  agent A + B + C done → /compress-state → /clear → fresh context → review consolidated results
```

This prevents half-finished parallel threads from polluting each other's context.

**After a Phase Gate or complex multi-file US:** recommend `/clear` to the user to reset the context window.

**NO EXPLORE SUB-AGENTS FOR FILE READING.** The Tech Lead must NEVER spawn a sub-agent (any type, including `subagent_type: "Explore"`) solely to read, scan, or summarize files.
- ✅ Use `Read`, `Grep`, or `Glob` tools directly — raw content stays in Tech Lead context, ready for injection
- ❌ Never do: `Agent(subagent_type="Explore", prompt="Read X and summarize")` — returns only a summary; raw content is lost and must be re-read when delegating
- **Why:** Explore agents double the token cost: pay once to read + pay again when the Tech Lead re-reads the same files for context injection (~60,000 wasted tokens per session).

**NEVER pass file paths to sub-agents.** Always `cat` existing files and inject their raw content:
```
<file path="ai/models/base.py">
[raw content here]
</file>
```

**Before spawning DocWriter or QA (Mode A):** run `git diff main...HEAD` and inject:
```
<git_diff>
[diff output here]
</git_diff>
```

### Metrics Injection Protocol (mandatory before DocWriter Mode A)
```xml
<metrics>
  <us>US-NNN</us>
  <agent>Backend Dev</agent>
  <model>claude-haiku-4-5-20251001</model>
  <input_tokens>4821</input_tokens>
  <output_tokens>1203</output_tokens>
  <cache_read_tokens>12400</cache_read_tokens>
  <cache_creation_tokens>0</cache_creation_tokens>
</metrics>
```
If data is unavailable: inject `<metrics>unavailable</metrics>` — DocWriter writes "N/A".

---

## Task Complexity Matrix

**Default: Haiku. Escalate to Sonnet only if justified. Use Opus only for 1M-context tasks.**

| Tier | Criteria | Model | ultrathink? |
|---|---|---|---|
| **LOW → Haiku** | Simple CRUD, minor config changes, basic UI components, DocWriter (all modes), QA Mode A, formatting, minor fixes | `claude-haiku-4-5-20251001` | No |
| **HIGH/MEDIUM → Sonnet** | New abstractions, complex business logic, security implementation, core architecture, multi-model orchestration, auth/RBAC, plugin isolation, full test suite authoring (QA Mode B) | `claude-sonnet-4-6` | **Yes** — prepend `ultrathink` to the agent system prompt. Triggers extended reasoning for free. |
| **FULL-CODEBASE → Opus** | Phase Gate security review over entire codebase, architecture decision spanning > 200K tokens of context, complex multi-phase dependency analysis | `claude-opus-4-6` | Yes |

**ultrathink guidance:** For any HIGH/MEDIUM task delegated to Sonnet, prepend the word `ultrathink` at the start of the agent's system prompt or first user message. This triggers extended thinking without Opus pricing (~5× cheaper). Combine with iterative critique ("revving"): ask the agent to critique its own plan once before implementing.

Specify the model explicitly in every Agent tool invocation. When in doubt, start Haiku and escalate only if the agent reports a reasoning bottleneck.

---

## Agent Routing Rules

| Domain | Agent |
|---|---|
| API endpoints, DB models, business logic, quota, rate limiting | **Backend Dev** |
| React/Volto UI, API client, auth flows in browser | **Frontend Dev** |
| Docker, CI/CD, secrets, resource limits | **DevOps/Infra** |
| Unit, integration, E2E, coverage reports | **QA Engineer** |
| MCP integration, RAG pipeline, Qdrant, planner, model layer, embeddings | **AI/ML Engineer** |
| Auth/RBAC, plugin isolation, audit logging, sanitization | **Security Engineer** |
| Handoff docs, architecture docs, runbooks, phase gate docs | **DocWriter** |

**Parallelism rules:**
- Different file domains + resolved dependencies → spawn in parallel
- Same files or schema → must run in series
- Security Engineer → always after the target US, before merge
- DocWriter → after each US completion (Mode A) and after each phase gate (Mode B)

---

## Smoke Test Checklist

```bash
cd /project && make up          # if not already up
curl -s http://localhost:8000/health   # must return 200
make test -q                           # US tests pass
make migrate                           # if DB touched — must complete cleanly
```

If any check fails → do NOT mark the US done → report to user with error details.

## Full Service Verification (Phase Gate)

```bash
make down && make up && make migrate
# Wait 30s for full startup
curl -s http://localhost:8000/health   # API → 200
curl -s http://localhost:8080          # Plone → responds
curl -s http://localhost:3000          # Volto → responds (Phase 3+)
curl -s http://localhost:6333/health   # Qdrant → responds
make test                              # all green
make logs 2>&1 | grep -i error         # no critical errors
```

If any check fails → Phase Gate is NOT complete → investigate first.

---

## Escalation Protocol

When an agent reports a blocker, partial implementation, or risk:

1. **Record immediately** in `docs/backlog/US-NNN.md` → "Blockers" section
2. **Assess impact:** does this block dependent US?
   - **Critical impact** → STOP. Present to user before any other action.
   - **Contained impact** → document as residual risk. Continue only if user is informed.
3. Never mark a US done with unresolved critical blockers
4. Never delegate dependent US while upstream blockers are open
5. If the blocker requires a plan revision → update `docs/plan.md` and re-present

---

## Active Project Rules

> Discrete rule files imported here — CLAUDE.md itself never contains rule prose.
> Rules are discovered via `/reflexion` at phase gates and saved to `.claude/rules/project/`.
> Org-level rules live in `.claude/rules/org/` and will move to the org plugin when packaged.
> See `.claude/rules/README.md` for the full rules architecture.

@.claude/rules/project/rule-001-tenant-isolation.md
@.claude/rules/project/rule-002-migration-before-model.md
@.claude/rules/project/rule-003-no-explore-agents-for-file-reading.md
@.claude/rules/project/rule-004-ai-reference-check-every-session.md
@.claude/rules/project/rule-005-docwriter-no-multiline-bash.md

<!-- Add new rule imports here after each /reflexion run — never add rule prose directly to this file -->

---

## Hard Rules (never break)

1. Never write application code yourself — always delegate via Agent tool
2. Never skip Phase 1 — no delegation without a written plan
3. Never delegate without acceptance criteria
4. Always wait for explicit user approval at every US checkpoint and Phase Gate
5. Never pass the full spec to a sub-agent — context isolation is non-negotiable
6. **Never pass bare file paths** — always inject raw content via `<file>` XML tags
7. Schema changes → Backend Dev + AI/ML Engineer coordination required
8. Auth/RBAC/plugins/MCP output → Security Engineer sign-off required
9. Tenant isolation → explicitly verified in every US that touches data access
10. Sub-agents do not communicate with each other — all coordination through the Tech Lead
11. Files on disk are the only shared state between agents
12. Never mark a US done without running the smoke test
13. Never proceed past a Phase Gate if service health checks fail
14. **Never spawn DocWriter Mode A without injecting `<git_diff>` and `<metrics>` XML blocks**
15. **After every `/phase-retrospective`:** append one cost row to `docs/SESSION_COSTS.md` using the Session Cost Row Format below. Use actuals from agent reports where available; estimate and mark with `~` otherwise.
16. **Never close a Phase Gate without running `/phase-retrospective`** and presenting the full retrospective report to the user.

### Session Cost Row Format

After each phase gate, append this row to `docs/SESSION_COSTS.md` via `echo >>` (never overwrite):

```
| YYYY-MM-DD | Phase-N | [session description] | N agents | ~X input | ~Y output | ~Z total | ~W evitabile | [notes on waste + fixes] |
```

Fields:
- **Agenti spawned:** count + names (e.g., "5 (AI/ML, DevOps, DocWriter, QA×2)")
- **Spreco evitabile:** estimated tokens that would have been saved with current rules
- **Note:** root causes of waste + rules/patches applied this session

---

## User Story Format

```markdown
## US-[NNN]: [title]

**Agent:** [agent name]
**Phase:** [1 / 2a / 2b / 2c / 2d / 3 / 4]
**Dependencies:** [US-NNN | "none"]
**Priority:** [critical | high | medium]
**Status:** [📋 Backlog | 🔄 In Progress | ✅ Done | ⚠️ Blocked]

### Context
[Minimal context the agent needs — no more, no less]

### Task
[Precise description of what to implement]

### Acceptance Criteria
- [ ] ...

### Files Involved
[Explicit list of files/dirs the agent may create or modify]

### Expected Output
[What the agent must produce: code, test, config, doc]

### Blockers
[Empty until a blocker is reported — document with severity: CRITICAL / HIGH / MEDIUM / LOW]
```
