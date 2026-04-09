← [Back to DEVLOG index](../DEVLOG.md)

## Entry 22 — Machine-First Notation: From Memory to Format

**Date:** 2026-04-07 · **Plan:** `woolly-coalescing-hellman.md`

### The benchmark passed

Entry-21 predicted the fix would work. It did.

Same task, same agent type (debugger), new session with rule-004 loaded:

| Metric | Baseline | Post-memory | Post-rule-004 |
|---|---|---|---|
| Total tokens | 38,896 | ~39,500 | **32,498** |
| `list_memories` called first | No | Yes | **Yes** |
| AI_REFERENCE.md read | Yes | Yes | **No** |
| Tool calls | — | 5 | 5 |

The agent called `list_memories`, read `testing/workflow`, `testing/conftest-fixtures`, `suggested_commands`, and `architecture/stack` — and stopped. Never touched AI_REFERENCE.md. −6,398 tokens vs baseline (−16%).

### The next problem: AI_REFERENCE.md itself

The benchmark validated that agents skip AI_REFERENCE.md when memories cover the task. But AI_REFERENCE.md is still ~1,743 tokens when it *is* read — for env vars, health endpoints, volume mounts. And CLAUDE.md is ~1,500 tokens of rules loaded every session, much of it verbose prose preambles around dense code blocks.

The question became: can we apply machine-first notation (optimized for LLM parsing, not human readability) to reduce the two-file system by ~50%?

Reference: [QBE Spec v7](https://marow.ai/research/qbe-spec-v7.md) — a 39KB technical spec designed for LLM consumption. Key patterns: pipe-delimited inline lists, `name:value(type)[default]` notation, no transitional prose, abbreviation legend upfront, dimensional tuple notation for multi-attribute entries.

### What changed

**`docs/AI_REFERENCE.md`** — full rewrite, 162 lines → 15 lines (~91% reduction):

- Removed: Stack table (in `architecture/stack` memory), Test Commands (in `testing/workflow` memory), Persistent Memory prose
- Merged: Services & Ports + Health Check Endpoints → single `## SVCS` line: `api:8000→/health(200) | pg:5432→pg_isready | ...`
- Compressed: all remaining tables → pipe-delimited inline lists
- Format: `svc:port→health-path(expected) | K:V(type)[default] | (ai-tools)=docker-compose.ai-tools.yml`

**`CLAUDE.md`** — 11 targeted edits (~47% reduction):

- R1–R4 rule labels: 4-line prose blocks → single directive lines with `❌`/`^R` notation
- Part 2 paradigm preambles compressed; numbered steps kept verbatim (load-bearing for agent compliance)
- Abbreviation legend added: `<!-- R=Read G=Grep Gl=Glob E=Edit B=Bash S=Serena | ^=exception -->`
- Part 4 reference table: verbose "Purpose" column → terse "When to load"
- Hard Rule 5.2 (model IDs): **not compressed** — `claude-haiku-4-5-20251001` and `claude-sonnet-4-6` remain verbatim; prior incident confirmed silent spawning failures when omitted

**`.claude/commands/init-ai-reference.md`** — updated to generate the new format:

- Step 0 added: call `list_memories` before scanning; skip sections already in memories
- `<output_format>` replaced with machine-first notation template (≤200 token target)
- Constraint 5 added: no Markdown tables, no prose, pipe-delimited only

**`.claude/skills/speed2-workflow/SKILL.md`** — line 14 fixed:

- Before: `Read docs/AI_REFERENCE.md — ground truth for stack, ports, make targets`
- After: `Call mcp__serena__list_memories → read suggested_commands + architecture/*. Fall back to docs/AI_REFERENCE.md only for env vars, health endpoints (rule-004).`
- This was a stale reference that would have sent every Speed 2 session directly to AI_REFERENCE.md unconditionally, negating the memory-first savings.

### Token economics

| File | Before | After | Reduction |
|---|---|---|---|
| `docs/AI_REFERENCE.md` | ~1,743 | ~170 | ~91% |
| `CLAUDE.md` | ~1,500 | ~790 | ~47% |
| **Combined** | **~3,243** | **~960** | **~71%** |

The AI_REFERENCE reduction is dominant. CLAUDE.md is conservative by design — security-critical rules (model IDs, FILE-INJECT logic, tenant isolation) were left verbose because compression risk > token gain.

### The conservative line on CLAUDE.md

The planner flagged a real tension: machine-first notation is ambiguous at low model capability. The `svc:port→health-path(expected)` format uses three delimiter characters simultaneously. A Haiku agent under context pressure could misparse it.

Mitigation is two-layer: the notation legend on line 2 of AI_REFERENCE.md acts as a parsing schema, and the next session should run a Haiku-specific parse test before treating the format as production-ready.

Same principle for CLAUDE.md: Rule 2 (explicit model IDs) was the one rule that must remain verbose. Every other rule is either hook-enforced (R1), implicit from the code block (R2 flags), or low-enough-stakes to compress. But "which model ID" is a decision agents make at delegation time with no fallback — a wrong ID produces a broken agent spawn with no error message. The two lines that name those IDs are load-bearing in a way that table headers are not.

### The discovery about speed2-workflow

The plan agent caught that `speed2-workflow/SKILL.md` line 14 contradicted rule-004. This is the kind of cross-file consistency failure that normally surfaces as a mysterious regression: the memory-first savings appear in benchmarks, then disappear in Speed 2 sessions, and no one knows why.

The fix was one line. The detection required reading a file that wasn't on the original change list. Both are reminders that governance files drift against each other if there's no system-level consistency check — and that planning agents are useful precisely because they read laterally, not just at the target files.
