# Rule 010 — Mandatory compress-state Before Parallel Agent Waves

## Constraint

The Tech Lead MUST run `/compress-state` → `/clear` → read `docs/.temp_context.md` BEFORE spawning any parallel wave of 2 or more sub-agents. This is a hard stop, not a recommendation.

## Mandatory Trigger Conditions

| Condition | Required action |
|---|---|
| About to spawn ≥ 2 agents in parallel | `/compress-state` → `/clear` → spawn |
| Just received results from ≥ 2 completed parallel agents | `/compress-state` → `/clear` → review |
| Session exceeded 15 tool calls | `/compress-state` → `/clear` |
| Phase Gate just opened | `/compress-state` → `/clear` before gate steps |

## Context

`/compress-state` has existed since project start and has never been triggered once (confirmed: `docs/.temp_context.md` does not exist as of 2026-03-30). Session JSONLs are 1.9–2.8 MB. The old threshold ("20 messages") is a passive heuristic missed under task pressure. Making it mandatory at structural moments — specifically parallel wave launch, which is when context balloons fastest — ties it to events the Tech Lead cannot miss.

Clearing an 80k-token planning context before a 3-agent parallel wave prevents 80k × 3 = 240k tokens of redundant context recalculation.

## Pattern

```
MANDATORY SEQUENCE before any parallel wave:
1. /compress-state  →  writes docs/.temp_context.md
2. /clear           →  context window reset
3. Read docs/.temp_context.md  →  resume state in fresh context
4. Spawn parallel agents
```

## Examples

✅ Correct:
```
Planning complete (8 US files read, plan.md written)
→ /compress-state → /clear → read .temp_context.md → spawn US-017 + US-018 + US-019
```

❌ Avoid:
```
Planning complete
→ immediately spawn US-017 + US-018 + US-019
← 80k planning context pollutes all three agent results; 240k tokens wasted
```
