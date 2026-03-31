---
type: devlog
audience: humans
purpose: education and retrospective — NOT a framework reference, NOT loaded in model context
updated: "2026-03-31"
---

# AI Governance Framework — Development Log

> This file records the thinking, research, and decisions behind the framework as it evolved.
> It is an educational artifact — read it to understand the *why*, not the *how*.
> For the *how*, see `AI_PLAYBOOK.md` and `docs/FRAMEWORK_README.md`.

---

## Entry 1 — Naming the Problem: Agentic Bloat

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The first discovery when switching from a passive assistant (Copilot) to an autonomous agent (Claude Code): if you ask the agent to "fix a bug" without any structure, it doesn't fix the bug. It first needs to *understand* the project. So it runs `ls`, `find`, `cat` — it explores the entire codebase before touching a single file, consuming tens of thousands of tokens on reconnaissance before writing a single line of code. For a trivial task this could cost $2–3 and introduce hallucinations from stale context.

We called this **Agentic Bloat**: the tendency of autonomous AI loops to expand their context window with irrelevant information until most of the compute is spent processing the agent's own previous mistakes rather than the actual task.

The insight was that this isn't a model quality problem — it's a governance problem. An agent with no constraints will always seek to maximize its context before acting, because that's the safe strategy from the model's perspective. We needed to make exploration impossible and surgical action the only available path.

---

## Entry 2 — The Deterministic Compiler Mental Model

The shift that unlocked the framework: stop thinking of Claude as a chatbot and start thinking of it as a **deterministic compiler**.

A compiler doesn't explore your filesystem. You hand it exactly the files it needs, and it produces exactly the output you specified. If you hand it bad input, it errors with a clear message rather than guessing. This is the contract we wanted.

Six architectural pillars emerged from this mental model:

1. **Push Context** — agents are forbidden from exploring the file system. Files must be explicitly passed to them. The agent never discovers; it receives.
2. **Tool Muzzling** — all commands the AI runs (`pytest`, `pip`, `npm`) must be silenced. Install logs, build output, test runner noise — none of it should enter the context window.
3. **Circuit Breakers** — maximum 2 debug attempts per failing command. On the third failure, stop and ask a human. This prevents the infinite retry loops that burn through token budgets.
4. **Targeted Editing** — no full-file rewrites. The agent uses surgical edit tools. A 300-line file that needs 3 lines changed should produce exactly 3 changed lines, not 300.
5. **Git Diff Reviews** — QA agents and documentation agents don't read source files; they read `git diff`. This enforces the "smallest correct change" principle on the reviewer side too.
6. **Dual-Speed Workflow** — Speed 1 for fast fixes (the agent acts like a senior developer with scoped files), Speed 2 for full features (an orchestrator decomposes the work and delegates to specialist subagents). These two modes have different cost profiles, different models, and different governance requirements.

---

## Entry 3 — Research Synthesis: What the Ecosystem Had Learned

Before building further, we reviewed the external literature and frameworks. The sources consulted:

- [Ultrathink (claudelog.com)](https://claudelog.com/mechanics/ultrathink/)
- [Bash Scripts batch writes (claudelog.com)](https://claudelog.com/mechanics/bash-scripts/)
- [Context Window Depletion (claudelog.com)](https://claudelog.com/mechanics/context-window-depletion/)
- [Tactical Model Selection (claudelog.com)](https://claudelog.com/mechanics/tactical-model-selection/)
- [Sub-agent Tactics (claudelog.com)](https://claudelog.com/mechanics/sub-agent-tactics/)
- [Anthropic Skills Spec](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [NeoLab Context Engineering Kit](https://github.com/NeoLabHQ/context-engineering-kit)
- [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode)

**What we adopted:**

- `ultrathink` keyword for HIGH-complexity tasks — triggers extended thinking in Sonnet at near-zero extra token cost
- Proactive context budget threshold — rather than waiting for degradation, trigger state compression after 15+ tool calls
- Destructive/non-destructive task classification before parallelizing — a more fundamental question than "do these touch different files?"
- "Consolidate → clear → act" between parallel agent waves — prevents context pollution from half-finished parallel threads
- Critic agent pattern (from oh-my-claudecode) — a dedicated agent challenges plans before any implementing agent is spawned
- Evidence-driven verification — every "pass" verdict requires actual terminal output, not assertions
- Separation of authoring and review — the agent that implements a feature must never be the one that verifies it

**What we rejected and why:**

- NeoLab CEK as a package — their orchestration instructions would collide with our custom Tech Lead agent
- Mandatory Tree-of-Thoughts on every task — 3–5× token cost for marginal gain over `ultrathink`
- LLM-as-Judge on every User Story — ~5,000–10,000 tokens per US × 35 US = up to 350,000 extra tokens with no meaningful QA improvement over human checkpoints
- oh-my-claudecode's plugin marketplace, external notifications, session sync, multi-provider auto-routing — all ruled out by EU AI Act compliance requirements (data boundary, provider allowlist, mandatory human checkpoints)

---

## Entry 4 — Architectural Decision: Rules vs Skills vs Agents

A recurring early mistake: appending "lessons learned" prose directly to `CLAUDE.md`. This is wrong because `CLAUDE.md` is always-loaded — every token added to it costs tokens in every future session, forever.

The correct architecture emerged from asking: what is the right granularity for different types of knowledge?

**Agents** — specialized roles with domain expertise. The orchestrator, the backend developer, the security reviewer. These are long-lived and session-persistent.

**Skills** — reusable procedures loaded on demand. How to delegate a User Story. How to run a phase gate. Triggered only when the relevant task starts.

**Rules** — behavioral constraints. "Never write a DB query without tenant_id." "Always read the migration file before touching the model." Small, discrete, actionable. One rule per file. Active until explicitly removed.

The key mechanic: `CLAUDE.md` stays a lean index that imports only currently-active rules. When a rule is no longer needed, remove the import. When a rule is valuable org-wide, promote it to an organization-level layer. **`CLAUDE.md` itself never grows** — only the import list changes.

---

## Entry 5 — Reflexion: Honest Token Math

We debated whether to run a "reflexion" cycle (extract session learnings into permanent rules) after every User Story. The math argued against it:

- Running reflexion: ~3,000 tokens
- Loading the resulting rule in every future session: ~200 tokens/session
- Break-even: the rule must prevent one debugging loop in its first 5 sessions

The real leverage is cross-project. A rule discovered in project 1 that prevents the same mistake in projects 2–N pays back N-fold. But rule bloat is a real risk — dozens of reflexion rules accumulate and start costing more than they save.

The correct cadence: run reflexion once per **phase gate** (not per US). Each run should produce at most 1–3 rules. The bar: "if an agent had known this from the start, would it have saved at least one circuit-breaker trigger?" If yes, keep it. If no, discard it.

---

## Entry 6 — The Plugin Architecture Path

The project's governance layer was designed to be extractable from the start. The insight: only `docs/AI_REFERENCE.md` is project-specific. Everything else in `.claude/` is org-generic.

The natural growth path:

1. **Git template repo** — fork the repo, run `/init-ai-reference`, you have the full framework for a new project  
2. **Shared submodule** — `.claude/commands/` as a git submodule shared across all repos in the org  
3. **Plugin** — a formally versioned package with a manifest, installable into any project that supports Claude Code

This wasn't built upfront because the framework needed to evolve first. Premature extraction would have locked in early mistakes as API surface.

---

## Entry 7 — EU AI Act Compliance Layer

As the framework matured, a compliance audit found five categories of risk from common agentic tooling (multi-provider routing, external session sync, plugin marketplaces, autonomous modes):

- **GDPR Art. 46** (data transfers) — sending code to non-EEA AI providers without a data processing agreement
- **EU AI Act Art. 10** (data governance) — session replay files that capture code and sync externally
- **EU AI Act Art. 12** (logging) — mutable local files don't satisfy tamper-proof logging requirements for high-risk AI
- **EU AI Act Art. 14** (human oversight) — autonomous modes that advance without human checkpoints
- **Supply chain risk** — public plugin marketplaces with unreviewed code execution

The framework's explicit provider allowlist, mandatory phase-gate checkpoints, local-only session notes, and rejection of external notification services are all responses to these risks — not over-engineering, but minimum necessary controls for enterprise deployment.

---

## Entry 8 — Token Optimization Benchmarks

After implementing the governance layer, we measured actual token usage:

| Configuration | Auto-loaded bytes | Notes |
|---|---|---|
| Baseline (monolithic CLAUDE.md) | ~68,000 | All rules inline |
| v1 (agents extracted) | ~60,764 | Agents loaded per-invocation |
| v2 (path-scoped rules + skills) | 36,878 | Conditional loading |
| Effective (unconditional only) | 32,936 | What actually loads for most tasks |

Result: **−54% from baseline** for typical tasks. For tasks that don't touch the specialized domains (auth, migrations, MCP), the saving is higher.

The CLAUDE.md itself went from ~450 lines to ~120 lines. The orchestrator agent went from a monolithic 2,500-token file to a 2,147-token core with a 745-token delegation skill loaded on demand.

Prompt caching (Claude's `cache_control` on system blocks) provides an additional 60–90% reduction on repeated context across a session — measured via `cache_read_tokens` tracking in the model layer.

---

## Entry 9 — The Rule / Skill / Command Architecture Decision

A recurring design question when adding governance: *which format does this belong in?* The question surfaced concretely when encoding Hart's Rules for audience-aware writing. It felt like a rule, but the decision revealed a cleaner architecture.

**The three formats and their jobs:**

- **Rule** = a behavioral red line. Any agent could violate it. The constraint must be active whenever a matching action is possible. Example: tenant isolation — any backend agent writing a DB query could accidentally omit the `tenant_id` filter. The rule loads for all `backend/**` work.
- **Skill** = a procedure for doing something well, loaded when a specific task type begins. The agent self-activates it at task entry. Example: speed2-delegation — only the orchestrator needs it, only when delegating. Zero cost otherwise.
- **Command** = a user-invoked macro. The human decides when to run it. Example: `/compress-state`, `/reflexion`. Zero cost until called.

**The token cost model is the deciding factor:**

Rules are always-loaded (within their path scope) — every token in a rule costs tokens in every matching session, forever. Skills and commands cost zero until triggered. This means the Rule format should be reserved for constraints where the *cost of not loading it* (a data breach, a QA bounce-back, a compliance violation) exceeds the *cost of loading it* in every session.

**Hart's Rules as the worked example:**

Audience-aware writing *feels* like a governance rule. But only `doc-writer` uses it, only during Mode B. A path-scoped Rule on `docs/**` would load for any agent injecting a `<file>` tag pointing at a doc — the orchestrator, backend-dev, anyone. Most of those agents have no use for writing register guidance. Result: rule loads in dozens of sessions where it does nothing.

As a Skill (`writing-audience.md`), it costs zero until `doc-writer` enters Mode B and explicitly loads it. The constraint is equally enforced; the token cost is a fraction.

**Decision rule (meta-rule for future governance additions):**
> Could any agent violate this, on any task? → Rule. 
> Is this a procedure for one specific agent or task type? → Skill. 
> Does a human need to invoke this explicitly? → Command.

---

## Entry 10 — EU AI Act Citations, Confidence Scores, and the Auto-Review Mechanism

Three separate decisions landed in the same session and reinforced each other.

### The EU AI Act coverage problem

The framework had a compliance section in `FRAMEWORK_README.md`, but it was thin: six table rows, no article citations, no audience differentiation. "EU AI Act compliant" in the header was closer to a badge than a proof. A systematic review of all front-door documents (README.md, AI_PLAYBOOK.md, HOW-TO-ADOPT.md) found that none of them named the regulation at all — they used "compliance" and "data boundary" as stand-in phrases.

This is a real problem for a specific audience. A CEO evaluating whether to adopt the framework doesn't know what "compliance" means without context — it could mean anything from PCI-DSS to internal code review policy. A DPO doing an audit needs article numbers and evidence locations, not prose assertions. The fix was to differentiate coverage by audience:

- **CEO/board**: lead with the liability exposure — Regulation (EU) 2024/1689 Art. 99(3) specifies penalties up to €30M or 6% of global turnover. Name the regulation; cite the penalty.
- **PM/project lead**: a control-mapping table showing each article, the framework's concrete control, and exactly which file proves it.
- **Security/DPO**: technical control descriptions — not "we protect your data" but "append-only `echo >>` enforced by command constraint, evidence at `docs/ARCHITECTURE_STATE.md`."
- **Developer**: two sentences explaining what Art. 14 (human oversight) and GDPR Art. 46 (data transfers) mean in day-to-day workflow.

The canonical compliance map lives in `docs/FRAMEWORK_README.md`. All other documents reference it rather than duplicating it. This means a single update to the compliance map propagates everywhere.

### The confidence score convention

The harder problem: we can't verify every article citation with certainty from within a coding session. The EU AI Act's Annex III (high-risk AI classification) is particularly context-dependent — whether a specific system qualifies depends on its deployment scope and sector, which requires legal judgment we can't substitute.

The established convention: every regulatory citation carries a confidence score inline.

- ★★★ = verified against official regulation text
- ★★☆ = cross-referenced, plausible, but not confirmed against primary source
- ★☆☆ = inferred — flag explicitly for legal review before relying on it

This isn't defensive hedging — it's accurate communication. A DPO reading a document with all ★★★ citations and no caveats would have no signal about which claims need independent verification. The ★★☆ on Annex III classification is more honest than a silent ★★★ would be. And it's actionable: anyone reading it knows to take that specific point to legal counsel.

The convention was also added as a formal register to `writing-audience.md` (Security/Legal/DPO register), so any future document targeting compliance audiences inherits the citation discipline automatically.

### The benchmark number problem

A subtler error surfaced during the review: the README claimed "a reduction of more than 90%" as a single figure. This conflated two different measurements:

1. **Context loading reduction**: from 60,764 to 32,936 bytes = −46%, measured by `benchmark/measure-context-size.sh`. This is about what loads in the model's context at session start.
2. **Per-task cost reduction**: 200,000+ API units (unstructured) down to <10,000 (structured) = up to 20×. This is about how many tokens a single task consumes when the agent role is bounded.

These are different claims about different things measured different ways. "90% reduction" implied they were the same metric. Someone checking the benchmark files would immediately see the −46% figure and distrust the rest of the claims. The fix was to state both metrics separately with their sources.

The lesson: performance claims in evaluator-facing docs must be traceable to a specific measurement, stated with the correct unit, and never averaged or combined across incompatible metrics.

### The auto-review mechanism

All of the above issues — wrong register, missing citations, conflated metrics, residual jargon — were found by a manual review pass at the end of the session. There was no systematic checklist. The review relied on the reviewer remembering what to look for.

The `/review-session` command formalizes this as a repeatable 7-check procedure: register audit, EU AI Act coverage, benchmark accuracy, citation confidence, link validity, ADAPT marker scan, residual jargon. Running it takes the same time as the manual pass but produces a structured report and catches things that manual review misses under cognitive load at the end of a long session.

The meta-insight: governance quality degrades fastest at session end, when the implementer is closest to the work and farthest from the reader's perspective. A command that runs the reviewer's checklist mechanically is most valuable precisely when the implementer least wants to run it.
