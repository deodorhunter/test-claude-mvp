---
name: ralplan-deliberation
description: "Structured deliberation record for HIGH complexity US. Produces a Deliberation Record (DR) that documents the reasoning behind the plan before any implementing agent is spawned. Applies only to HIGH tasks — MEDIUM tasks use ultrathink only."
version: "1.0"
type: skill
trigger: "Orchestrator invokes before delegating HIGH complexity US"
updated: "2026-03-31"
---

<insight>
Before delegating a HIGH complexity US, write a Deliberation Record that forces explicit articulation of principles, decision drivers, viable options, and anticipated failure modes. This prevents drift between plan and implementation and gives the critic concrete assumptions to challenge.
</insight>

<why_this_matters>
HIGH tasks that skip deliberation tend to have implicit assumptions that only surface at QA bounce-back time (~25k tokens wasted per bounce). The DR makes these assumptions explicit BEFORE the implementing agent is spawned.
</why_this_matters>

<recognition_pattern>
Apply when: orchestrator classifies a US as HIGH complexity AND is about to delegate to a Sonnet-tier implementing agent. Do NOT apply to MEDIUM tasks (ultrathink is sufficient) or LOW tasks.
</recognition_pattern>

<approach>
1. State 3-5 guiding principles that must hold throughout implementation.
2. Identify the top 3 decision drivers (constraints, tradeoffs, requirements that most shape the approach).
3. List ≥2 viable options with bounded pros/cons (max 3 bullets each).
4. State the chosen option and why (1-3 sentences).
5. State anticipated consequences: what this makes easier, what it forecloses.
6. For HIGH-risk US (auth/security/schema migrations): add a pre-mortem with 3 failure scenarios + test plan skeleton.
7. Write the `<deliberation_record>` block into `docs/plan.md` before spawning the implementing agent.
</approach>

<example>
```xml
<deliberation_record us="US-019" complexity="HIGH" date="2026-03-31">
  <principles>
    1. Tenant isolation is non-negotiable — no cross-tenant data in any path
    2. Schema changes require migration-first (rule-002)
    3. Audit log every MCP query
  </principles>
  <decision_drivers>
    1. Qdrant must remain the only vector store (no second store)
    2. RAG latency budget: <500ms p95
    3. EU AI Act: source attribution on every context chunk
  </decision_drivers>
  <options>
    Option A: Lazy embedding on first query
      + Zero startup cost
      - First-query latency spike
    Option B: Eager embedding at upload
      + Consistent latency
      - Upload endpoint becomes blocking
  </options>
  <chosen>Option B — upload is already async; blocking is acceptable there</chosen>
  <consequences>
    Enables: consistent RAG latency
    Forecloses: lazy-load optimization (acceptable tradeoff)
  </consequences>
  <pre_mortem failure_scenarios="3">
    1. Embedding model OOM at upload → rate-limit concurrent uploads
    2. Qdrant unavailable at query time → fallback to keyword search
    3. Tenant ID not propagated to vector metadata → cross-tenant leak
  </pre_mortem>
</deliberation_record>
```
</example>
