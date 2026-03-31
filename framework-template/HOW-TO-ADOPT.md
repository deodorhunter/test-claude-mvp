# AI Governance Framework — Portable Template

> **Developer?** Start at the [30-Minute Adoption Checklist](#30-minute-adoption-checklist).
> **Evaluating this for your organisation?** Start at [The Three Layers](#the-three-layers) and [Without AI Tooling](#without-ai-tooling).

This directory is the portable layer of the AI governance framework.  
Copy it to a new project, fill in the **ADAPT** markers, and you're running in under 30 minutes.

```
framework-template/
  CLAUDE.template.md              ← root CLAUDE.md for the new project
  agents/
    orchestrator.md               ← Tech Lead agent (stack-agnostic)
    backend-dev.md                ← Backend agent (adapt: stack, paths)
    critic.md                     ← Plan validator (copy as-is)
  rules/
    TEMPLATE.md                   ← rule authoring template (copy as-is)
  copilot-instructions.template.md  ← .github/copilot-instructions.md base
  HOW-TO-ADOPT.md                 ← this guide
```

---

## The Three Layers

```
Universal layer (this template)        Project layer (per-project)
──────────────────────────────         ─────────────────────────────
Speed 1/2 model                        docs/AI_REFERENCE.md
Token anti-patterns                    Project-specific rules (tenant, schema, etc.)
Circuit breaker rule                   Agent forbidden/owns paths
Phase gate workflow                    .claude/settings.local.json
Critic + Orchestrator logic            Backlog and US files
Copilot instructions structure
```

Separate the two cleanly. The universal layer never changes across projects. The project layer is written once at session start (`/init-ai-reference`) and updated as the project evolves.

---

## 30-Minute Adoption Checklist

1. **Copy files** — `cp -r framework-template/.claude /your-new-project/` and `cp -r framework-template/.github /your-new-project/`
2. **Rename** — `cp framework-template/CLAUDE.template.md /your-new-project/CLAUDE.md`
3. **Set stack identity** — edit `CLAUDE.md`: fill in the stack name in the project identity block
4. **Adapt the backend agent** — in `.claude/agents/backend-dev.md`, replace `owns:` and `forbidden:` paths with your project's directory structure
5. **Write `docs/AI_REFERENCE.md`** — run `/init-ai-reference` in Claude Code, or copy the template at `docs/AI_REFERENCE.md` and fill it in manually (stack, ports, test commands)
6. **Add your first project rule** — use `rules/TEMPLATE.md` to capture the first domain constraint you know about (e.g., auth scope isolation, DB naming convention)
7. **Add `.gitignore` entries** — `docs/.temp_context.md`, `docs/.session-notes.md`, `.claude/settings.local.json`
8. **Test Speed 1** — open Copilot Chat, attach a file, run a targeted fix. Verify it doesn't try to read other files.

---

## Common Failure Modes

**The AI read the whole codebase before making any change.**  
The project description file (`docs/AI_REFERENCE.md`) is missing or the global rules file (`CLAUDE.md`) wasn't found. Add both to the repo root before starting any AI-assisted work.

**AI costs vary wildly from session to session.**  
There's no habit of saving state between sessions. At the end of each session, run the context-save command (Claude Code: `/compress-state`; Copilot: use the `compress-state` prompt). This prevents the next session from re-reading everything from scratch.

**A piece of work came back from review broken and had to be redone from scratch.**  
No independent plan review happened before the work started. For any non-trivial feature, route the plan through the Critic agent before delegating to the implementing agent. The Critic catches flawed assumptions before they become expensive mistakes.

**Sessions got slower as the project grew — too many rules loading.**  
Rules accumulated beyond what's useful. Apply the survival test: would knowing this rule earlier have prevented at least one expensive mistake? If no, remove it. Rules are not a log — they are active constraints that load on every relevant session.

**The agent made changes outside the expected files.**  
The `forbidden:` and `owns:` path lists in the agent definition (`backend-dev.md`) weren't updated to match the project's actual directory structure. These are the only lines that need changing — the rest of the agent definition is stack-agnostic.

---

## Without AI Tooling

The governance principles in this framework apply to human code review workflows too:

- **Speed 1 / Speed 2 split** = difference between a PR comment fix and a full feature spec
- **Circuit breaker (max 2 attempts)** = time-box a debugging session; escalate after 2 hours, not after 2 days
- **Atomic changes** = reviewer contract: each PR does one thing
- **Targeted editing** = code review principle: don't refactor adjacent code in the same PR
- **No autonomous exploration** = reviewer shouldn't need to read the whole codebase to review a PR — the PR description should provide context

The framework doesn't create new discipline. It formalizes discipline that good engineering teams already practice and makes it explicit enough that an AI agent can follow it.

---

## EU AI Act Adoption Notes

> **Regulation:** EU AI Act — Regulation (EU) 2024/1689 [[Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)], in force 1 August 2024. High-risk AI obligations apply from August 2026.
> **Classification:** Whether your use of AI qualifies as high-risk under Annex III of Reg. (EU) 2024/1689 depends on your deployment context and sector. Consult your legal or DPO team. [Cross-referenced]

This template provides the following controls out of the box:

| Article | Control provided by this template |
|---|---|
| Art. 9 — Risk management | Critic agent pre-validation; circuit breaker (2-attempt hard stop); pre-prompt hook blocking uninformed AI operation |
| Art. 10 — Data governance | Provider allowlist (`rule-011`); tenant data isolation (`rule-001`); MCP full-schema validation (`rule-012`) |
| Art. 12 — Record-keeping | Append-only `/handoff` logging; audit trail in `docs/ARCHITECTURE_STATE.md` |
| Art. 13 — Transparency | All agent roles and constraints documented in `.claude/agents/`; every AI action tied to a named User Story |
| Art. 14 — Human oversight | Mandatory approval at every US checkpoint and Phase Gate; no autonomous modes; Hard Rule 17 (no self-approval) |
| GDPR Art. 46 — Data transfers | Only local (Ollama) and EU-DPA-covered (Claude API) providers permitted; auto-routing to other providers blocked |

**What requires your own project-specific work:**
- Define the provider allowlist for your specific deployment (update `rule-011` with your approved providers and their DPAs)
- Adapt the tenant isolation rule (`rule-001`) to your data model if your system is not multi-tenant
- Conduct or commission a Data Protection Impact Assessment (DPIA) under GDPR Art. 35 — the framework's controls are inputs to the DPIA, not a substitute for it
- If your system may qualify as high-risk under Annex III, engage legal counsel to confirm classification and verify that your implementation of Art. 9, 10, 12, 13, and 14 satisfies the applicable conformity requirements

**For the full article-by-article control map with evidence pointers:** copy `docs/FRAMEWORK_README.md` from the source repository into your project's `docs/` folder.
