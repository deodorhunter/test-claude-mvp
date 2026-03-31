# Copilot vs Claude Code — What Doesn't Translate

> Read this before expecting feature parity between the two setups.

---

## What works in both

| Capability | Copilot | Claude Code |
|---|---|---|
| Speed 1 targeted fixes | ✅ Native | ✅ Native |
| Token anti-patterns (no exploration, silence outputs, circuit breaker) | ✅ Via instructions | ✅ Via CLAUDE.md |
| Path-scoped rules (backend, tests, MCP) | ✅ Via `applyTo` in `.github/instructions/` | ✅ Via `paths:` in rule frontmatter |
| Reusable prompts / commands | ✅ Via `.github/prompts/` | ✅ Via `.claude/commands/` |
| Tenant isolation, migration order, MCP trust | ✅ Via instructions | ✅ Via rules |
| **Serena LSP navigation** | ✅ Via `.vscode/mcp.json` + `serena-navigation.instructions.md` | ✅ Via `claude mcp add` + rule-009 |
| **Context7 library docs** | ✅ Via `.vscode/mcp.json` | ✅ Via `claude mcp add` |

---

## What only works in Claude Code

### Pre-flight hooks
Claude Code runs `.claude/hooks/pre-prompt.sh` before every session. It checks for `AI_REFERENCE.md`, git bloat, and forbidden tool installs. Copilot has no hook mechanism — these checks are manual pre-conditions.

**What to do in Copilot:** Before starting any non-trivial session, manually verify:
- `docs/AI_REFERENCE.md` exists and is current
- No uncommitted files from a previous session that shouldn't be there

### Sub-agent orchestration (Speed 2)
Claude Code can spawn specialized sub-agents (backend dev, security engineer, QA) with scoped permissions and different models per role. Copilot Chat is a single-agent surface — the user acts as the orchestrator themselves.

**What to do in Copilot:** For multi-step features, decompose the work manually into the same specialist roles, run each as a separate scoped conversation, and attach only the relevant files for each role.

#### Why Copilot Chat agents don't solve this
GitHub added agent support to Copilot Chat (late 2024), but Copilot agents are **tool-wrapping personas**, not governance systems. Key limitations:

| Requirement | Claude Code | Copilot Chat agents |
|---|---|---|
| Enforce tool restrictions per agent (e.g., backend-dev cannot touch `backend/app/auth/`) | ✅ Executable: agent receives scoped tool list | ❌ Personas only — no `allowed_tools` enforcement |
| Parallel multi-agent coordination with context clearing | ✅ Orchestrator manages waves + `/compress-state` | ❌ Single chat surface — no wave coordination |
| Prevent agent self-approval + enforcement chain (implement → judge → QA) | ✅ Orchestrator routes; hard gates | ❌ Agent can approve own work — no checkpoints |
| Hard-coded constraints in agent prompt (tenant isolation, circuit breaker) | ✅ Non-negotiable per agent | ❌ Soft guidance — agent can override |

Copilot Chat agents are useful as **UI personas** (e.g., "Ask the Backend Developer") but cannot replace the governance model this framework requires for Speed 2 workflows.

### Serena LSP integration
Claude Code uses `serena__get_symbols_overview` and `serena__find_symbol` to navigate code at ~200 tokens per file rather than full reads. **Copilot now has this too** — Serena is configured in `.vscode/mcp.json` and `serena-navigation.instructions.md` activates the same navigation behaviour for Copilot. See `.vscode/mcp.json` and [`.github/instructions/serena-navigation.instructions.md`](.github/instructions/serena-navigation.instructions.md).

### Persistent session state / compress-state
The `/compress-state` command writes a structured snapshot and clears the context window. Copilot's equivalent (`compress-state.prompt.md`) captures the snapshot but context clearing is manual.

### Phase gates
The formal phase gate workflow — full service verification, DocWriter Mode B, retrospective, cost tracking — has no Copilot equivalent. These are Speed 2 processes requiring orchestrator automation.

---

## Principle: same governance, different automation level

Both setups enforce the same core principles: no autonomous exploration, targeted editing, circuit breaker, tenant isolation, EU data boundary. The difference is automation — Claude Code automates the orchestration; Copilot requires the developer to apply the same discipline manually.

The `.github/` setup is not a "Copilot version" of the framework — it's the same framework expressed as guidance for a different tool surface.
