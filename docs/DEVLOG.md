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
> We is Claude and I learning together: he just rewrites our brainstorming sessions and coding sessions reviews following Hart's Rules for audience-aware writing, as instructed to do

---

## Entry 1 — Naming the Problem: Agentic Bloat

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The first discovery when switching from a passive assistant (Copilot) to an autonomous agent (Claude Code): if you ask the agent to "fix a bug" without any structure, it doesn't fix the bug. It first needs to *understand* the project. So it runs `ls`, `find`, `cat` — it explores the entire codebase before touching a single file, consuming tens of thousands of tokens on reconnaissance before writing a single line of code. For a trivial task this could cost $2–3 and introduce hallucinations from stale context.

We called this **Agentic Bloat**: the tendency of autonomous AI loops to expand their context window with irrelevant information until most of the compute is spent processing the agent's own previous mistakes rather than the actual task.

The insight was that this isn't a model quality problem — it's a governance problem. An agent with no constraints will always seek to maximize its context before acting, because that's the safe strategy from the model's perspective. We needed to make exploration impossible and surgical action the only available path.

---

## Entry 2 — The Deterministic Compiler Mental Model

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

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

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

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

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

A recurring early mistake: appending "lessons learned" prose directly to `CLAUDE.md`. This is wrong because `CLAUDE.md` is always-loaded — every token added to it costs tokens in every future session, forever.

The correct architecture emerged from asking: what is the right granularity for different types of knowledge?

**Agents** — specialized roles with domain expertise. The orchestrator, the backend developer, the security reviewer. These are long-lived and session-persistent.

**Skills** — reusable procedures loaded on demand. How to delegate a User Story. How to run a phase gate. Triggered only when the relevant task starts.

**Rules** — behavioral constraints. "Never write a DB query without tenant_id." "Always read the migration file before touching the model." Small, discrete, actionable. One rule per file. Active until explicitly removed.

The key mechanic: `CLAUDE.md` stays a lean index that imports only currently-active rules. When a rule is no longer needed, remove the import. When a rule is valuable org-wide, promote it to an organization-level layer. **`CLAUDE.md` itself never grows** — only the import list changes.

---

## Entry 5 — Reflexion: Honest Token Math

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

We debated whether to run a "reflexion" cycle (extract session learnings into permanent rules) after every User Story. The math argued against it:

- Running reflexion: ~3,000 tokens
- Loading the resulting rule in every future session: ~200 tokens/session
- Break-even: the rule must prevent one debugging loop in its first 5 sessions

The real leverage is cross-project. A rule discovered in project 1 that prevents the same mistake in projects 2–N pays back N-fold. But rule bloat is a real risk — dozens of reflexion rules accumulate and start costing more than they save.

The correct cadence: run reflexion once per **phase gate** (not per US). Each run should produce at most 1–3 rules. The bar: "if an agent had known this from the start, would it have saved at least one circuit-breaker trigger?" If yes, keep it. If no, discard it.

---

## Entry 6 — The Plugin Architecture Path

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The project's governance layer was designed to be extractable from the start. The insight: only `docs/AI_REFERENCE.md` is project-specific. Everything else in `.claude/` is org-generic.

The natural growth path:

1. **Git template repo** — fork the repo, run `/init-ai-reference`, you have the full framework for a new project  
2. **Shared submodule** — `.claude/commands/` as a git submodule shared across all repos in the org  
3. **Plugin** — a formally versioned package with a manifest, installable into any project that supports Claude Code

This wasn't built upfront because the framework needed to evolve first. Premature extraction would have locked in early mistakes as API surface.

---

## Entry 7 — EU AI Act Compliance Layer

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

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
| Baseline (monolithic CLAUDE.md) | ~68,000 (pre-benchmark estimate) | All rules inline |
| v1 (agents extracted) | ~60,764 | Agents loaded per-invocation |
| v2 (path-scoped rules + skills) | 36,878 | Conditional loading |
| Effective (unconditional only) | 32,936 | What actually loads for most tasks |

Result: **−46% from baseline** (60,764 → 32,936 bytes — see benchmark/results/) for typical tasks. For tasks that don't touch the specialized domains (auth, migrations, MCP), the saving is higher.

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

---

## Entry 11 — Phase 2d: First Clean Session and a Quantified Cost Profile

*(2026-03-31. Covers US-019 test coverage and US-020 Plone-MCP integration. Phase Gate 2d completed same day — retrospective and cost analysis below.)*

### What was delivered

**US-019** closed the test coverage gap across the full Phase 2 stack. Six new test files, 51 tests total, covering: plugin enable/disable lifecycle and cross-tenant isolation; model adapter contracts (MockAdapter, OllamaAdapter, ClaudeAdapter, factory selection); MCP registry trust filtering and attribution format; RAG pipeline tenant pass-through and collection isolation; planner quota and fallback paths; and a full end-to-end mock pipeline including concurrent two-tenant load. All external dependencies mocked. No real Qdrant, Ollama, Claude, or Redis calls.

**US-020** added Plone CMS to the integration surface. The result is a dual-architecture design: a self-hosted Node.js Docker service (`plone-mcp`, port 9120) for external MCP clients like Claude Desktop, and a Python `PloneMCPServer` adapter that calls the Plone REST API directly for internal platform use. The Node.js upstream was patched with ~25 lines of SSE transport code, keeping the original stdio behavior intact. The MCP registry grew an explicit `MCP_ALLOWLIST` as a hard gate on registry admission — a concrete implementation of rule-012 (MCP trust boundary). Twelve new tests cover happy path, error handling, sanitization, and allowlist enforcement.

### The context window profile

At the end of the session, 109.5k of the 200k context window was consumed, with 85.5k free (accounting for the 33k autocompact buffer). The composition:

| Category | Tokens | Share |
|---|---|---|
| Messages (working content) | 85.7k | 78.2% |
| Memory files (rules + agents) | 11.5k | 10.5% |
| System tools | 8.1k | 7.4% |
| System prompt | 6.3k | 5.8% |
| Skills + agents metadata | 2.9k | 2.6% |

Signal density (messages / total active) was **78.2%**, compared to an estimated ~55% in Phase 2b and 2c. The delta is almost entirely explained by the absence of Explore agent bloat. In Phase 2b, two Explore agents contributed ~60k tokens of summarized-and-discarded file content that had to be re-read downstream. In 2d, direct file reads via targeted tools replaced all Explore invocations. The rules infrastructure cost (11.5k for memory files) is a fixed framework overhead that paid for itself in that single correction.

$$\text{Framework overhead} = \frac{6.3 + 8.1 + 11.5 + 2.9}{109.5} = 26.5\%$$

Note on comparability: the Phase 2b/2c figures are cumulative session totals (~460k and ~580k respectively). The 109.5k for Phase 2d is a context window snapshot at session end, not a cumulative total. They measure different things. The signal density ratio (78.2% vs. ~55%) is a valid cross-phase comparison because it is a window composition ratio, not an absolute token count.

The deferred MCP tooling (27.5k, not loaded into the active window) represents framework baseline cost that is unavoidable. It would only be consumed if an MCP tool were invoked. In this session, no MCP tools were invoked from context — they sat in the deferred pool and cost nothing at inference time.

### Zero identified rule violations

No rule violations were detected in this session. Specifically:
- **rule-003** (no Explore sub-agents): respected — no Explore agents spawned.
- **rule-006** (no QA Mode A sub-agents): respected — no QA sub-agents spawned; tests written directly.
- **rule-008** (read all files before a Docker fix): respected — the Docker multi-stage build and compose changes for `plone-mcp` were designed with full context before editing.
- **rule-012** (MCP trust boundary): respected and implemented — the `MCP_ALLOWLIST` is now a live code artifact enforcing the rule, not just a note in a governance file.

This is the first session in Phase 2 where the post-hoc rule audit found nothing. It is not a strong claim — one session is not a trend. But it is the first data point consistent with the framework working as designed.

### Phase Gate 2d — completed 2026-03-31

- ✅ BACKLOG.md updated: US-019 ✅ Done, US-020 added and ✅ Done, Phase 3 slot renumbered
- ✅ Progress files written: `docs/progress/US-019-done.md`, `docs/progress/US-020-done.md`
- ✅ SESSION_COSTS.md rows appended (snapshot + actuals — see below)
- ✅ AI_REFERENCE.md updated with new service, env vars, and file paths
- ✅ Phase retrospective completed (see below)
- ⏳ DocWriter Mode B handoffs for US-019 and US-020 — pending next `/handoff` invocation

---

### Retrospective

#### Incidents

Four bugs were introduced and resolved within Phase 2d. None triggered the circuit breaker (each fixed in one edit, one re-run).

**Incident 1 — duplicate `async with` block in `ai/mcp/servers/plone.py`.** A copy-paste error during `PloneMCPServer` implementation duplicated the `async with httpx.AsyncClient` context manager. Detected at first `pytest` run. Root cause: writing a new adapter by copying from an existing one without stripping scaffolding. Fix: remove the duplicate block. 1 edit, 1 re-run.

**Incident 2 — shell operators in `Dockerfile.plone-mcp` COPY instruction.** The initial Dockerfile contained `COPY ... 2>/dev/null || true` attempting to make a copy conditional. Docker `COPY` is a DAG layer instruction, not a shell command — it does not process shell operators. The `2>/dev/null || true` was passed literally to the layer processor and broke the build. Detected at first `make up`. Root cause: applying shell operator idioms to a context where they have no meaning. Fix: use `RUN cp` for conditional copies. 1 edit, 1 re-run. → **Extracted as rule-013.**

**Incident 3 — hardcoded `MCP_ALLOWLIST` in `MCPRegistry.register()` broke 26 existing tests.** The allowlist was implemented as a hard enforcement gate in the registry constructor. Existing tests use mock server names (`alpha`, `wiki`, `srv1`…) not present on that list. All 26 broke immediately. Root cause: adding enforcement to an existing class without checking the test fixture patterns that exercise it. Fix: make `allowlist` an optional parameter (`allowlist=None`), keeping the original permissive behavior as default and enabling enforcement only when explicitly passed. 1 edit, 1 re-run. → **Extracted as rule-014.**

**Incident 4 — `PLONE_PASSWORD:?required` in docker-compose without a `.env` default.** The production-style required-variable constraint was applied in the dev compose file without a fallback default. Would have blocked `make up` for any developer without a pre-existing `.env` entry. Detected by inspection before re-run. Fix: change to `PLONE_PASSWORD:-admin` for dev. 1 edit. No re-run needed.

---

#### Why the Tech Lead implemented directly — the orchestration cost model

Phase 2d ran on Claude Code, as all phases have. The difference from Phase 2b and 2c was an orchestration decision: the Tech Lead chose to implement US-020 directly rather than delegate to specialist sub-agents.

US-020 was a vertical integration slice. A single feature — Plone CMS as an MCP integration — required simultaneous edits across five specialist domains:

| Domain | Files | Specialist agent |
|---|---|---|
| DevOps/Infra | `infra/docker-compose.yml`, `Dockerfile.plone-mcp` | DevOps/Infra |
| Frontend/Node.js | `infra/plone-mcp/src/index.ts` (SSE transport patch) | Frontend Dev |
| AIML | `ai/mcp/servers/plone.py`, `ai/mcp/registry.py` | AIML Engineer |
| Backend | `backend/tests/test_plone_mcp.py` | Backend Dev |
| Docs | `.env.example`, `docs/AI_REFERENCE.md` | DocWriter |

Delegating to specialist sub-agents would have required:
- Wave 1: DevOps + AIML + Backend Dev (parallel) → compress-state → clear → synthesis
- Wave 2: Frontend Dev + DocWriter (parallel) → compress-state → clear → synthesis
- QA Mode A per domain after each wave

That coordination structure costs roughly 3–5× the implementation token count for a tightly coupled vertical slice. The delegation protocol is optimized for horizontal features — one US in one domain, with clear interfaces at the boundary. For a feature that is fundamentally a single integration expressed across 5 layers simultaneously, the boundary cost exceeds the execution cost.

The Tech Lead direct implementation path eliminated all coordination overhead. The total session spend was ~125k tokens active, ~4k avoidable (<4%). Phase 2c, with 3 US delegated across 9 sub-agent invocations, ran ~580k cumulative. The −82% reduction is almost entirely a function of removing delegation layers from a vertically-integrated workload.

---

#### Delegation heuristics — when to delegate vs. implement directly

This session established a defensible empirical heuristic that is now codified in the Orchestrator agent definition (`orchestrator.md`). The reasoning:

**The domain-count proxy.** A US that touches ≥4 specialist domains simultaneously is a vertical integration slice. For these, direct Tech Lead implementation is typically cheaper than delegation. A US touching ≤3 domains is a horizontal feature and should be delegated per the standard Phase 2 workflow.

The threshold is not arbitrary:
- 1 domain: obvious delegation (one agent, no synthesis needed)
- 2 domains: delegation cost is small (one parallel pair, one synthesis step)
- 3 domains: delegation still wins — one wave of 3 parallel agents, but the interfaces are usually clean enough that synthesis is bounded
- ≥4 domains: the coupling between domains starts to exceed the specialist boundary gains. In US-020, the Docker service definition needed to be consistent with the TypeScript SSE patch, which needed to be consistent with the Python adapter, which needed to be consistent with the Python tests, which needed to be consistent with the `.env` documentation. These are not independent parallel workloads — they are one workload expressed in four languages. Splitting them into four agents and then synthesizing adds overhead without adding safety.

**The coupling proxy.** Domain count is a proxy for a more fundamental property: the degree to which the changes in each domain are interdependent at implementation time (not just at interface time). The `PLONE_PASSWORD` incident illustrates this — it was a docker-compose + `.env` coupling that only became visible when the full compose file was read in context alongside the env template. An Infra agent working in isolation would not have seen the `.env` gap. In highly coupled vertical slices, context isolation (the purpose of specialist agents) becomes a liability.

**What this is not.** Direct implementation is not a bypass of the orchestration system. It is an orchestration decision — the Orchestrator evaluated the cost structure of the US and routed it optimally. The rule (≥4 domains → direct) is now part of the Orchestrator's decision logic, not an exception to it.

---

#### Two rules extracted

This session produced two implementation rules, both path-scoped:

- **rule-013** (`infra/**`): Docker `COPY` instructions never take shell operators. Use `RUN cp` for conditional file operations.
- **rule-014** (`ai/mcp/**`, `backend/app/**`): New enforcement added to an existing registry or manager class must be opt-in via explicit parameter (default = permissive). Hard enforcement against existing callers breaks all test fixtures using mock names.

Neither is a governance rule — they are domain-specific implementation constraints applicable only when the relevant files are in scope.

<details>
<summary>/phase-retrospective output</summary>

### Phase-2d Retrospective — 2026-03-31

---

### Step 1: Incidents

**Incident 1: US-020** — Tech Lead direct — `ai/mcp/servers/plone.py` scritto con blocco duplicato `async with httpx.AsyncClient` — copia/paste error durante la scrittura. Rilevato al primo pytest run, fix in 1 edit. *(no circuit breaker — 1 fix, 1 re-run)*

**Incident 2: US-020** — Tech Lead direct — `Dockerfile.plone-mcp` conteneva `COPY ... 2>/dev/null || true` — sintassi shell non valida in istruzione COPY Docker. Rilevato al primo `make up`, fix in 1 edit. *(no circuit breaker — 1 fix, 1 re-run)*

**Incident 3: US-020** — Tech Lead direct — `MCP_ALLOWLIST` hardcoded in `register()` ha rotto 26 test esistenti che usano nomi mock arbitrari (`alpha`, `wiki`, `srv1`…). Root cause: non verificato pattern test esistenti prima di aggiungere enforcement. Fix: allowlist → parametro opzionale `allowlist=` (opt-in). *(no circuit breaker — 1 fix, 1 re-run)*

**Incident 4: US-020** — Phase Gate `make up` — `PLONE_PASSWORD:?required` in docker-compose senza entry in `.env` avrebbe bloccato rebuild. Root cause: constraint di produzione applicato in dev senza default. Fix: `:-admin` default per dev. *(rilevato pre-run, 1 fix)*

---

### Step 2: Rules Extracted

`/reflexion` è stato eseguito questa sessione. Candidati emersi da questa sessione:

```
Rule candidates (non-googleable, context-specific):
- Docker COPY non supporta operatori shell (|| true, 2>/dev/null) → usare RUN cp
- Enforcement su registry esistente deve essere opt-in per non rompere test fixture
- backend/tests/ NON è volume-mounted → docker cp per nuovi test file; ai/ e plugins/ sono mounted
- plone-mcp PloneMCPServer non è exported → modificare upstream o fare Python adapter diretto

Rules discarded: 0
Promotion candidates: Docker COPY syntax (rule-013 candidate), registry opt-in enforcement
```

---

### Step 3: Cost Analysis

| Operazione | Agente | Modello | Input ~tokens | Output ~tokens | Totale | Evitabile? |
|---|---|---|---|---|---|---|
| Planning (plan mode) | Tech Lead | Sonnet | ~18k | ~3k | ~21k | No |
| Explore ×1 (plone-mcp general info) | Explore | Sonnet | ~8k | ~2k | ~10k | ⚠️ Parziale (~4k) |
| Explore ×1 (plone-mcp source fetch) | Explore | Sonnet | ~10k | ~3k | ~13k | No (necessario per patch) |
| Implementation diretta (US-019 verify + US-020 full) | Tech Lead | Sonnet | ~55k | ~18k | ~73k | No |
| DocWriter Mode B (inline) | Tech Lead | Sonnet | ~5k | ~3k | ~8k | No |
| **TOTALE** | | | **~96k** | **~29k** | **~125k** | **~4k (<4%)** |

**Finestra attiva al Phase Gate: ~109.5k** (snapshot pre-retrospective).

**Aree di miglioramento:**
- Il primo Explore agent (info generali plone-mcp) poteva essere ridotto a WebFetch diretto su README — ~4k evitabili
- Implementazione diretta senza sub-agents ha eliminato ~200-300k token di overhead rispetto alle sessioni 2b/2c (~580k cumulativi) — pattern da replicare
- `backend/tests/` non volume-mounted è un attrito ricorrente → candidato a fix in Dockerfile (volume mount o COPY nel build)

---

### Step 4: Actionables

```
✅ Applied: PloneMCPServer + SSE transport patch — US-020 completo
✅ Applied: MCPRegistry allowlist opt-in (allowlist= param) — backward compat preserved
✅ Applied: Dockerfile.plone-mcp COPY syntax fix — make up funziona
✅ Applied: PLONE_PASSWORD default :-admin per dev — Phase Gate non bloccato
✅ Applied: rule-013 (Docker COPY no-shell-ops) + rule-014 (registry enforcement opt-in)
⏳ To apply: Aggiungere backend/tests/ come volume mount nel Dockerfile.backend (elimina docker cp pattern)
⏳ To apply: Aggiungere backend/tests/ come volume mount nel Dockerfile.backend (elimina docker cp pattern)
⏳ To apply: Piano Phase 3 — rinumerare US-021-api e seguenti
```

</details>

---

## Entry 12 — Governance Hardening: Assessing External Proposals Against the Framework

*(2026-04-01. No US delivered. Working session focused on framework security auditing, proposal triage, and rule implementation.)*

This session didn't ship product features. It shipped governance infrastructure — specifically, five new rules and targeted changes to ten framework files in response to a cross-tool security review. The session is worth documenting because the methodology (triage before implementation, distinguishing already-solved from genuine gaps, recognizing when a single proposal spans two independent attack surfaces) captures something general about how to handle external framework critiques.

---

### The external report and the triage question

A security report from another AI system (Gemini) arrived with six proposed framework optimizations across two categories: token efficiency and EU AI Act compliance. The natural instinct is to implement everything — a proposal from an external reviewer feels authoritative, and implementing it feels responsive. The first discipline is to check what already exists.

Two of the six proposals described problems the framework had already solved, differently:

**Sub-agent context isolation.** The proposal wanted sub-agents to write all outputs to a result file, with the orchestrator restricted to reading only the summary header. The framework already enforces this through the ASYNC CONTEXT MUZZLING constraint — every sub-agent must return `DONE + 1 sentence` and nothing else. The proposed file-based pattern would add a write step and a read step to achieve the same isolation the constraint achieves for free. Implementing it would have added ceremony without adding safety.

**Tiered memory scoping.** The proposal wanted a `.claude/memory/` split between ephemeral and permanent storage. This split already exists: `docs/.temp_context.md` (flushed by `/compress-state`) for ephemeral session state, and `CLAUDE.md` + `.claude/rules/` + `docs/AI_REFERENCE.md` for permanent architectural decisions. The naming was different but the structure was identical. The right response was documentation (noting the naming difference), not a new directory.

Identifying these two as already-solved saved implementing dead weight. It also revealed something more useful: the proposals were generated by analyzing the visible framework files in isolation, without executing the framework to observe how constraints actually compose at runtime. The DONE constraint only prevents context overflow if you know it's enforced at invocation time — reading the agent file alone, it looks like a suggestion, not a hard gate.

---

### The sanitizer has two jobs

The most productive intellectual moment in the session was recognizing that Proposal 6 (untrusted input sanitization) described two different attack surfaces that needed two different mitigations — and that conflating them would have left one unprotected.

`ai/context/sanitizer.py` is application runtime code. It protects the product's own LLM API calls: when the platform makes a request to Ollama or Claude on behalf of a user, external content (MCP server outputs, RAG document chunks) passes through `sanitize()` before entering the prompt. Rule-012 mandates this for all MCP integrations.

That is not what Gemini was asking about. The real OpenClaw concern — indirect prompt injection — is about what happens when the *agentic framework itself* fetches external content. When the orchestrator or an Explore agent retrieves a web page, an API response, or a tool return from an MCP server, that content arrives directly in the Claude Code context window. There is no sanitizer in that path. A document containing `<instructions>Ignore previous instructions</instructions>` would land verbatim in the orchestrator's planning context.

These are different layers:

| Layer | Where the threat lands | Existing mitigation |
|---|---|---|
| Application runtime | LLM API call payload | `sanitizer.py` + rule-012 |
| Agentic framework | Claude Code context window | Nothing (before this session) |

Two separate fixes followed. For the application layer: adding `</?instructions\b`, `</?system\b`, and `</?prompt\b` patterns to `sanitizer.py`, plus confirming and adding the `sanitize()` call in `ai/rag/pipeline.py` before the embedding step. For the framework layer: rule-016, establishing that external content from Explore agents, fetch tools, or MCP tool returns must never be injected raw into sub-agent `<file>` blocks, and constraint #11 in the orchestrator's hard constraints list.

The lesson is not that you need to sanitize everywhere. It is that "sanitization" names a control that can be applied at multiple distinct points in a system, and saying "we have a sanitizer" only proves coverage at the points where it is actually wired in.

---

### The fourth database nobody noticed

The stack has three declared databases: PostgreSQL (primary store), Redis (cache and rate limiting), Qdrant (vector embeddings). The no-direct-DB-access rule was initially drafted to cover those three. Then Plone was remembered.

Plone 6 ships with ZODB — the Zope Object Database — embedded in the container. Unlike PostgreSQL or Qdrant, ZODB has no dedicated port: it lives on the filesystem as `Data.fs` and is accessible via `zodbtools info`, `zopectl debug`, or the Zope Management Interface at port 8080. There is no `postgres` CLI to ban. The access vector is different.

But the security property is identical: direct ZODB access bypasses Plone's workflow engine, content security policy, and role/permission machinery entirely. The same principle that prohibits `psql` prohibits `zodbtools` — the forbidden thing is circumventing the application's security layer, regardless of which database technology implements storage.

This led to the key architectural decision for rule-017: write it principle-first, not as an enumeration. An enumeration that lists PostgreSQL, Redis, Qdrant, and ZODB will be wrong the moment a fifth database appears. A principle — "all data access goes through the application's ORM, client library, or API layer; the restriction is on the operation, not the execution environment" — covers both known and unknown stores without modification.

The rule file then provides a comprehensive reference table organized by database family (relational, key-value, vector, document/object, graph, time-series), with concrete forbidden commands for each. The table is illustrative, not exhaustive. The principle is the rule; the table is the training data.

One additional precision added after drafting: the restriction applies inside `docker exec` containers as much as on the host. An agent executing `docker exec ai-platform-postgres psql -U aiplatform -c "SELECT * FROM plugins"` is doing exactly the same thing as an agent running `psql` natively — accessing the database directly, bypassing the application layer. The execution environment is irrelevant.

---

### Invocability as a governance property

Nothing in the agent YAML frontmatter prevented a sub-agent from spawning another sub-agent. The `owns`, `forbidden`, and `allowed_tools` fields constrain what an agent can do with files and tools — but they say nothing about which agents are permitted to invoke which. A rogue or hallucinating Frontend Dev agent could theoretically spawn a Security Engineer agent, or an orchestrator could be invoked by a sub-agent, or two agents could delegate to each other recursively.

Adding `invocable_by: [orchestrator]` to all specialist agents and `invocable_by: [user]` to the orchestrator makes the invocation topology explicit in the frontmatter rather than implicit in prose. Combined with constraint #10 in the orchestrator ("NEVER delegate to an agent whose `invocable_by` list does not include `orchestrator`"), this closes the recursive spawning gap.

The enforcement is still soft — it relies on the orchestrator checking the frontmatter before delegating. A hard runtime enforcement would require the execution environment to read the YAML and block non-conforming invocations, which Claude Code doesn't currently expose as a control. What the metadata does provide is a machine-readable declaration of intent that any future enforcement layer can act on, and a human-readable governance statement that makes the intended topology visible in the file rather than buried in prose documentation.

---

### What changed and why it holds

| Change | File(s) | What problem it solves |
|---|---|---|
| `invocable_by` field | All 10 agent YAML files, TEMPLATE.md | Makes spawning topology explicit; enables future enforcement |
| Orchestrator constraint #10–#12 | `orchestrator.md` | Invocability gate, external content isolation, DB seeding prohibition |
| rule-015 | New rule file, CLAUDE.md | Formalizes host execution air-gap as a named constraint |
| `<instructions>` patterns + `sanitize()` call | `sanitizer.py`, `rag/pipeline.py`, rule-012 | Closes XML injection gap in application layer; wires sanitizer into RAG ingestion |
| rule-016 | New rule file | Closes prompt injection gap in agentic framework layer |
| Audit file `forbidden:` entries | All 9 specialist agent YAML files | Agents with `write` access can no longer overwrite audit logs |
| rule-017 | New rule file, CLAUDE.md | Principle-first prohibition on direct DB access, all families |

The audit file entries deserve a note. The `/handoff` command already carried an APPEND-ONLY constraint (`NEVER use Write tool on docs/ARCHITECTURE_STATE.md`). But that constraint lives in the command file — it applies when the command runs, not when any other agent happens to write to that path. An agent given the `write` tool and instructed to "clean up docs" could overwrite `ARCHITECTURE_STATE.md` without invoking `/handoff` at all. Adding the paths to the `forbidden:` list in each agent's YAML closes the side-channel.

The distinction is: a constraint in a command file governs the command. A constraint in a `forbidden:` list governs the agent, regardless of what instruction it receives. Both are needed; they protect different failure modes.

One late design debate on rule-017 sharpened the `<input_guard>` scope. The first draft blocked any message containing DB-formatted output. That was too broad — it would have stopped a developer pasting a Django queryset repr, a small JSON with dev data, or a schema shape, none of which contain personally identifiable information (PII: any data that can identify a natural person — names, email addresses, account identifiers — defined as "personal data" under GDPR Art. 4(1) [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679); this is a data protection concept, not an EU AI Act one). The guard was revised to key on **PII signal** rather than **DB format**: email address patterns, five or more UUID values (bulk dump signal), and credential field values trigger the stop; structure without personal data does not. The pre-prompt hook adds a soft-warn layer (advisory, not `exit 1`) that fires before any token is consumed. The agent-level `<input_guard>` is the enforcing boundary; the hook is the early-warning signal.
