---
name: update-memories
description: "Audit and rewrite stale Serena project memories. Run after phase gates, significant refactors, or when a sub-agent reports memory content that doesn't match current code."
---

## Purpose
Audit and rewrite stale Serena project memories. Run after phase gates, significant refactors,
or when a sub-agent reports memory content that doesn't match current code.

## Process
1. Call `mcp__serena__list_memories` to enumerate all current memories
2. For each memory, identify the source file(s) it describes
3. Check `git log --oneline -10` for recent changes to those files
4. For each changed source: rewrite the memory to reflect current state
5. If memory name no longer matches content: delete and rewrite with correct name
6. If new project facts emerged with no memory: write a new memory
7. If a memory duplicates content in `.claude/rules/` or `CLAUDE.md`: delete it

## Memory Constraints (enforced on every write)
- **≤100 tokens (≤75 words)** — if it's longer it's not a memory, it's a document
- **Facts only** — no behavioral rules (those belong in `.claude/rules/` and `CLAUDE.md`)
- **Name = content** — `testing/workflow` describes testing workflow, nothing else
- **No duplication** of content already in rule files or CLAUDE.md

## Source → Memory Mapping
| Memory | Validate against |
|---|---|
| `onboarding` | `backend/app/main.py`, `ai/models/base.py`, top-level directory structure |
| `suggested_commands` | `Makefile`, `infra/docker-compose.yml`, `backend/pyproject.toml` |
| `code_style` | `backend/pyproject.toml`, `CLAUDE.md` (check no duplication) |
| `testing/workflow` | `backend/tests/conftest.py`, `infra/docker-compose.yml` (container name) |
| `testing/conftest-fixtures` | `backend/tests/conftest.py` (fixture names, patched paths) |
| `architecture/stack` | `backend/app/` directory structure |
| `architecture/serena-config` | `infra/docker-compose.ai-tools.yml`, `.mcp.json` |
| `global/infrastructure` | `infra/docker-compose.yml` (port table, service names) |

## When to Run
- After every **Phase Gate** (codebase state changes most between phases)
- When `git log --oneline -5` shows changes to any file in the mapping table above
- When a sub-agent reports unexpected behavior that might indicate stale memory

## Anti-Patterns to Fix
- Memory contains `rule-NNN` references → extract the fact, drop the rule reference
- Memory contains prose explanation → convert to key:value or bullet list
- Memory exceeds 100 tokens → cut to essential facts only
- Two memories with overlapping content → merge or delete the weaker one
