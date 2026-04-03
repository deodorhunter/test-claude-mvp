← [Back to DEVLOG index](../DEVLOG.md)

## Entry 12 — Feedback simulation session - 2026-04-02

> We conducted a test feedback simulation session, prompting Claude with some good and bad user feedbacks, and testing its response and planning sequence and reasoning.
> It hallucinated and it behaved like a yes-man.
> This was expected, here's what happened in this session and what was actioned to prevent it in future sessions.

Phase 3 was originally slated for API & Frontend work (US-021 through US-029). That scope is now deferred to Phase 4. Phase 3 is repurposed entirely for framework governance upgrades, driven by 14 user feedback items collected at the milestone stop point.

#### Feedback triage

14 items were collected (verbatim, uncurated). They clustered into 7 themes: token/model costs, automation, benchmarking, Copilot DX, adoption friction, infrastructure docs, and Plone-MCP naming confusion. 15 US were generated from these themes. After critic review, 2 were dropped and 4 were rewritten.

#### The hallucination incident

US-052 (Automated Cost Extraction) was generated with 6 implementation details: a session log path (`~/.claude/projects/<hash>/sessions/`), a JSONL field schema, a `--output-format json` CLI flag, cost rates, and a CSV output schema. User challenged the `smallFastModel` setting key referenced in US-051. Audit revealed US-052 was 75% fabricated — none of the paths, field names, or CLI flags could be verified against Claude Code documentation or settings schema. US-052 was dropped entirely.

The incident also contaminated US-051 (which referenced `smallFastModel` as a global settings key — no such key exists) and US-056 (which listed hook event types `PreCompact` and `SubAgentComplete` that cannot be verified). Both were rewritten to reference only verified mechanisms: agent frontmatter `model:` keys (confirmed in 12 agent files) and `UserPromptSubmit`/`PostToolUse` hooks (confirmed in `.claude/settings.json`).

Lesson: agent-generated US that describe tool internals (paths, schemas, flags) must be verified against actual files or documentation before entering the backlog. An unverified implementation detail is not a plan — it is a hallucination wearing a plan's clothes.

#### The yes-man pattern

Critic review of the 15 US found 3 that were reflexive agreement with user feedback rather than genuine value:

- **US-053** proposed creating `docs/ORCHESTRATION_GUIDE.md` — a 4th guidance document alongside `CLAUDE.md`, `orchestrator.md`, and `product-owner.md`. The real need is consolidation into existing `docs/AI_REFERENCE.md`, not another file.
- **US-057** proposed `make init-framework` when users literally reported their workflow as "copied `.claude/` directly." Building a make target for something `cp -r` already does is over-engineering.
- **US-059** proposed a structured feedback mechanism with a dedicated command, template file, and make target. For a framework used by fewer than 10 people, a section in an existing doc suffices. Dropped; its 10-line feedback template was absorbed into US-057.

Counter-measure: `/refine-backlog` command (US-065, implemented) — a pre-sprint Agile ceremony backed by a 5-question yes-man filter encoded as a skill. See `.claude/skills/backlog-refinement/SKILL.md` and `.claude/commands/refine-backlog.md`. Codified as rule-018 (ceremony reminder, not automated gate).

#### Archive cleanup — US-050

The `.claude/rules/archive/` directory contained 12 verbose original rule drafts (418 lines) that were auto-loaded alongside 14 compact project rules (289 lines) every session. Archive was 59% more text than the active rules. Moved to `docs/rules-archive/` — outside the auto-load path. Immediate savings: 418 lines per session context window.

#### Phase 3 final structure

12 active US across 4 sub-phases, 2 dropped, 2 already done:

- **3a — Token & Model** (3 US): US-050 ✅, US-051, US-053
- **3b — Automation & Cognitive** (4 US): US-054, US-055, US-056, US-065 ✅
- **3c — Adoption & DX** (3 US): US-057, US-058, US-060
- **3d — Infra & Architecture** (4 US): US-061, US-062, US-063, US-064
- **Dropped:** US-052 (hallucinated), US-059 (yes-man)

---
