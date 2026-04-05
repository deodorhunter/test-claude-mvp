← [Back to DEVLOG index](../DEVLOG.md)

## Entry 19 — Post-Restart MCP Enforcement Tests: What Passed, What Didn't, and Two Surprises — 2026-04-04

> We spent a session fixing agent frontmatter governance (allowed_tools → tools, PascalCase, case-sensitive disallowedTools). After restart, we ran six targeted tests to verify the fixes held. Three passed cleanly. Two failed for a reason nobody predicted. One was inconclusive in an instructive way.

---

### What was being tested

The previous session (also 2026-04-04) audited all 11 agent definition files and found three categories of silent failure:

1. `allowed_tools` is not a Claude Code field — `tools` is the correct allowlist key. Agents had been running with no tool restrictions at all.
2. `disallowedTools` entries were lowercase (`bash`, `edit`) — Claude Code's enforcement is case-sensitive. `Bash` blocks; `bash` does not.
3. `.mcp.json` had not been created at project level, so context7 and Serena were only registered in the personal `~/.claude.json`, not in project agent sessions.

After applying the fixes, Claude Code was restarted to reload agent definitions. Six tests were designed to probe each fix.

---

### Test results

**Test 1 — critic cannot run Bash** ✅ PASS

The critic agent refused to run `echo "governance-test-1"` via Bash. Zero tool uses. It cited role constraints ("falls outside the critic role") rather than an explicit block message. The underlying cause is ambiguous: `tools: Read` may have prevented the tool from appearing in its context, or the system prompt instruction alone was sufficient. Either way, Bash was not executed. For governance purposes, the outcome is correct.

**Test 2 — qa-engineer cannot use Edit** ⚠️ INCONCLUSIVE

The qa-engineer used the Read tool (5 tool uses, confirming Read is accessible), then declined to attempt Edit, reasoning that a no-op replacement is untestable without making a real change. This is a test design flaw, not a governance failure. The agent clearly had Read access. Whether Edit is blocked by `disallowedTools: Edit` remains unverified. A future test should ask for a small, revertible change to a scratch file.

**Test 3 — critic cannot call Serena** ✅ PASS

The critic agent received "No such tool available: mcp__serena__get_symbols_overview" when attempting to call Serena. This is the correct outcome — but for an unexpected reason (see surprise #1 below).

**Test 4 — aiml-engineer can call Serena** ❌ FAIL

Agent never launched. Error: "There's an issue with the selected model (dynamic). It may not exist or you may not have access to it." The aiml-engineer definition has `model: dynamic`, which is not a recognized Claude Code model identifier. The agent frontmatter governance fix corrected `allowed_tools` → `tools` but left `model: dynamic` intact.

**Test 5 — devops-infra cannot call Serena** ❌ FAIL

Same failure mode as test 4. dev-ops.md also has `model: dynamic`. The agent never launched, so the Serena block could not be verified.

**Test 6 — context7 resolves library names** ✅ PASS

`mcp__context7__resolve-library-id("fastapi")` returned five matching libraries including `/fastapi/fastapi` (High reputation, 1075 snippets, benchmark 84.62). context7 is working from the main session after `.mcp.json` was created at project level.

---

### Surprise 1: Serena is not reachable from sub-agents at all

Tests 3, 4, and 5 were designed to distinguish between agents that *should* have Serena access and agents that *shouldn't*. The distinction turned out to be moot: Serena is unavailable in all sub-agent sessions, regardless of what `tools` declares.

The critic (test 3) got "No such tool available" — which looks like a `tools` enforcement pass. But aiml-engineer would have received the same error if it had launched (test 4 was supposed to show Serena *working*). The block is infrastructure-level, not governance-level: sub-agents spawned via the Agent tool do not inherit the MCP server connections from the parent session.

This has a significant implication. Serena-first navigation (rule-009) is only enforced in the main session. Any sub-agent that needs Serena for semantic navigation must either have Serena registered in its own MCP config, or the orchestrator must inject file content via `<file>` XML tags rather than delegating navigation to the sub-agent.

**Practical consequence:** The current `tools: Bash, Read, Edit, Write, mcp__serena, mcp__context7` declarations in agent frontmatter are aspirational, not functional. They describe intended access, not actual access. The gap between "declared in tools" and "available in session" needs to be closed before Serena can be relied on in delegated agents.

**Surprise 2: `model: dynamic` breaks agent spawning**

Seven of twelve agent definitions have `model: dynamic` in their frontmatter. This value is not recognized by Claude Code. The agents fail silently at spawn time with a model error, before any tool or instruction processing occurs.

The agents affected: backend-dev, aiml-engineer, security-engineer, frontend-dev, dev-ops, debugger (has haiku), and TEMPLATE. Of these, aiml-engineer and dev-ops were part of the governance test suite.

The fix is mechanical: replace `model: dynamic` with an explicit model ID (`claude-haiku-4-5-20251001` for most specialist agents, `claude-sonnet-4-6` for orchestrator-level work). This was not part of the previous session's frontmatter audit because the focus was on `tools`/`disallowedTools` schema correctness, not model field validity.

---

### What this session established

1. `tools: Read` on the critic agent correctly restricts Bash (test 1 — directional confirmation).
2. context7 MCP is operational at project level after `.mcp.json` creation (test 6 — clean pass).
3. Serena MCP is not reachable in sub-agent sessions regardless of `tools` declarations.
4. `model: dynamic` is an invalid identifier that silently kills agent spawning.
5. Test design matters: a no-op Edit test cannot distinguish "blocked" from "refused on principle."

**Next actions required:**
- Replace `model: dynamic` with explicit model IDs in all 7 affected agent files.
- Investigate whether Serena can be made available in sub-agent sessions via `.mcp.json` project-level registration or an alternative transport.
- Retest qa-engineer Edit block with a real scratch-file change.
- Retest aiml-engineer/devops-infra Serena access once model field is fixed.
