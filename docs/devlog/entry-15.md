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

#### Benchmark Note (Logged for Phase 3c Gate)

The user asked whether the benchmark suite has been re-run with Framework v3.0 (rule-020 + auto-compress hook + symbol-context guidance active). It has not. US-064 (SWE-Agent evaluation, Phase 3d) addresses the benchmark methodology question. The re-run with current framework, against Phase 3b baselines, remains an open action item for Phase 3d or Phase 4 prep.

---
