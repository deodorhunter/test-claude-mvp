---
applyTo: "**"
---

# Serena Code Navigation (VS Code)

Serena is configured in `.vscode/mcp.json`. It gives Copilot direct symbol-level access to the codebase — finding classes, functions, and type information without reading entire files.

## Navigation priority

Use Serena tools in this order before reading any file for structure:

1. `mcp_oraios_serena_get_symbols_overview` — list all symbols (classes, functions, variables) in a file with signatures only. Use before opening a file. ~200 tokens vs ~2,000 for a full file read.
2. `mcp_oraios_serena_find_symbol` — find a specific function/class by name across the whole project. Returns file path + line number. Use instead of asking the user to search.
3. `mcp_oraios_serena_read_file` — read a specific line range once you know where the symbol is. Never read a whole file when you only need one function.
4. `mcp_oraios_serena_get_diagnostics` — check for type errors in a file before touching it. Avoids breaking changes that only surface after editing.

## Rules

- Never read an entire file to find a function. Use `find_symbol` first.
- Never guess import paths or class structures. Use `get_symbols_overview`.
- If you need to check whether a change is type-safe before proposing it, use `get_diagnostics`.
- Full file reads (`#file:path`) are appropriate only when you need to understand the *entire* file context for an edit spanning more than one function.

## Context7 for library documentation

Context7 (also configured in `.vscode/mcp.json`) provides up-to-date library documentation directly in your context. Use it when you need to generate code that uses a specific library or API.

- `mcp_context7_resolve_library_id` — map a library name to its Context7 ID
- `mcp_context7_query_docs` — fetch current documentation for a library

**Important:** Context7 queries must contain only the library name and your question. Do not include source code, file paths, or schema fragments in Context7 queries.
