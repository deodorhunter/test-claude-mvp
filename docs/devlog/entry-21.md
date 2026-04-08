← [Back to DEVLOG index](../DEVLOG.md)

## Entry 21 — Memory Doesn't Save Tokens Without Rules

**Date:** 2026-04-07 · **Plan:** `mellow-rolling-dijkstra.md`

### What we built

Entry-20 fixed sub-agent Serena access. This session built the memory foundation that makes that access useful:

- Ran Serena onboarding (`mcp__serena__onboarding`) — creates project structure memory from LSP exploration
- Wrote 9 project memories: `onboarding`, `suggested_commands`, `code_style`, `task_completion_checklist`, `testing/workflow`, `governance/agent-routing`, `architecture/stack`, `architecture/serena-config`, plus `global/infrastructure`
- Fixed Docker write access: `.serena/` overlay mount (`read_only: false`) on top of the read-only workspace mount, so SSE Serena sub-agents can write memories
- Expanded `settings.local.json` allow list to cover all memory tools plus `find_symbol`, `find_referencing_symbols`, `mcp__context7__query-docs`
- Set `initial_prompt` in `.serena/project.yml` to inject project context on every Serena activation

### The benchmark didn't show what we expected

Before writing any memories, a debugger sub-agent was given a fixed task: describe the testing workflow. It read 6 files and cost 38,896 tokens. After memories were written, the same task cost ~39,500 tokens — slightly more, not less.

| Metric | Before | After |
|---|---|---|
| Total tokens | 38,896 | ~39,500 |
| Memory tools called | 0 | 2–3 |
| AI_REFERENCE.md read | Yes | **Still yes** |
| Files read | 6 | 4–5 |

The after-state agent did call `list_memories` and `read_memory("testing/workflow")`. Then it read AI_REFERENCE.md anyway.

### Behavioral rules beat memory suggestions

The `initial_prompt` I set said "check memories before navigating code." Rule-004 said "read `docs/AI_REFERENCE.md` first." The agent followed rule-004.

This is by design. `initial_prompt` is injected as Serena MCP context — it's a suggestion from a tool. Rule-004 lives in `.claude/rules/project/` and is loaded by Claude Code as governance. Governance > tool suggestions.

The memories I wrote were largely a superset of AI_REFERENCE.md content for common sub-agent needs (commands, ports, file paths). But without a governing rule pointing agents toward memories, they went to the file they were told to go to. Memories are inert until rules activate them.

### The fix

Three changes, applied in the same session:

**1. rule-004 updated** — constraint now reads:
```
At every Speed 2 session start:
1. list_memories → read relevant memories (suggested_commands, architecture/*)
2. Fall back to AI_REFERENCE.md only for env vars, health endpoints, content not in memories
```

AI_REFERENCE.md still exists as fallback. It has env vars, health check endpoints, and volume mount details that aren't in memories yet. The file isn't obsolete — it's just no longer the mandatory first read.

**2. CLAUDE.md Part 2 updated** — a step 0 was prepended to the Serena-First Navigation list:
```
0. mcp__serena__list_memories → read relevant memories for project context BEFORE navigating code
```

This gives memory-checking the same authority level as `get_symbols_overview`. It's now a behavioral rule, not a suggestion.

**3. Memories revised to ≤100 tokens each** — the initial memories were 200–800 tokens and mixed facts with rules. Two were deleted outright (`task_completion_checklist`, `governance/agent-routing` — both duplicated rule files). The remaining 7 were rewritten as terse fact lists. A new `testing/conftest-fixtures` memory was added.

The principle: memories are project facts (what exists, what's configured), not behavioral rules (what to do). Rules belong in `.claude/rules/`. A memory that says "never spawn QA sub-agent" is a rule misplaced in memory. A memory that says "container name is ai-platform-api" is a fact that belongs there.

### The update mechanism

Memories go stale as the codebase evolves. A new `/update-memories` skill (`.claude/skills/update-memories.md`) codifies the audit process:

1. `list_memories` → enumerate
2. For each memory, check `git log` against the source files it describes
3. Rewrite changed entries, delete mismatched names, write new memories for uncovered facts
4. Enforce: ≤100 tokens, facts only, no rule duplication

The command is registered in `settings.json` and should run at every Phase Gate alongside the retrospective.

### What the next benchmark should show

These changes take effect in the next session (CLAUDE.md and rule files reload on session start). The validation protocol:

Delegate the same task to debugger: *"Describe the testing workflow. Report every tool call."*

Expected pass criteria:
- Agent calls `list_memories` before reading any file
- Agent reads `testing/workflow` memory (~65 tokens) instead of AI_REFERENCE.md (~1,743 tokens)
- Agent does NOT read AI_REFERENCE.md
- Total tokens < 38,896 (the pre-memory baseline)

Estimated savings: ~1,300 tokens per delegation where memories replace the AI_REFERENCE.md read. Across a 3-US sprint with 6 sub-agent delegations: ~7,800 tokens.

### The meta-lesson

A memory system is a navigation layer, not a token-saving mechanism by itself. The loop that produces savings is:

```
memory exists → rule points to it → agent reads it → skips the file read
```

Break any link in that chain and the savings disappear. Writing memories without updating the rules closed only the first link. The benchmark revealed the open link immediately — which is exactly what benchmarks are for.

The 100-token constraint matters for the same reason. A memory that costs 300 tokens to read, replacing a file that costs 400 tokens, saves 100 tokens and adds 2 tool calls. A memory that costs 65 tokens, replacing the same file, saves 335 tokens with the same overhead. The constraint isn't aesthetic — it's the margin that makes the trade worth making.

---

## Entry 21b — Machine-First Notation: From Memory to Format

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

---
