---
description: "Serena-first navigation in both main session and sub-agents"
---

<metadata>
  id: rule-009
  updated: "2026-04-05"
</metadata>

# Rule 009 — Serena-First Navigation

<constraint>
Before reading any file for structure, use Serena: `get_symbols_overview` (~200 tokens) → `find_symbol` (~50 tokens) → targeted `read_file` range. Full `Read`/`cat` ONLY for `<file>` XML injection into DocWriter or algorithm-level detail.

Scope: Python and TypeScript files only (`.serena/project.yml`). Markdown, YAML, JSON, Dockerfile → use Read/Grep directly.

Sub-agents: Serena IS available in sub-agents when agent frontmatter uses `disallowedTools` (not `tools:` allowlist) and includes inline `mcpServers` definition. All implementing agents have this configured. If Serena is unavailable in a sub-agent, it must STOP and request orchestrator to inject `<file>` blocks — never fall back to shell exploration.

Orchestrator: Serena calls are for cross-file architectural analysis during planning only. Sub-agents self-navigate — orchestrator symbol injection is no longer required for delegation.

Scope: Speed 1 (main session direct implementation + debugger agent) AND Speed 2 (all implementing sub-agents via mcpServers field).
</constraint>

<why>
Full-file reads cost ~2,000 tokens each. Serena overviews give the same structural info at 10% cost. Root cause of prior sub-agent Serena failure: `tools:` allowlist silently blocked MCP tools (confirmed 2026-04-05, GitHub issue #25200). Fix: `disallowedTools` + inline `mcpServers`.
</why>

<pattern>
✅ Sub-agent: `mcp__serena__get_symbols_overview(file)` → targeted Read range (direct — no orchestrator pre-flight needed)
✅ Main session: `mcp__serena__get_symbols_overview(file)` → cross-file architectural analysis
✅ Orchestrator delegation: inject `<file>` only for algorithm-level detail or DocWriter
❌ `Read(whole_file)` when Serena symbol overview suffices
❌ Sub-agent falling back to `ls`/`find` when Serena unavailable — STOP and escalate instead
</pattern>
