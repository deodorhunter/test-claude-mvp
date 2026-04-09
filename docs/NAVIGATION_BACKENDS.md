# Navigation Backends: Serena vs codebase-memory-mcp

Reference doc for the dual-backend navigation framework. Update after each benchmark run.

---

## Capabilities Comparison

| Aspect | Serena | codebase-memory-mcp (CBM) |
|--------|--------|--------------------------|
| **Transport** | SSE/HTTP (Docker daemon, persistent) | stdio (docker interactive exec, daemon) |
| **Storage** | Session-scoped, LSP in-memory | SQLite (persists cross-session, `~/<project>_cbm_cache`) |
| **Memory update** | Manual — requires `update-memories` skill | **Auto-indexed on file change** |
| **Language scope** | Python + TypeScript only (`.serena/project.yml`) | 66 languages (tree-sitter grammars) |
| **Primary capability** | AST symbols, call graphs, in-place editing | Code search, impact analysis, dead code, import graphs |
| **Best for** | Active refactoring, symbol editing, small–medium repos | Large repos, cross-session memory, wide-scope search |
| **Project size fit** | Small–Medium (<100 files) | Medium–Large (any size) |
| **Token reduction claim** | ~90% vs full-file reads | ~99.2% vs file-by-file search |
| **Startup** | Always running (Docker service) | Always running (Docker service), cold-start per MCP session for downloading latest version |

**Key insight:** These tools are **complementary, not competitive.**
- Serena = precise in-session AST editing (replace symbol bodies, get errors, navigate type hierarchy)
- CBM = persistent wide-scope memory that never needs manual flushing (auto-indexes on change)
- The `both` backend uses each for its strength simultaneously

---

## Decision Tree: Which Backend to Use

```
Project size?
├── < 2 files → neither (Read/Grep/Glob is sufficient)
├── 2–99 files, Python/TS, active refactor → serena
├── 100+ files OR multi-language → cbm or both
└── Need cross-session memory without manual flush → cbm or both

Task type?
├── Edit/rename a symbol body → serena (replace_symbol_body)
├── Find symbol definition, get fields/methods → serena (get_symbols_overview)
├── Wide search: "all files that reference X" → cbm (search_codebase)
├── Call path / impact analysis → cbm (call_path, impact)
├── Dead code detection → cbm
└── Cross-session context (survives compaction) → cbm
```

---

## Configuration

### Changing the active backend

Edit `.claude/settings.json`:
```json
"mcpServers": {
  "codebase-memory-mcp": {
    "command": "bash",
    "args": ["infra/scripts/cbm-mcp.sh"],
    "env": {
      "NAVIGATION_BACKEND": "serena"   ← change this value
    }
  }
}
```

Valid values: `serena` | `cbm` | `both`

**After changing:** restart Claude Code (MCP servers are loaded at launch, not per-prompt).

### Developer session override (no file edit)

```bash
export NAVIGATION_BACKEND=cbm
# then launch Claude Code
```

Shell env takes precedence over settings.json. Unset to revert: `unset NAVIGATION_BACKEND`.

### Building the CBM Docker image

```bash
docker compose -f infra/docker-compose.ai-tools.yml build codebase-memory-mcp
```

- Workspace bind-mounted **read-only** at `/workspace`
- SQLite cache persists in Docker named volume `<project-name>_cbm_cache`

---

## Progressive Disclosure Architecture

The framework uses **on-demand context injection** rather than always-active monolithic rules. Three enforcement layers:

```
Layer 1 — UserPromptSubmit: tool-preference-inject.sh
  ├── Reads NAVIGATION_BACKEND from settings.json
  ├── Injects dispatch table into context at start of every prompt
  └── Non-blocking (exit 0) — always fires, even on simple queries

Layer 2 — PreToolUse: tool-routing-guard.sh
  ├── Fires before every mcp__serena__* or mcp__codebase-memory-mcp__* call
  ├── Checks tool name against active backend
  ├── Injects redirect message if wrong tool selected
  └── Non-blocking (exit 0) — Claude retains discretion for edge cases

Layer 3 — PreToolUse (Bash): block-exploration.sh
  ├── Fires before every Bash command
  ├── Blocks filesystem exploration (ls, find, tree, du)
  ├── Error message suggests correct navigation tool for active backend
  └── Blocking (exit 2) — hard stop
```

**Why non-blocking for Layer 2?**
Blocking would prevent legitimate cross-backend calls: e.g. using `serena__replace_symbol_body` when `NAVIGATION_BACKEND=cbm` is *correct* (CBM has no editing tools). Advisory + firm language at call time is higher-leverage than a hard block that creates workarounds.

---

## Benchmark Results

See `benchmark/results/` for recorded runs.

| Run | Date | Serena total tokens | CBM total tokens | Serena avg acc | CBM avg acc | Notes |
|-----|------|---------------------|-----------------|----------------|-------------|-------|
| —   | —    | pending             | pending         | pending        | pending     | Runs not yet executed |

**Tasks:** defined in `benchmark/tasks/navigation_tasks.md`

---

## Frequently Asked Questions

**Q: Does CBM replace Serena's memories?**
A: Yes for cross-session persistence — CBM auto-indexes on file change, so Serena's `update-memories` skill becomes optional. No for in-session symbol editing — Serena's `replace_symbol_body` has no CBM equivalent.

**Q: Do I need to run `update-memories` when using CBM?**
A: Only if you explicitly need Serena's memory layer (e.g. architecture summaries for sub-agents). CBM maintains its own persistent index automatically.

**Q: What happens if I set `both` and have 40+ navigation tools visible?**
A: `tool-routing-guard.sh` fires before every MCP call and redirects to the correct tool. CLAUDE.md has a strict dispatch table. Claude will still see all tools but gets a redirect at decision time.

**Q: Can sub-agents use CBM?**
A: CBM (stdio) needs to be invoked per-session via `infra/scripts/cbm-mcp.sh`. Sub-agents with inline `mcpServers` definitions can include it.
