# Rule 007 — "Proceed" at Phase Boundary Means Complete Gate Steps First

## Constraint

When the user says "proceed", "approved", "continue", or any similar confirmation at a phase boundary, the Tech Lead MUST complete all Phase Gate steps (BACKLOG update → retrospective → present summary → wait for explicit approval) BEFORE reading, planning, or delegating anything for the next phase. "Proceed" is approval to run the Gate, not to start the next phase.

## Context

In Phase 2c, the user approved Phase 2c completion. The Tech Lead immediately read Phase 2d US files and began planning Phase 2d delegation — skipping the Phase Gate entirely (BACKLOG not updated, retrospective not run, no summary presented). The retrospective is mandatory even when zero incidents occurred. The docwriter Mode B step is also mandatory. No new phase may begin until the previous phase's gate is fully closed.

## Gate Checklist (must complete in order before next phase)

```
1. Mark all phase USes ✅ Done in BACKLOG.md and individual US-NNN.md files
2. Run Full Service Verification (make down && make up && make migrate && make test)
3. STOP — present phase summary + token cost estimate to user. Wait for approval.
4. Spawn DocWriter Mode B (human-facing architecture doc for the phase)
5. Run /phase-retrospective — present full report to user (MANDATORY, never skip)
6. Append row to docs/SESSION_COSTS.md
7. Update docs/plan.md + docs/backlog/BACKLOG.md phase status
8. STOP — wait for explicit user approval before starting next phase
```

## Examples

✅ Correct:
```
User: "Phase 2c approved, proceed"
Tech Lead: [runs gate steps 1-8] → "Phase 2c gate complete. Ready for Phase 2d on your go."
```

❌ Avoid:
```
User: "Phase 2c approved, proceed"
Tech Lead: reads US-017.md, US-018.md, US-019.md, plans Phase 2d...
← Gate steps skipped entirely
```
