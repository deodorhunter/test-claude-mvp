---
id: rule-010
trigger: "Before spawning ≥2 parallel agents, after receiving ≥2 parallel results, after 15 tool calls, at Phase Gate opening"
updated: "2026-03-31"
---

# Rule 010 — Compress-State Before Parallel Waves

<constraint>
MANDATORY `/compress-state` → `/clear` → read `docs/.temp_context.md` BEFORE: spawning ≥2 parallel agents, after receiving ≥2 parallel results, after 15 tool calls, at Phase Gate opening.
</constraint>

<why>
80k planning context × 3 agents = 240k wasted tokens. Clear break between waves costs 30s, saves thousands of tokens.
</why>
