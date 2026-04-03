---
type: devlog
audience: humans
purpose: education and retrospective — NOT a framework reference, NOT loaded in model context
updated: "2026-04-03"
---

# AI Governance Framework — Development Log

> This file records the thinking, research, and decisions behind the framework as it evolved.
> It is an educational artifact — read it to understand the *why*, not the *how*.
> For the *how*, see `AI_PLAYBOOK.md` and `docs/FRAMEWORK_README.md`.
> We is Claude and I learning together: he just rewrites our brainstorming sessions and coding sessions reviews following Hart's Rules for audience-aware writing, as instructed to do

Individual entries are in [`docs/devlog/`](devlog/).

---

## Index

### Foundation (Entries 1–9) — original notes, in Italian, written during the first experiments with Claude Code

| # | Title | Theme |
|---|---|---|
| [Entry 1](devlog/entry-01.md) | Naming the Problem: Agentic Bloat | Why autonomous agents bloat their own context |
| [Entry 2](devlog/entry-02.md) | The Deterministic Compiler Mental Model | The shift that unlocked the framework |
| [Entry 3](devlog/entry-03.md) | Research Synthesis: What the Ecosystem Had Learned | What we adopted and rejected from external frameworks |
| [Entry 4](devlog/entry-04.md) | Architectural Decision: Rules vs Skills vs Agents | Granularity of governance knowledge |
| [Entry 5](devlog/entry-05.md) | Reflexion: Honest Token Math | When to extract rules, when to skip |
| [Entry 6](devlog/entry-06.md) | The Plugin Architecture Path | Designed for extraction from the start |
| [Entry 7](devlog/entry-07.md) | EU AI Act Compliance Layer | Five risk categories, five controls |
| [Entry 8](devlog/entry-08.md) | Token Optimization Benchmarks | −46% from baseline, measured |
| [Entry 9](devlog/entry-09.md) | The Rule / Skill / Command Architecture Decision | Token cost model as the deciding factor |

### Maturity (Entries 10–11) — deep dives on specific decisions

| # | Title | Theme |
|---|---|---|
| [Entry 10](devlog/entry-10.md) | EU AI Act Citations, Confidence Scores, and the Auto-Review Mechanism | Audience differentiation, citation discipline, benchmark honesty |
| [Entry 11](devlog/entry-11.md) | Phase 2d: First Clean Session and a Quantified Cost Profile | First zero-violation session; delegation cost model |

### Incidents (Entries 12–16) — governance failures and what they taught us

| # | Title | Theme |
|---|---|---|
| [Entry 12](devlog/entry-12.md) | Feedback Simulation Session | Hallucination and yes-man patterns; Phase 3 replanning |
| [Entry 13](devlog/entry-13.md) | Wave 1 Scope Creep: Agent Autonomy Boundary Gaps | Agents improve adjacent systems when boundaries are implicit |
| [Entry 14](devlog/entry-14.md) | Phase 3b Gate & Rule-020 | Discretionary-choice anti-pattern; rule-020 extracted |
| [Entry 15](devlog/entry-15.md) | The Orchestrator Is Not Exempt | The orchestrator violates the same rules it enforces |
| [Entry 16](devlog/entry-16.md) | The Governance Paradox: Framework v4.0 Simplification | Too many rules = no rules followed; reduce to what gets followed |

### Operations (Entry 17+)

| # | Title | Theme |
|---|---|---|
| [Entry 17](devlog/entry-17.md) | YAML Frontmatter Schema Compliance | Schema-invisible metadata is invisible governance |
