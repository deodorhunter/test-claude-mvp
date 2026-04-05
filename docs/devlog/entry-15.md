← [Back to DEVLOG index](../DEVLOG.md)

## Entry 15 — The Orchestrator Is Not Exempt

*(Phase 3c retrospective — 2026-04-03)*

Entries 13 and 14 documented how agents exhibit scope creep and gate-skip behaviour. Entry 15 completes the picture: **the orchestrator itself is subject to the same failure modes it is supposed to prevent.**

Phase 3c produced three incidents, all in the same session:

1. **DocWriter sub-agent blocked** — spawned without file content pre-injected. The agent immediately hit a Read permission denial and stalled. The orchestrator knows Rule 003 (no autonomous file reads) — but failed to apply the corollary: if an agent cannot explore, the orchestrator must provide the content explicitly before spawning.

2. **DevOps sub-agent failed to spawn** — delegated with `model: dynamic`. The agent runtime rejected it: model not found. The Task Complexity Matrix specifies Haiku for LOW tasks. The orchestrator knows this. But the delegation prompt left the model unresolved, trusting runtime inference that doesn't exist.

3. **Phase 3c Gate presented as optional** — after all US completed, the orchestrator presented a choice: "Close Phase 3 OR run Phase 3c Gate." Rule-020 was extracted precisely to prevent this pattern (Phase 3b incident). The rule fired one phase later.

All three failures are **implicit assumption failures**: the orchestrator assumed the agent could read its own files, assumed the runtime would resolve the model, assumed the user wanted a choice when no choice exists. The framework's core principle is that explicit constraints beat implicit assumptions — for agents and for the orchestrator equally.

#### What Was Fixed

Two targeted changes applied at the Phase 3c gate:

**1. Orchestrator delegation checklist updated (`orchestrator.md`):**
- DocWriter agents: raw file content MUST be pre-injected via `<file>` XML (permission denied otherwise)
- Model assignment: NEVER leave as `dynamic` — resolve at delegation time, state explicitly in prompt

These are now in the "Each sub-agent prompt MUST include" block — the same section that governs `<user_story>` and ASYNC CONTEXT MUZZLING.

**2. Seven rule files patched (`rule-003` through `rule-018`):**
The verify-docs script checks for `<constraint>`, `<why>`, and `<pattern>` sections in every rule file. Seven compact rules were missing `<pattern>` — added minimal ✅/❌ examples to each. Not a framework change, just consistency enforcement.

#### The Recursion Problem

There is a structural tension in this framework that Phase 3c makes explicit: **the orchestrator writes and enforces its own rules**. When the orchestrator violates a rule it extracted from its own past violations, no automated system catches it — the user does.

The detection layers (Judge, Critic, /consistency-check) operate on *output* quality, not on *orchestrator behaviour*. A judge checks whether an agent's code satisfies acceptance criteria. Nothing checks whether the orchestrator followed its own delegation protocol.

This is not necessarily a bug. Human oversight is an explicit design choice (EU AI Act Art. 14). But it means the framework's robustness depends on the user's willingness to call out violations — which this user did, twice in this session.

The open question for Phase 4: can orchestrator compliance checks be automated without adding cost that exceeds the violations they prevent?

#### Benchmark Note (Resolved — Phase 3d/3e)

**Closed 2026-04-03.** The benchmark re-run happened in Phase 3d: `make benchmark-session` against the live session JSONL produced the first real cost measurement. Result: $11.41 actual vs ~$78 implied by token estimates — a 7× gap caused by cache read tokens (10× cheaper than raw input). Framework v3.0 with rule-020, auto-compress hook, and symbol-context guidance active throughout. Cache read ratio: 91% (Phase 3d) → 100% (Phase 3e). See Entry 18 for full analysis.

#### Orchestrator Compliance Automation (Open Question Update — Phase 3e)

The Phase 3e gate produced one incident: a Doc Writer agent reported done on US-071 without verifying the numeric AC (`≤6,000 bytes`). The judge caught it. The fix was 3 targeted edits by the Tech Lead.

This is the same class of failure described in Entry 15 — implicit assumption (the agent assumed the byte count was close enough without measuring). The detection layer (Judge) worked correctly. The human caught it and fixed it without re-delegation.

The question of whether orchestrator compliance checks can be automated without exceeding the cost of violations they prevent: Phase 3e provides one data point. The violation cost ~3k tokens; a preventive rule loaded every session would cost ~200 tokens × all sessions ≥ 15 sessions to break even. The rule was discarded at the Phase 3e reflexion gate. The Judge system remains the correct intervention point — not always-loaded rules.

Verdict for Phase 4: no automation needed at this class of violation rate. Revisit if the pattern recurs ≥3 times in Phase 4.

**Fix applied (Phase 3e gate):** Added constraint 7 to `.claude/agents/doc-writer.md` — when the delegation prompt specifies a `≤N bytes` or `≤N lines` AC, the agent must run `wc -c`/`wc -l` and confirm the result before reporting done. The cost is zero (it's in the agent's system prompt, not a loaded rule) and the benefit is eliminating the judge→fix→re-judge loop for this class of AC.

#### Phase Boundary Session Management (Applied — Phase 3e Gate)

A second improvement came from the benchmark data: this session's JSONL spans both Phase 3d and Phase 3e, making the cost of each phase indistinguishable from the cumulative total. The Phase 3d measurement ($11.41) and the Phase 3e delta ($7.17) had to be hand-subtracted.

**Fix applied:** Added step 6 to the Phase Gate workflow in `.claude/skills/speed2-workflow.md` — after gate approval, run `/clear` to start the next phase as a new session. Each phase now has its own JSONL for clean per-phase cost attribution via `make benchmark-session`. No ambiguity, no subtraction arithmetic.

---

#### Governance Enforcement Tests — 2026-04-04 (Same Failure Class, Confirmed Again)

A session of targeted governance tests confirmed entry-15's thesis from a different angle: not just that the orchestrator makes implicit assumptions, but that those assumptions are **structurally invisible** until you try to spawn an agent in isolation.

**`model: dynamic` breaks non-orchestrated spawning.** Seven agent files had this value. In Speed 2 the orchestrator always passes an explicit model override — so the frontmatter value was never exercised and the failure was invisible. The moment a test tried to spawn an agent directly (without Speed 2 orchestration), it failed silently at the model lookup step. The fix: typed fallback defaults in every agent file. Speed 2 orchestrators still override per Task Complexity Matrix; the fallback is only ever exercised for ad-hoc or Speed 1 use.

This is exactly the DevOps incident from Phase 3c described above — `model: dynamic` rejected at runtime — now reproduced as a systematic test and fixed at the source (frontmatter) rather than only at the orchestrator delegation layer. The root cause in Phase 3c was: "orchestrator left the model unresolved." The root cause in the 2026-04-04 audit: "no one ever tested what happens when the orchestrator isn't present."

**Serena is not available in sub-agents.** MCP server descriptions are injected into sub-agent system prompts, but the tool RPC bridge is not passed to Agent-spawned sessions. Confirmed via test 4: aiml-engineer received Serena instructions in its system-reminder but returned "No such tool available" when calling `mcp__serena__get_symbols_overview`. This is a Claude Code limitation, not a config error.

The governance fix (rule-010) makes the orchestrator the Serena proxy: before delegating any US touching Python or TypeScript, the orchestrator calls Serena in main session and injects `<symbols>` blocks into the delegation prompt. This restores the token savings (~200 tokens/file vs ~2,000) while working within the platform constraint.

**TypeScript added to Serena.** `.serena/project.yml` had `languages: [python]` only. Added `typescript`. The Serena Docker image includes bundled TypeScript 5.9.3 (Node.js pre-installed). The only obstacle was that the workspace is mounted read-only in Docker, so Serena couldn't create `.serena/cache/typescript/` — fixed by creating the directory locally before restart. TypeScript LSP started in 3.07s. Verification of TypeScript symbols in main session is pending session restart (current session has the old Python-only Serena state cached).

The pattern across all three findings is the same: **the failure mode is invisible until you test the non-happy path.** Speed 2 hides `model: dynamic`. Production use hides Serena's sub-agent gap. The `languages: [python]` omission was invisible because no TypeScript work had been delegated yet. The framework needs periodic enforcement tests — not just rules and checklists, but actual agent spawns in controlled conditions.

---
