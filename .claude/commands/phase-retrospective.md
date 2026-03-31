---
name: phase-retrospective
description: "Produces the mandatory end-of-phase retrospective report: incidents, rules extracted, cost analysis, and actionables. Appends one row to docs/SESSION_COSTS.md. Run automatically at every Phase Gate (Phase 4, step 6). Never skip."
version: "1.0.0"
model: claude-sonnet-4-6
destructive: false
output: docs/SESSION_COSTS.md (append-only)
speed: 2
trigger: "/phase-retrospective"
parallel_safe: false
---

# Command: /phase-retrospective
> Mandatory phase-gate ritual. Produces the full retrospective report and appends the session cost row.
> Run ONCE per phase gate, immediately after DocWriter Mode B.
> Invocation: type `/phase-retrospective` in the chat (or call it by name).

---

<identity>
Produces a structured retrospective report covering the entire phase and presents it to the user.
Then appends one cost row to `docs/SESSION_COSTS.md` using append-only bash.
</identity>

<workflow>
<step_1>
**Recall Phase Incidents (in-context only, no file reads)**

From the current session history, list every:
- Circuit breaker triggered (agent hit 2 attempts)
- QA bounce-back (QA Mode A returned FAIL, US re-delegated)
- Unexpected blocker (missing context, wrong assumption, infra issue)
- /judge FAIL verdict

Format: `Incident N: [US-NNN] — [agent] — [what failed] — [root cause]`

If zero incidents: write `No incidents this phase.`
</step_1>

<step_2>
**Rules Extracted**

List rule files saved by `/reflexion` this phase:
```
Rules saved: rule-NNN-*.md (one line per rule, with title)
Rules discarded: N (reason)
Promotion candidates: [list or "none"]
```

If `/reflexion` was not run: note it and run it now before continuing.
</step_2>

<step_3>
**Cost Analysis**

Produce the cost table. Use actuals from agent invocation reports where available; estimate with `~` where not.

```markdown
| Phase/Operation | Agent | Model | Input tokens | Output tokens | Total tokens | Avoidable? |
|---|---|---|---|---|---|---|
| Planning | Tech Lead | Sonnet | ~X | ~Y | ~Z | No |
| [US-NNN impl] | [Agent] | Haiku | X | Y | Z | No |
| [Explore ×N] | Explore | — | ~X | ~Y | ~Z | ✅ Yes (~Xk — rule-003) |
| DocWriter | DocWriter | Haiku | X | Y | Z | No |
| QA Mode A | QA | Haiku | X | Y | Z | No |
| **TOTAL** | | | **~X** | **~Y** | **~Z** | **~W avoidable** |
```

Then: "Areas to improve" — 2-3 bullet points on highest-impact waste.
</step_3>

<step_4>
**Actionables**

Prioritized list of fixes applied or to apply:
```
✅ Applied: [fix description] — rule/patch reference
⏳ To apply: [fix description] — where/how
```

Include both cost-expert fixes AND Tech Lead's own observations.
</step_4>

<step_5>
**Append to SESSION_COSTS.md**

Use append-only bash (`echo >>` — NEVER overwrite):

```bash
echo "| $(date +%Y-%m-%d) | Phase-N | [session description] | N agents | ~X input | ~Y output | ~Z total | ~W evitable | [notes] |" >> docs/SESSION_COSTS.md
```

Verify the append with `tail -3 docs/SESSION_COSTS.md`.
</step_5>

<step_6>
**Present Report to User**

Output the complete report in this order:
1. Header: `## Phase-N Retrospective — [date]`
2. Incidents section
3. Rules extracted section
4. Cost table + areas to improve
5. Actionables
6. Confirmation: `✅ Row appended to docs/SESSION_COSTS.md`
</step_6>
</workflow>

<hard_constraints>
1. Never skip this command at a Phase Gate — Hard Rule 16.
2. Never overwrite SESSION_COSTS.md — append only.
3. If /reflexion was not run before this command: run it first (Step 2 will note this).
4. Token estimates are acceptable; mark with `~`. Actuals preferred where available.
5. Maximum 1 page output — be concise. The user reads this to make decisions, not for history.
</hard_constraints>
