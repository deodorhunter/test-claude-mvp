## 🔬 Research Synthesis + Impact Analysis

Sources:

- <https://claudelog.com/mechanics/ultrathink/>
- <https://claudelog.com/mechanics/bash-scripts/>
- <https://claudelog.com/mechanics/context-window-depletion/>
- <https://claudelog.com/mechanics/tactical-model-selection/>
- <https://claudelog.com/mechanics/sub-agent-tactics/>
- <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- <https://github.com/NeoLabHQ/context-engineering-kit>
- <https://github.com/NeoLabHQ/context-engineering-kit/tree/master/plugins/customaize-agent/skills>

### What each source actually teaches us

| Source | Core Mechanic | Token Cost | Complexity |
|---|---|---|---|
| **Ultrathink** | Trigger word → extended thinking in Sonnet. Alt to Opus for complex reasoning. Combine with Plan Mode + iterative critique ("revving"). | ~0 extra tokens for the trigger. Thinking tokens are extended. | Low to add |
| **Bash Scripts** | Batch multiple file writes into a single tool call via JSON-driven bash. Eliminates sequential Edit overhead for multi-file changes. | Reduces O(n) API round trips to O(1) | Medium to implement |
| **Context Window Depletion** | Avoid last ~20% of context window for memory-intensive tasks. Proactive checkpointing beats reactive recovery. Disable unused MCP servers. | Saves 10k–40k tokens per session if respected | Low to add (docs) |
| **Tactical Model Selection** | Haiku 4.5 = 90% of Sonnet agentic capability at 3× lower cost. Sonnet orchestrator + Haiku workers = 2–2.5× overall savings. Opus 4.6 has 1M context. | Strategic: up to 80% savings | Low (matrix tweak) |
| **Sub-agent Tactics** | Classify tasks as **destructive** vs **non-destructive** before parallelising. "Consolidate → /clear → Action" between parallel waves. Explicit agent count control. | Prevents runaway parallel agents | Low (wording) |
| **Anthropic Skills spec** | YAML frontmatter (`name` + `description`). Progressive disclosure: metadata always loaded, SKILL.md on trigger, extra files on demand. Concise is non-negotiable. Skills = portable across Claude Code, Cursor, OpenCode. | Reduces per-invocation context overhead | Medium to retrofit |
| **NeoLab CEK** | Plugin architecture for skills. Rich patterns: SDD, Reflexion (/memorize → CLAUDE.md), SADD (do-and-judge, competitive gen), FPF (hypothesis → evidence → decision). | Adds overhead if installed wholesale | High, cherry-pick only |
| **NeoLab Skills dir** | 13 meta-skill categories. Notable: `thought-based-reasoning`, `context-engineering`, `agent-evaluation`, `create-workflow-command`. Shows what mature skill libraries look like. | Reference architecture | Reference only |

---

## ✅ HELPS — What to adopt and why

### 1. YAML frontmatter on all `.md` governance files *(implement now)*

The Anthropic Skills spec requires it. More importantly for our 40-project goal: YAML makes our framework **machine-readable and portable** across Claude Code, Cursor, OpenCode. It also serves as the **canonical routing metadata** — the Tech Lead can read `parallel_safe: true` and `requires_security_review: true` directly from agent YAML instead of parsing prose.

**What we gain:** Portability, structured routing metadata, compatibility with skill registries.

### 2. `ultrathink` keyword for HIGH-complexity tasks *(implement now)*

It's free — just a word prepended to the prompt. The claudelog source is clear: this triggers extended thinking in Sonnet without paying Opus prices. It should live in our Task Complexity Matrix as a directive: *when delegating a HIGH complexity US on Sonnet, prepend `ultrathink` to the agent's system prompt.*

**Important caveat:** `ultrathink` is effective with Sonnet, not Haiku. LOW complexity tasks stay Haiku, no ultrathink.

### 3. Proactive context budget threshold *(implement now)*

Right now our `/compress-state` is **reactive** (user notices degradation and calls it manually). The claudelog article gives a concrete signal: the last ~20% of the context window is danger territory for memory-intensive work. We should add a **proactive trigger rule** to CLAUDE.md: after 15+ tool calls or if the agent observes its reasoning is fragmenting, it must self-trigger a checkpoint, not wait to fail.

### 4. Destructive/Non-destructive task classification before parallelism *(implement now)*

Our current parallelism rule says "different file domains → parallel." The sub-agent tactics article adds a more fundamental prior question: **is this task destructive (modifies shared state) or non-destructive (reads + analysis only)?** Non-destructive tasks can always parallelize safely. Destructive tasks need the domain isolation check first. This is a small wording change to `workflow.md` that prevents an entire class of race-condition bugs.

### 5. "Consolidate → /clear → Action" between parallel agent waves *(implement now)*

When we spawn 2–3 parallel implementing agents for a phase, we currently chain directly to the next step as each one finishes. The correct pattern is: **collect all results from the wave, run `/compress-state`, clear context, then action the consolidated findings from a fresh context window.** This prevents the context from being polluted by half-finished parallel threads.

### 6. Opus 4.6 tier for 1M-context use cases *(add to matrix, discuss)*

Our matrix currently has two tiers: Haiku (LOW) and Sonnet (HIGH/MEDIUM). The research shows Opus 4.6 has a **1M token context window** — qualitatively different from Sonnet's 200K. There's a specific niche where this matters: Phase Gate reviews where we need ALL US handoffs loaded simultaneously, or Security Reviews over the entire codebase. This warrants a third tier in the matrix.

---

## ⚠️ NEUTRAL — Cherry-pick, don't wholesale adopt

### 7. NeoLab's **Reflexion → /memorize** pattern

Their `/reflexion:memorize` command extracts insights from a session and appends them to CLAUDE.md. **This is genuinely good,** but rather than adopting their command, we should build it into our **DocWriter Mode B**: after each phase gate, DocWriter extracts a "Lessons Learned" paragraph and appends it to a section in `CLAUDE.md`. No new command needed — it's an extension of existing DocWriter responsibilities.

### 8. NeoLab's **SADD /do-and-judge** pattern → our `/judge` command

Their "execute with verification loop" concept maps well onto our workflow gap: after implementation but before DocWriter+QA, a lightweight Haiku judge reads the git diff and checks it against the acceptance criteria. ~2,000 tokens. This **would reduce QA bounce-backs** because obvious AC failures get caught earlier. Worth creating as an optional command.

### 9. Batch bash scripts for multi-file agents

For US that touch 5+ files, a JSON-driven batch script reduces tool call overhead. **However**, our agents already use the `Edit` tool (targeted, not full rewrites), so the gain is mostly latency (API round trips), not tokens. Worth documenting as an optional pattern in TEMPLATE.md, but not worth mandating.

### 10. Progressive disclosure for agent files

Currently our agents are 50–100 lines. They're already lean. Progressive disclosure (SKILL.md + domain/ sub-files) would only pay off if agents grew to 200+ lines. **Monitor, don't act yet.**

---

## ❌ HINDERS — Do not adopt

### 11. Installing NeoLab CEK as a package

Their SDD plugin defines its own: Tech Lead workflow, agent roles (researcher, business-analyst, team-lead…), quality gates, and commands namespace (`/sdd:`, `/git:`, `/reflexion:`). **This directly conflicts** with our custom framework. The Tech Lead would receive two competing sets of orchestration instructions and route incorrectly. **Risk: very high, benefit: zero (we already have equivalents).**

### 12. Mandatory Tree-of-Thoughts / FPF as standard

Both patterns produce excellent reasoning but at **high token cost** (3–5× normal planning tokens). They're appropriate for genuinely ambiguous architectural decisions, not standard US implementation. Making them mandatory would defeat our entire token optimization work. **Use ultrathink instead** — it achieves similar depth at a fraction of the cost.

### 13. LLM-as-Judge on every US

Running a dedicated "judge" evaluation after every US adds ~5,000–10,000 tokens and one full agent invocation per US. At 35 US in our backlog, that's 175,000–350,000 extra tokens for marginal QA improvement over our existing human-in-the-loop checkpoints. **Only use the judge pattern for security-critical or architecturally-critical US.**

### 14. DDD 15 composable rules

Their Domain-Driven Development rules overlap heavily with our agent file domain boundaries. Adding them would create rule conflicts. Not needed.

Good questions. Let me answer all three precisely before implementing, because they all connect.

---

## Rules vs Skills

Appending "lessons learned" prose to `CLAUDE.md` is architecturally wrong for one simple reason: **CLAUDE.md is always-loaded**. Every token you add to it costs you in every single session, forever. That's the opposite of what we want.

The correct two-layer architecture:

```
.claude/
  rules/              ← behavioral constraints (always active, but discrete files)
    org/              ← promoted to org plugin when ready
    project/          ← discovered during this project's sessions
  skills/             ← reusable procedures (loaded on demand)
  agents/             ← already have this
  commands/           ← already have this
```

**Rules** = `"never do X"`, `"always check Y before Z"`. Small, focused, actionable constraints. One rule per file.

**Skills** = `"how to perform operation Z"`. Our agents and commands already serve this role.

**The key mechanic:** In Claude Code, `CLAUDE.md` supports `@path/to/file.md` imports. So `CLAUDE.md` stays a **lean index** — it only imports the rules currently active on this project:

```markdown
## Active Project Rules
@.claude/rules/project/rule-001-tenant-isolation.md
@.claude/rules/project/rule-002-no-raw-redis-timeout.md
```

When a rule is no longer needed, delete the import. When a rule is valuable org-wide, move it to `org/` and promote it to the plugin. **CLAUDE.md itself never grows** — only the import list changes.

---

## Reflexion — Honest Token Math

You're right to push back. Let me be precise about where the value is and isn't.

**What Reflexion does NOT do:** save tokens in the *current* session. Running it costs ~3,000 tokens.

**What it DOES do:** prevent a class of future token waste by converting a session failure into a permanent rule. Here's the math:

```
One debugging loop that hits the circuit breaker:     ~15,000 tokens wasted
One "wrong architectural approach" caught at QA:      ~25,000 tokens wasted (full cycle)

Cost of a Reflexion rule:
  - Running /reflexion once:                          ~3,000 tokens
  - Loading the rule in future sessions:              ~200 tokens/session

Break-even: The rule prevents ONE debugging loop in its first 5 sessions.
```

**The real leverage is cross-project.** A rule discovered in Project 1 that prevents the same mistake in Projects 2–40 = 39× token savings on zero additional effort. That's where the compounding happens.

**BUT — rule bloat is a real risk.** If you run Reflexion after every US, you accumulate dozens of rules, each taxing every future session with ~200 tokens of context overhead. The rules start costing more than they save.

**The right cadence:** run `/reflexion` once at each **phase gate** (not per US). That's ~5 runs per project lifecycle. Each run should produce at most 1–3 rules worth keeping. Rules that are session-specific noise get discarded. Only rules that meet this bar survive:

> *"If an agent had known this rule from the start, would it have saved at least one circuit breaker trigger?"*

If yes → save it. If no → discard it. The `/reflexion` command should enforce this bar explicitly.

---

## Q3: Plugin Architecture Path

Our current file structure is already plugin-ready. Here's the phased path:

```
Phase 1 (now):    git template repo — fork + /init-ai-reference
Phase 2 (soon):   .claude/commands/ as a git submodule across all 40 repos
Phase 3 (later):  .claude-plugin/ manifest — marketplace-ready plugin
```

The key insight: **only `docs/AI_REFERENCE.md` is project-specific**. Everything else in `.claude/` is org-generic and belongs in the plugin. The plugin installs the generic kit; the project overrides only what's different.

Let me implement all of this now.