← [Back to DEVLOG index](../DEVLOG.md)

## Entry 20 — The Tools Allowlist Problem

**Date:** 2026-04-05 · **Plan:** `rustling-dreaming-pine.md`

### The symptom and the workaround we shouldn't have needed

For several sessions, sub-agents couldn't call Serena or Context7. They'd receive Serena's system instructions in the `system-reminder` block — the server was connected, the documentation was there — but calling `mcp__serena__get_symbols_overview` returned "No such tool available." The diagnosis at the time was a Claude Code architectural limitation: MCP tool RPC bridges aren't passed to Agent-spawned sub-sessions.

The workaround became rule-010: before delegating any US that touched Python or TypeScript, the orchestrator would call `mcp__serena__get_symbols_overview` for each relevant file, inject the results as `<symbols>` blocks into the delegation prompt, and only then spawn the sub-agent. This worked, but it was ~200 tokens per file in orchestrator (Sonnet) context, per delegation, for every US. The agents were getting the structural information they needed — but paying for it in the wrong place, at the wrong model tier, every time.

### The actual root cause

The real problem turned out to be simpler and more embarrassing: the `tools:` allowlist in agent frontmatter.

Every implementing agent had a line like `tools: Bash, Read, Edit, Write, mcp__serena, mcp__context7`. The intent was to permit these tools while restricting others. What actually happened: `tools:` is a filter on Claude Code's native tools. It has no mechanism to inject external MCP connections. The `mcp__serena` and `mcp__context7` entries were just strings in a list that the allowlist processor didn't know what to do with — they silently matched nothing. GitHub issue #25200 confirms this is a known behavior.

The agents were receiving the MCP system instructions but had no RPC bridge, because the allowlist had effectively disqualified all MCP tools before the session started.

### The fix and the gate test

The previous session formed this hypothesis and updated `debugger.md` as a canary: replace `tools:` with `disallowedTools: Write, Glob, Agent` and add inline `mcpServers` definitions. A denylist passes all tools through by default — including MCP — while still blocking specific ones. The `mcpServers` block establishes the RPC connection at agent spawn time.

This session opened by spawning the debugger immediately to validate the fix before touching anything else. Both calls succeeded:

```
mcp__serena__get_symbols_overview("ai/models/base.py")
→ {"Class": ["ModelResponse", "ModelAdapter", "ModelError", "OllamaUnavailableError", "ClaudeConfigError"]}

mcp__context7__resolve-library-id("fastapi")
→ /fastapi/fastapi — score 84.63, 1075 snippets
```

Strategy A confirmed. The fix rolled out to all eight implementing agents in the same session.

### What the fix changes about how agents work

Previously, the constraint on sub-agents read: "Rely strictly on `<user_story>` and `<file>` blocks injected by the Tech Lead." This was accurate — with no Serena access, agents genuinely couldn't navigate code any other way. The constraint was also a symptom: it described a limitation masquerading as a rule.

With Serena available, agents can call `mcp__serena__get_symbols_overview` directly to get ~200 tokens of structural information per file instead of reading the whole file (~2,000 tokens). The constraint becomes: navigate first via Serena, use targeted `Read` ranges for bodies, fall back to orchestrator injection only if Serena is unavailable. The rule now reflects capability rather than papering over absence.

The orchestrator delegation section changed accordingly. Symbol injection is no longer a required step before delegation — agents self-navigate. The pre-flight calls that rule-010 mandated are gone. rule-010 is retired and archived.

### Rule 1 going from soft to hard

The same session also added mechanical enforcement for Rule 1 (no autonomous filesystem exploration). Until now, Rule 1 was a text constraint — agents read it and were expected to follow it. Whether they did was invisible at harness level.

The new `block-exploration.sh` PreToolUse hook intercepts Bash tool calls before execution and checks the command against a set of patterns: bare `ls`, `ls` with flags but no path, `find` from `.` or `/`, `tree`, `du`, `locate`. Any match exits with code 2 and a message pointing to `mcp__serena__get_symbols_overview`. Targeted path verification (`ls backend/app/specific/`) is allowed.

The hook runs in the main session and in all sub-agent sessions via agent frontmatter. Rule 1 is now enforced at the harness level, not just declared in text.

The distinction matters. A soft rule degrades under pressure — an agent that's stuck on a problem for two attempts will try `ls` on the third. A hard rule doesn't degrade; it just blocks the command and forces the agent to use the right tool.

### What the benchmark measured

Running `benchmark/measure-context-size.sh` after the session:

- Total auto-loaded context: 60,764 bytes (baseline, 2026-03-30) → 43,293 bytes today (−29%)
- Per-agent scoped rule injection: 103,012 bytes across 7 agents → 8,836 bytes (−91%)
- Tool output: `git log --oneline -50` truncated from 991 → 185 tokens (−81%)
- Session cost: $4.15, cache 100%, drift 0

The 29% reduction in auto-loaded context is conservative. It doesn't capture the delegation overhead eliminated by removing orchestrator pre-flight — those savings appear per-US in future sessions, not in the file-size benchmark. A typical 3-file US was costing ~1,200 tokens of orchestrator context for symbol injection alone; that's now zero.

### The meta-lesson

The Serena workaround lasted three sessions before the real cause was found. That's three sessions of building governance around a limitation that didn't exist — rule-010 was a precise and well-reasoned solution to the wrong problem.

The right debugging step would have been to isolate the variable earlier: test a `general-purpose` agent (which uses `tools: *`) against the same MCP calls. We did eventually run that test in the previous session, and it succeeded immediately — which should have been the signal to look at the allowlist mechanism rather than the MCP bridge. It wasn't, because the "architectural limitation" explanation was plausible enough to accept.

The practical lesson: when a workaround feels more complex than the underlying system warrants, the diagnosis is probably wrong. The fix for "sub-agents can't use Serena" was two lines of frontmatter, not a mandatory pre-flight protocol.

---
