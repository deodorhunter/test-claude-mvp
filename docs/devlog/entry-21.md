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

The after-state agent did call `list_memories` and `read_memory("testing/workflow")`. Then it read AI_REFERENCE.md anyway. Am I a joke to you?

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

