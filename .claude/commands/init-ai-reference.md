---
name: init-ai-reference
description: "Scans the repository once using a single find command, reads up to 5 config files, and writes docs/AI_REFERENCE.md as the permanent stack reference. Use when setting up this repo for the first time, when AI_REFERENCE.md is missing, or after a major stack change."
version: "3.0"
type: command
model: claude-haiku-4-5-20251001
allowed_tools: [bash, write]
destructive: false
output: docs/AI_REFERENCE.md
trigger: "/init-ai-reference"
parallel_safe: true
---

<identity>
One-time stack reference generator. Performs the single allowed codebase scan to produce docs/AI_REFERENCE.md — the permanent reference that replaces all future exploration. After this command runs, all sessions read AI_REFERENCE.md instead of exploring.
</identity>

<hard_constraints>
1. ONE SCAN ONLY: The find command below is the only allowed codebase exploration in this command.
2. MAX 5 FILE READS: Read only Makefile, docker-compose.yml, pyproject.toml or requirements.txt, package.json, and .env.example. No application code files.
3. WRITE ONCE: Write docs/AI_REFERENCE.md completely in one Write tool call. No partial writes.
4. NO SECRETS: .env.example shows variable names only — never include actual values.
</hard_constraints>

<workflow>
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
3. Write `docs/AI_REFERENCE.md` with exact structure (stack table, services+ports table, make targets table, test commands, key file paths, env var names only, health check endpoints).
4. Report: ✅ file written + make targets discovered + services and ports discovered.
</workflow>

<output_format>
Report EXACTLY:
✅ docs/AI_REFERENCE.md written

Make targets found: [list]
Services found: [name:port list]
Env vars found: [count] variables documented

Reminder: Re-run /init-ai-reference after major stack changes. Future sessions read this file instead of exploring.
</output_format>
