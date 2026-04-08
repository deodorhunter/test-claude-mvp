---
description: "Directives for exploration in main session and subagents. Applies to any agent action that attempts to read, scan, summarize, or explore files in the codebase."
---
<metadata>
  id: rule-003
  updated: "2026-04-03"
</metadata>

# Rule 003 — No Explore Agents for File Reading

<constraint>
NEVER spawn a sub-agent solely to read, scan, or summarize files. Use Serena MCP tools if available, fallback to Read, Grep, or Glob tools directly.
</constraint>

<why>
Explore agents return summaries — raw content is lost and must be re-read for context injection (~60k wasted tokens per avoidable Explore call).
</why>

<pattern>
```
✅ Read("path/to/file.py") or Grep(pattern, path) or Glob(pattern)
❌ Agent(subagent_type="Explore", prompt="summarize this file for me")
```
</pattern>
