---
id: rule-010
trigger: "Before spawning ≥2 parallel agents, after receiving ≥2 parallel results, after 12 tool calls, at Phase Gate opening"
updated: "2026-04-02"
---

# Rule 010 — Compress-State Before Parallel Waves

<constraint>
MANDATORY `/compress-state` → `/clear` → read `docs/.temp_context.md` BEFORE: spawning ≥2 parallel agents, after receiving ≥2 parallel results, after 12 tool calls (configurable via `COMPRESS_THRESHOLD`), at Phase Gate opening.
</constraint>

<why>
80k planning context × 3 agents = 240k wasted tokens. Clear break between waves costs 30s, saves thousands of tokens.
</why>

<automation>
`.claude/hooks/auto-compress.sh` automates this rule via three hook registrations in `.claude/settings.json`:
- **PostToolUse (all tools):** increments a per-session counter; emits advisory at `COMPRESS_THRESHOLD` (default: 12)
- **PreToolUse (Agent):** warns before sub-agent spawn when context is already large
- **SubagentStop (all):** tracks completed sub-agents; warns at ≥2 completions
- **UserPromptSubmit:** detects Phase Gate keywords and reminds of gate steps

All warnings are **advisory only** — session flow is never blocked.
Manual `/compress-state` remains the primary mechanism; the hook is a safety net.

Override threshold: `export COMPRESS_THRESHOLD=8` (set lower for smaller context budgets).
</automation>
