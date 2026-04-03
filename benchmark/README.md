# Token Optimization Benchmark

Reproducible benchmark for measuring Claude Code token usage per request.
Target: **35%+ reduction** in auto-loaded context and per-agent injection overhead.

---

## Quick Start

```bash
# Measure baseline (before optimizations)
./benchmark/measure-context-size.sh baseline

# Apply optimizations (strategies S1-S5), then:
./benchmark/measure-context-size.sh optimized

# Compare results
./benchmark/compare.sh

# Measure per-agent injection overhead
./benchmark/measure-agent-injection.sh

# Sample tool output sizes (before/after truncation hook)
./benchmark/measure-tool-output.sh
```

---

## What We Measure

| Metric | Script | Unit |
|---|---|---|
| Auto-loaded context size | `measure-context-size.sh` | bytes + estimated tokens |
| Per-agent rule injection | `measure-agent-injection.sh` | bytes per agent type |
| Tool output bloat | `measure-tool-output.sh` | lines before/after truncation |
| Cache hit ratio | Parse session JSONL `cache_read_tokens` | % |

### Token Estimation

We use the standard approximation: **1 token ~ 4 bytes** for English text / code.
This is consistent with Anthropic's tokenizer for Claude models.

---

## Optimization Strategies

### S1: Output Truncation Hook (PostToolUse) — ~10% savings

**Problem:** `pip install`, `docker build`, `alembic upgrade`, `npm install` outputs flood 500-5000 tokens into context. Only the exit code and last few lines matter.

**Solution:** A `PostToolUse` hook (`.claude/hooks/post-tool-truncate.sh`) that intercepts Bash tool results and truncates known noisy patterns to the last 5-10 lines with a summary header.

**Inspired by:** oh-my-claudecode's `PostToolUse` verifier hook and `PreCompact` context guard.

**Verification:**
```bash
# Before hook: run a docker build, count output lines
docker build -q . 2>&1 | wc -l   # typically 50-200 lines

# After hook: same command through Claude, output should be ≤10 lines
./benchmark/measure-tool-output.sh
```

### S2: Rule Compression — ~8% savings

**Problem:** 11 rule files total 17.4 KB (~4,300 tokens). Each contains verbose historical context, multiple examples, and incident narratives that served as learning material but are redundant at runtime.

**Solution:** Compress each rule to a "compact" format:
- `## Constraint` — the actual rule (1-3 sentences)
- `## Why` — 1 line motivation
- `## Pattern` — 1 correct example only

Archive verbose originals to `.claude/rules/archive/` for reference.

**Target:** 17.4 KB → ~7 KB (~1,750 tokens). Savings: ~2,550 tokens per conversation turn.

**Verification:**
```bash
./benchmark/measure-context-size.sh optimized
# Compare "Rules total" line: should be ≤7,500 bytes
```

### S3: Agent-Scoped Rule Injection — ~12% savings

**Problem:** Every sub-agent inherits all 11 rules (~4,300 tokens) via the system prompt, but a DocWriter only needs rule-005 and a Frontend Dev only needs rule-001. Over 6 agents in a phase: 6 × ~3,500 wasted = ~21,000 tokens.

**Solution:** Rule routing table in `orchestrator.md`. When building agent prompts, inject only relevant rules as inline `<rules>` XML blocks instead of relying on system-prompt inheritance.

| Agent | Rules Needed | Tokens (est.) |
|---|---|---|
| Backend Dev | 001, 002 | ~500 |
| AI/ML Engineer | 001, 011 | ~500 |
| Security Engineer | 001, 011 | ~500 |
| DevOps/Infra | 008 | ~200 |
| DocWriter | 005 | ~200 |
| QA Engineer | 005, 006 | ~300 |
| Frontend Dev | 001 | ~200 |

**Inspired by:** oh-my-claudecode's "lightweight path preference" — match context weight to task needs.

**Verification:**
```bash
./benchmark/measure-agent-injection.sh
# Each agent type should show ≤500 tokens of rule injection
```

### S4: Symbols-Only Context Injection — ~8% savings

**Problem:** When injecting file context into agent prompts, full `<file>` blocks cost ~2,000 tokens per file. Agents that only need to *call into* a module (not modify it) waste ~1,800 tokens per file.

**Solution:** Decision criteria in orchestrator delegation:
- **Will the agent MODIFY this file?** → inject as `<file>` (full content)
- **Will the agent only CALL INTO this file?** → inject as `<symbols>` (Serena overview, ~200 tokens)

For 5 files injected per agent where 3 are call-only: 3 × 1,800 = 5,400 tokens saved per agent.

**Inspired by:** oh-my-claudecode's Deep-Executor research showing 2-3x efficiency from targeted context loading.

**Verification:**
```bash
# Compare injection sizes for a typical US delegation prompt
./benchmark/measure-agent-injection.sh --detail
```

### S5: CLAUDE.md Deduplication — ~5% savings

**Problem:** CLAUDE.md Part 5 "Hard Rules" (18 rules) largely duplicates `orchestrator.md` constraints. The rules README duplicates the rule file format. ~2,500 bytes of redundancy loaded on every turn.

**Solution:** Slim CLAUDE.md Part 5 to a 3-line pointer: "See orchestrator.md for full constraint list." Remove workflow duplication already covered by `@.claude/workflow.md`.

**Verification:**
```bash
./benchmark/measure-context-size.sh optimized
# Compare "CLAUDE.md" line: should be ≤4,500 bytes (from 6,129)
```

---

## Patterns Adopted from oh-my-claudecode

These patterns from [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode) are adopted in our framework, filtered through EU AI Act compliance (rule-011).

### Adopted Patterns

| Pattern | OMC Source | Our Implementation | Impact |
|---|---|---|---|
| **Output truncation hooks** | `PostToolUse` verifier + `PreCompact` guard | `.claude/hooks/post-tool-truncate.sh` (S1) | ~10% token savings |
| **Smart model routing** | Model right-sizing (Haiku/Sonnet/Opus) | Task Complexity Matrix in `product-owner.md` | 30-50% cost savings |
| **Bounded iteration** | Fix loops bounded by max attempts | Rule 4: Circuit Breaker (max 2 attempts) | Prevents runaway consumption |
| **Evidence-driven verification** | `trace` lane for evidence collection | Smoke tests + QA Mode A in orchestrator | Quality gate |
| **Authoring/review separation** | `code-reviewer` / `verifier` agents | Hard Rule 17: never self-approve | Prevents self-approval bias |
| **Context compression** | `PreCompact` hook + session state | Rule 10: `/compress-state` before parallel waves | ~240k savings per wave |
| **Sequential over parallel (simple tasks)** | Deep-Executor research (2-3x efficiency) | Agent-scoped rules reduce per-agent overhead (S3) | ~12% savings |
| **Tool call batching** | Multiple Glob/Grep/Read in single turn | Already enforced by Rule 5 (bulk reading) | Reduces round-trips |
| **Background processing** | `run_in_background` for builds/tests | Available but underused — now documented | Frees active context |
| **Commit decision trailers** | `Constraint:`, `Rejected:`, `Directive:` | Not yet adopted — low priority | Decision traceability |
| **Exploration budgeting** | Cap tool calls before analysis | Rule 4 circuit breaker + Rule 10 compress | Prevents context bloat |
| **Task complexity classification** | SIMPLE/MEDIUM/COMPLEX tiers | Task Complexity Matrix (LOW/MEDIUM+HIGH/OPUS) | Right-sized reasoning |

### Rejected Patterns (EU AI Act Non-Compliant)

| Pattern | OMC Feature | Reason for Rejection | Rule |
|---|---|---|---|
| Session replay sync | `.omc/state/*.jsonl` external sync | GDPR Art. 5(1)(e) storage limitation | rule-011 |
| Plugin marketplace | Public skill marketplace | Art. 9 supply chain risk | rule-011 |
| External notifications | Discord/Slack/Telegram hooks | GDPR Art. 46 data transfers | rule-011 |
| Autopilot mode | Autonomous execution without stops | Art. 14 human oversight | rule-011 |
| Multi-provider auto-routing | Cheapest-provider routing (Gemini, Codex) | Art. 46 no DPA with providers | rule-011 |
| Mutable session logs | `.omc/sessions/*.json` | Art. 12 tamper-proof logging required | rule-011 |

### Selectively Adopted (Local-Only, Modified)

| Pattern | OMC Feature | Our Modification |
|---|---|---|
| **Notepad wisdom** | `.omc/notepad.md` persistent notes | `docs/.session-notes.md` (gitignored, local only) via `/notepad` skill |
| **Critic agent** | Pre-implementation challenge | Critic agent in orchestrator (MEDIUM/HIGH US only) |
| **Atomic changes** | Small, focused commits | Git branching per US + merge after QA |
| **HUD statusline** | Real-time token/cost display | Not yet adopted — evaluate after benchmark |

---

## Benchmark Results

### Baseline (pre-optimization) — 2026-03-30

```
CLAUDE.md:              6,129 bytes  (~1,532 tokens)
orchestrator.md:        8,267 bytes  (~2,067 tokens)
product-owner.md:       4,560 bytes  (~1,140 tokens)
Rules (11 files):      17,367 bytes  (~4,342 tokens)
Rules README:           2,527 bytes  (~  632 tokens)
workflow.md:           14,188 bytes  (~3,547 tokens)
AI_REFERENCE.md:        5,447 bytes  (~1,362 tokens)
Hooks (1 file):         2,279 bytes  (~  570 tokens)
─────────────────────────────────────────────────────
TOTAL AUTO-LOADED:     60,764 bytes  (~15,191 tokens)
```

### Optimized (post-optimization) — 2026-03-30

```
CLAUDE.md:              4,415 bytes  (~1,103 tokens)  -28%
orchestrator.md:        8,730 bytes  (~2,182 tokens)  +6% (added S3/S4 routing tables)
product-owner.md:       4,042 bytes  (~1,010 tokens)  -11%
Rules (11 files):       4,944 bytes  (~1,236 tokens)  -72%
Rules README:             350 bytes  (~   87 tokens)  -86%
workflow.md:            2,103 bytes  (~  525 tokens)  -85%
AI_REFERENCE.md:        5,447 bytes  (~1,362 tokens)  (unchanged)
Hooks (2 files):        4,612 bytes  (~1,153 tokens)  +102% (new truncation hook)
─────────────────────────────────────────────────────
TOTAL AUTO-LOADED:     34,643 bytes  (~ 8,660 tokens)
```

### Comparison — 2026-03-30

```
Baseline:      60,764 bytes  (~15,191 tokens)
Optimized:     34,643 bytes  (~ 8,660 tokens)
Saved:         26,121 bytes  (~ 6,530 tokens)
RESULT:        42% reduction — TARGET MET (>=35%)
```

### Per-Agent Rule Injection — 2026-03-30

```
Across 7 agent types:
  Baseline (all rules):   34,608 bytes  (~8,652 tokens)
  Optimized (scoped):      5,771 bytes  (~1,442 tokens)
  Saved:                  28,837 bytes  (~7,209 tokens)  [83% reduction]
```

---

## File Structure

```
benchmark/
  README.md                    — this file
  measure-context-size.sh      — counts all auto-loaded context files
  measure-agent-injection.sh   — counts per-agent rule injection sizes
  measure-tool-output.sh       — samples Bash tool output sizes
  compare.sh                   — compares baseline vs optimized results
  capture-session-metrics.sh   — extracts token usage from session JSONL
  report-session-costs.sh      — prints cost summary table
  report-accuracy.sh           — prints per-phase and per-agent accuracy summary
  results/
    baseline.txt               — baseline measurement output
    optimized.txt              — post-optimization measurement output
  session-metrics/             — captured session JSON files (gitignored)
    YYYY-MM-DD-HH-MM.json      — one file per captured session
```

---

## Session Cost Capture

### What it measures

Real API token counts extracted from Claude Code session JSONL logs, compared against rough estimates in `docs/SESSION_COSTS.md`. Tracks four token categories (input, output, cache read, cache creation) plus an estimated USD cost and a drift signal count.

### Data source

Claude Code writes session logs to `~/.claude/projects/<project-path>/` on the local machine. The project path key is derived from `pwd` with `/` replaced by `-`. These files never leave the machine — fully EU AI Act (rule-011) compliant.

### Drift signal detection

The Budget Cap truncation bug manifests as a `"truncated": true` flag in Glob and Read tool responses — not as short content length. The script counts two signal types:

1. **Primary:** JSONL entries where any `content` item contains `"truncated": true` (the actual Budget Cap signal from Glob/Read responses)
2. **Secondary:** Tool result entries where `content` is a plain string shorter than 50 characters (genuine plain-text truncation)

Content length < 100 characters was a false positive: tool metadata objects (`{"filenames":[],...}`) and skill result objects (`{"success":true,...}`) are valid short responses that triggered the old metric. A healthy session shows `drift_signals_count: 0`.

### Make targets

```bash
# Capture metrics from the most recent session JSONL
make benchmark-session

# Print summary table with delta vs SESSION_COSTS.md
make benchmark-report
```

### Data location

Captured JSON files are written to `benchmark/session-metrics/` (gitignored, local only). Each file is named `YYYY-MM-DD-HH-MM.json` and contains:

```json
{
  "session_date": "YYYY-MM-DD HH:MM",
  "source_file": "~/.claude/projects/.../session-NNN.jsonl",
  "input_tokens": 12345,
  "output_tokens": 4567,
  "cache_read_tokens": 89012,
  "cache_creation_tokens": 3456,
  "cache_read_ratio_pct": 87.3,
  "estimated_cost_usd": 0.42,
  "drift_signals_count": 3,
  "note": "Cost estimated using Sonnet rates (conservative). Drift signals = truncated:true flag in Glob/Read responses (primary) + plain-string results <50 chars (secondary)."
}
```

Cost is estimated using Sonnet claude-sonnet-4-6 rates as a conservative upper bound for mixed-model sessions:
- Input: $3.00 / 1M tokens
- Output: $15.00 / 1M tokens
- Cache read: $0.30 / 1M tokens
- Cache creation: $3.75 / 1M tokens

Cache read ratio should exceed 90% in healthy sessions. Values below 80% indicate the prompt cache is not warming correctly.

---

## Accuracy Tracking

### What it tracks

Per-User Story acceptance criteria (AC) pass/fail verdicts from `/judge` runs. Enables:
- Per-phase AC pass rate trending (to detect regressions or improving agent quality)
- Per-agent-type accuracy scoring (to identify specialists vs generalists)
- Bottleneck detection (phases or agents with consistently low pass rates)
- Guidance for when to tighten AC acceptance thresholds or request re-implementation

### How it's populated

Each `/judge US-NNN` command appends one JSON line to `benchmark/accuracy-log.jsonl` with:
- `date` — YYYY-MM-DD when the judge ran
- `us` — User Story identifier (e.g., "US-070")
- `agent` — Agent type that performed the implementation (from US frontmatter)
- `ac_total` — Total AC count for the US
- `ac_pass` — Number of PASS verdicts
- `ac_fail` — Number of FAIL verdicts
- `verdict` — "pass" (all AC met or unclear) or "fail" (1+ explicit failures)
- `phase` — Phase ID (e.g., "3d") from `docs/backlog/BACKLOG.md`

UNCLEAR AC count toward `ac_total` but NOT toward `ac_pass` (conservative scoring).

### Make target

```bash
make benchmark-accuracy
```

### Data location

`benchmark/accuracy-log.jsonl` (gitignored, append-only). Each line is a valid JSON object. Example:

```json
{"date":"2026-04-03","us":"US-070","agent":"backend-dev","ac_total":5,"ac_pass":5,"ac_fail":0,"verdict":"pass","phase":"3d"}
{"date":"2026-04-03","us":"US-071","agent":"frontend-dev","ac_total":4,"ac_pass":3,"ac_fail":1,"verdict":"fail","phase":"3d"}
```

### Sample Report Output

```
## Accuracy Report — Phase Summary

| Phase | US Count | ACs Total | ACs Pass | Pass Rate | Bouncebacks |
|---|---|---|---|---|---|
| 3c | 8 | 42 | 40 | 95% | 1 |
| 3d | 12 | 68 | 64 | 94% | 2 |

## Per-Agent Breakdown

| Agent | US Count | Pass Rate | Status |
|---|---|---|---|
| backend-dev | 10 | 90% | ✅ OK |
| frontend-dev | 5 | 80% | ✅ OK |
| aiml-engineer | 4 | 75% | ⚠️ Below 80% |

## Overall Totals

- **User Stories evaluated:** 20 (18 passed, 2 failed) — 90% pass rate
- **Acceptance Criteria:** 110 total (104 passed, 6 failed) — 94% pass rate

**Last updated:** 2026-04-03
```
