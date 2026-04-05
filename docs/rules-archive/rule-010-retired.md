<metadata>
  id: rule-010
  updated: "2026-04-04"
</metadata>

# Rule 010 — Orchestrator Is the Serena Proxy for Sub-Agents

<constraint>
Before delegating any US that touches Python or TypeScript source files, the orchestrator (main session) MUST call `mcp__serena__get_symbols_overview` for each relevant file and inject results as `<symbols path="...">` blocks in the delegation prompt. Never instruct a sub-agent to "use Serena" — Serena tool calls are not available in sub-agent sessions (Claude Code limitation: MCP tool bridge not passed to Agent-spawned sub-agents).
</constraint>

<why>
Confirmed 2026-04-04: aiml-engineer session received Serena system instructions but "No such tool available: mcp__serena__get_symbols_overview". Sub-agents get MCP server descriptions (system-reminder) but not callable tools. Without orchestrator pre-flight, sub-agents default to full-file Read (~2,000 tokens each vs ~200 for symbol overview).
</why>

<pattern>
```
✅ CORRECT — orchestrator pre-flight:
  mcp__serena__get_symbols_overview("backend/app/models.py")
  → inject into delegation: <symbols path="backend/app/models.py">{"Class": ["Plugin", "Tenant"]}</symbols>

✅ CORRECT — delegation prompt includes symbols:
  "Edit Plugin model. Symbols: <symbols path="backend/app/models.py">...</symbols>"

❌ WRONG — delegating without pre-flight:
  "Use Serena to navigate the models before editing"  ← tool unavailable in sub-agent

❌ WRONG — expecting sub-agent to call Serena directly:
  Agent prompt: "Call get_symbols_overview on the relevant files first"
```
</pattern>
