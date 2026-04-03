← [Back to DEVLOG index](../DEVLOG.md)

## Entry 18 — Phase 3 Complete: The First Real Cost Benchmark and What the JSONL Revealed — 2026-04-03

> Phase 3d closed with something the framework had never had before: a live measurement of what a session actually costs, down to the dollar, with cache ratios, drift signals, and a direct comparison against our hand-written estimates. The number was surprising. The gap was instructive.

---

### What happened this session

Phase 3d implemented six User Stories across two parallel waves:

**Wave 1 (three agents in parallel):**
- US-061: MODEL_COMPARISON.md — Claude API vs Copilot vs local Ollama, seven comparison dimensions. Required mid-flight correction: the Doc Writer agent trusted its training cutoff on Qwen3 availability instead of running the WebSearch step in the acceptance criteria. WebFetch confirmed qwen3:8b, qwen3:14b, and qwen3-coder:30b are all live on Ollama today.
- US-062: Plone architecture clarification — module docstring on plone_bridge.py, Architecture Note in plone-mcp README, ASCII diagram in ARCHITECTURE_STATE.md showing the four Plone touchpoints and their data flows.
- US-069: Session cost capture — `benchmark/capture-session-metrics.sh`, `benchmark/report-session-costs.sh`, two new Makefile targets (`make benchmark-session`, `make benchmark-report`), gitignore entries. A path key bug was found post-implementation: Claude Code uses a leading `-` for the project directory (`-Users-martina-…`) but the script stripped it. Fixed with a one-line sed swap.

**Wave 2 (two agents in parallel):**
- US-063: Competitive analysis — "OpenClaw" does not exist as a standalone framework. Searches of GitHub confirm it is a webhook relay integration inside oh-my-claudecode, routing session events to an external HTTP endpoint (Discord via Clawdbot). The competitive analysis was written against oh-my-claudecode (22.8k stars, MIT, Princeton/Stanford team), which is the framework the user almost certainly intended.
- US-070: Accuracy scoring — `benchmark/report-accuracy.sh`, `make benchmark-accuracy`, and an `<accuracy_logging>` section appended to `.claude/commands/judge.md` so that every future `/judge` run appends a structured JSON line to `benchmark/accuracy-log.jsonl`. The Doc Writer agent documented the judge.md edit rather than making it. The Tech Lead applied it directly.
- US-064: SWE-agent evaluation — CONDITIONAL GO verdict for mini-swe-agent + custom harness hybrid. mini-swe-agent is technically compatible (Python 3.10+, Claude via LiteLLM, free-form task strings, MIT licensed) but needs a custom wrapper for governance-domain benchmarking. Evaluated as Phase 4 MEDIUM effort.

After all six US passed judge, Phase Gate 3 ran. /reflexion found zero durable patterns — the two Phase 3d incidents (Qwen3 verification, judge.md edit) were one-time corrections, not systemic failures. No new rules were extracted.

---

### The benchmark

The framework now measures real session cost from Claude Code's session JSONL instead of estimating it. The JSONL lives at `~/.claude/projects/-Users-martina-personal-projects-test-claude-mvp/<session-id>.jsonl`. Each assistant entry carries a `message.usage` object with four token fields: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`.

Running `make benchmark-session` on the current session produced:

| Metric | Value |
|---|---|
| Claude Code version | v2.1.91 |
| Input tokens (raw, non-cached) | 405 |
| Output tokens | 54,554 |
| Cache creation tokens | 1,493,258 |
| Cache read tokens | 16,638,201 |
| Cache read ratio | 91% overall / 100% late-session |
| Estimated cost | **$11.41** |
| Drift signals | 0 |

The session ran on v2.1.91, which the ArkNill claude-code-cache-analysis investigation confirmed as the fixed version: the Sentinel bug (Bun runtime corrupting cache prefixes, reducing read ratios to 4-17%) and the Resume bug (--continue replaying entire conversations as billable input) are both patched here. The 91% cache read ratio confirms the cache is healthy.

---

### The gap: $11 vs $78

SESSION_COSTS.md logged this phase as "~78k avoidable tokens" with a total estimate that implied a much higher cost. The actual cost was $11.41. The gap is not an error — it is a unit problem.

The estimates were denominated in tokens, treated as if all tokens cost the same. They do not. The token cost breakdown for this session:

| Token type | Count | Rate | Cost |
|---|---|---|---|
| Cache read | 16,638,201 | $0.30 / 1M | $4.99 |
| Cache creation | 1,493,258 | $3.75 / 1M | $5.60 |
| Output | 54,554 | $15.00 / 1M | $0.82 |
| Input (raw) | 405 | $3.00 / 1M | $0.00 |
| **Total** | | | **$11.41** |

Without the prompt cache — if every cache read token had been billed as a raw input — the cost would have been $50.07. The cache saved $38.66 in this session alone. All of the Phase 3 work on rule compression, agent-scoped injection, and context optimization reduced cache creation costs at the margin. The prompt cache itself is the primary cost control mechanism.

The implication for SESSION_COSTS.md: token counts are a proxy for cost, but a poor one when cache ratios vary. Phase 4 will track dollar estimates directly.

---

### The drift signal false positive

The benchmark script was measuring drift by checking whether `toolUseResult` content was shorter than 100 characters — the Budget Cap bug signal identified in the ArkNill report. The initial run showed 95.2% of tool results as "short." Investigation showed the measurement was wrong.

The `toolUseResult` field in the JSONL is a JSON object for most tool types (Glob, Read, Bash, Edit), not a plain string. Measuring `string_length` on these returned 0. After correcting to serialize the full object (`tojson | length`), the real rate was 22.6% — and investigation of those 24 entries showed they were all legitimate: tool metadata objects (`{"filenames":[],...}`), skill invocation results (`{"success":true,"commandName":"judge",...}`), and one user rejection. No genuine Budget Cap truncations were found.

The drift signal metric needs recalibrating. The correct signal for the Budget Cap bug is the `truncated: true` flag in Glob and Read responses — not content length. This is tracked as US-072.

---

### AI_REFERENCE.md: the silent bloat

The context size benchmark revealed a secondary finding. AI_REFERENCE.md, which loads on every session, grew from 5,447 bytes (1,362 tokens) at Phase 3a to 18,821 bytes (4,705 tokens) today — a 245% increase. The growth came from three sections added across Phase 3: the model routing matrix (US-051), the orchestration patterns guide (US-053), and the context management section (US-056).

Each of these additions was correct for the session that requested them. Collectively they turned the stack reference into an orchestration manual. The two have different audiences: stack reference needs to be read at every session start (rule-004); orchestration patterns are consulted when planning delegation, not on every turn.

The fix is structural: keep AI_REFERENCE.md as the compact stack/ports/commands/test-commands reference (rule-004 compliance), and move the orchestration patterns and model routing into a separate `docs/ORCHESTRATION_GUIDE.md` loaded on demand. Estimated saving: ~3,000 tokens per session. This is tracked as US-071.

---

### What Phase 3 delivered overall

Across 4 sub-phases and 22 User Stories (plus 6 added in 3d), Phase 3 built the governance layer that Phase 2 could not have: backlog refinement to catch yes-man US before implementation, backlog-scoped rule injection to prevent agent context bloat, cognitive tools (judge, reflexion, phase-retrospective, notepad, learn) as first-class commands, copy-first adoption path, competitive analysis, and now a live cost measurement infrastructure. The framework that existed at Phase 2d gate was capable but opaque. The framework at Phase 3 gate is measurable.

The two rules that survived the full 4-phase filter: rule-007 (Phase Gate mandatory) and rule-018 (pre-sprint backlog refinement). Both address the same root cause — the orchestrator's tendency to treat process steps as optional when the cost of skipping feels low in the moment and the cost only becomes visible in retrospect.

---

### Session notes

**Incidents:**
- US-061: Doc Writer relied on training cutoff for Qwen3 status. AC said "verify against ollama.com." Fixed by Tech Lead via WebFetch. Rule not extracted (one-time factual verification, not a systemic pattern).
- US-070: Doc Writer created an instruction document instead of editing judge.md directly. Fixed by Tech Lead. Rule not extracted (agent uncertainty on a specific file, not a domain-wide pattern).
- `capture-session-metrics.sh` path key bug: `sed 's|^-||'` stripped the leading `-` from the Claude project directory name. Fixed by swapping sed order.

**Tools that worked well:**
- Parallel wave execution (Wave 1: 3 agents, Wave 2: 2 agents) — all completed without conflicts.
- `/judge` on all 6 US before commit — caught no FAILs, confirmed UNCLEARs are runtime-only.
- `make benchmark-session` on first real run produced actionable data immediately.

**Version confirmation:** v2.1.91 is safe. Cache ratio 91% confirms the Sentinel bug is not present. The Resume bug (avoid `--resume`/`--continue`) remains unfixed in this version but is not relevant to our workflow (we start fresh sessions).
