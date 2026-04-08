---
name: init-ai-reference
description: "Scans the repository once using a single find command, reads up to 5 config files, and writes docs/AI_REFERENCE.md as the permanent stack reference. Use when setting up this repo for the first time, when AI_REFERENCE.md is missing, or after a major stack change."
model: haiku
---

<identity>
One-time stack reference generator. Produces docs/AI_REFERENCE.md in machine-first format (pipe-delimited inline lists, no prose tables). Checks Serena memories first — sections already in memories are omitted. After this runs, sessions read AI_REFERENCE.md only for env vars, health endpoints, mounts (rule-004).
</identity>

<hard_constraints>
1. ONE SCAN ONLY: The find command below is the only allowed codebase exploration in this command.
2. MAX 5 FILE READS: Read only Makefile, docker-compose.yml, pyproject.toml or requirements.txt, package.json, and .env.example. No application code files.
3. WRITE ONCE: Write docs/AI_REFERENCE.md completely in one Write tool call. No partial writes.
4. NO SECRETS: .env.example shows variable names only — never include actual values.
5. COMPACT FORMAT: Machine-first notation only (pipe-delimited inline lists). No Markdown tables, no prose. Target: ≤200 tokens.
</hard_constraints>

<workflow>
0. Call `mcp__serena__list_memories` → check for `architecture/stack`, `testing/workflow`, `suggested_commands`.
   - All three present: omit Stack + Test Commands from output.
   - Any missing: proceed with full scan.
1. Single repo scan (one Bash command):
   ```bash
   find . -maxdepth 3 \
     \( -name "*.toml" -o -name "*.json" -o -name "Makefile" \
        -o -name "docker-compose*.yml" -o -name "requirements*.txt" \
        -o -name "package.json" -o -name ".env.example" \
        -o -name "alembic.ini" -o -name "pytest.ini" \
        -o -name "tsconfig.json" -o -name "vite.config.*" \) \
     -not -path "*/node_modules/*" \
     -not -path "*/.git/*" \
     -not -path "*/dist/*" \
     -not -path "*/__pycache__/*" \
     2>/dev/null | sort
   ```
2. Read up to 5 key config files: Makefile, docker-compose.yml, pyproject.toml (or requirements.txt), package.json (root or frontend/), .env.example.
3. Write `docs/AI_REFERENCE.md` in machine-first format (see output_format). No prose tables — pipe-delimited inline lists only.
4. Report per output_format.
</workflow>

<output_format>
Write docs/AI_REFERENCE.md with this exact structure (machine-first, no prose tables):

```
# AI_REF v2 — rule-004: memories first; read here ONLY for env/health/mounts
# Notation: svc:port→health-path(expected) | K:V(type)[default] | (ai-tools)=docker-compose.ai-tools.yml

## SVCS
[pipe-delimited: name:port→health-path(expected) per service; no health endpoint = omit → clause]

## MAKE
[pipe-delimited: target:short-description]

## PATHS
[pipe-delimited: group:path1,path2,...]

## ENV
[pipe-delimited: VAR(type)[default] — type/default optional, include only if meaningful]

## MOUNTS
[pipe-delimited: host→container | vols:name1,name2,...]

## MCP
[pipe-delimited: name:transport-endpoint(scope,rules,constraints)]
```

Target: ≤200 tokens total.

Report EXACTLY:
✅ docs/AI_REFERENCE.md written (~NNN tokens)

Memories found: [list or "none"]
Sections skipped (in memories): [list or "none"]
Env vars documented: [count]
</output_format>
