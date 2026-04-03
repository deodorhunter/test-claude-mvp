← [Back to DEVLOG index](../DEVLOG.md)

## Entry 14 — Phase 3b Gate & Rule-020: Automating the Discretionary-Choice Anti-pattern — 2026-04-02

> Phase 3b completed (7 US, 454k tokens). Phase Gate 3b executed all mandatory steps. Rule-020 extracted to prevent recurrence of Phase Gate skip pattern (observed in Phase 2c and again in Phase 3b).

#### Phase 3b outcomes

**Implementation (Wave 1 + 2):** 7 US across 3 waves
- Wave 1 (cleanup after scope creep): US-054 ✅ (45k), US-055 ✅ (38k), US-066 ✅ (24k)
- Wave 2a (parallel): US-056 ✅ (58.5k AI/ML), US-067 ✅ (48.4k DocWriter)
- Wave 2b (sequential): US-068 ✅ (53.6k Product Owner)

**Documentation (Mode B):** 57.3k tokens — `docs/architecture/phase-3b-overview.md`

**Deliverables:**
- `.claude/hooks/auto-compress.sh` — 4-event advisory hook (PostToolUse, PreToolUse, SubagentStop, UserPromptSubmit)
- `docs/.command-catalog.md` — 12 commands, reusable reference (~3k tokens/delegation savings)
- Updated rule-010, AI_REFERENCE.md with Context Management + Symbol-Context sections
- rule-020 extracted and activated

**Phase 3b mini-gate verified:** cognitive patterns ✅, doc verification ✅, context compression automation ✅, refinement ceremony ✅

#### Rule-020: Phase Gate Auto-Proceed Pattern

**Pattern identified:** Rule-007 violation recurrence (Phase 2c + Phase 3b).

**Incident 1 (Phase 2c, 2026-03-29):** Phase Gate was entirely skipped when orchestrator asked user "proceed to Phase 3?" instead of running mandatory gate steps.

**Incident 2 (Phase 3b, 2026-04-02):** After Wave 2b completion, orchestrator asked "Phase 3c work OR Phase Gate 3b?" — again offering discretionary choice over mandatory gate.

**Root cause:** Misreading orchestrator.md Phase 4 as a decision point rather than a non-discretionary sequence. The hard constraint is rule-007 ("complete ALL phase gate steps"), but the implementation assumed user input was needed.

**Cost of the pattern:** Each full skip costs ~40k tokens (missing retrospective, cost analysis, architecture doc). Partial skip (asking discretionary choice) doesn't cause token waste directly but signals the gate is being treated as optional.

**Prevention:** Rule-020 — "When all US in a phase are marked Done, proceed immediately with Phase Gate steps (orchestrator.md Phase 4). Never ask 'Phase N+1 work OR Phase Gate N?' — the gate is mandatory and non-discretionary."

**Impact:** Blocks the discretionary-choice anti-pattern. The user caught the violation in real-time (Phase 3b); rule-020 will prevent recurrence in Phase 4+.

#### Cost analysis: Phase 3b vs prior phases

| Phase | Duration (est.) | Total tokens | Avoidable waste | Notes |
|---|---|---|---|---|
| Phase 2d | ~90 mins | ~125k | ~4k (3%) | Minimal waste; direct impl pattern; rule-010 not yet automated |
| Phase 3a | ~60 mins | ~102k | ~20k (20%) | Over-contextualization on doc tasks; led to US-067 (symbol-first) + US-068 (pre-collect catalog) |
| **Phase 3b** | **~180 mins** | **~454k** | **~40k (9%) prevented by rule-020** | Rule-020 extraction (recurrence prevention); Wave 1 scope creep cleaned; context compression automated |

**Observation:** Phase 3b is longer and has higher absolute token cost, but avoidable waste is lower % than Phase 3a. Improvements from 3a (symbol-context guidance, pre-collected commands) likely contributing to efficiency. No circuit-breaker triggers or QA bounce-backs in Phase 3b.

#### Framework learning: Behavioral constraints vs detection

Entry 13 focused on scope creep detection (Judge verdicts caught stub files). Entry 14 reveals a parallel gap in orchestration: the orchestrator itself was violating rule-007, caught by the user not by the system.

**Current defensive layers:**
- **Detection:** Judge (post-impl), Critic (pre-impl), /consistency-check, /judge verdicts
- **Prevention:** Rules loaded in CLAUDE.md, hard constraints in orchestrator.md

**Gap:** Orchestrator rules (rule-007, rule-020) are documented but not auto-enforced. A human still has to notice when the orchestrator skips a gate or offers discretionary choice.

**Future consideration:** Could a "orchestrator validator" agent run post-gate-step to confirm rule-007 compliance? Or could the pre-prompt hook detect Phase Gate keywords and enforce gate-step sequencing? For now, rule-020 + user vigilance is the control.

#### Lessons for Phase 3c+

1. **Explicit DO NOT sections in AC** are now standard (from Entry 13). Reduces autonomy creep risk.
2. **Rule-020 activation** prevents gate-skip pattern in Phase 4 orchestration.
3. **Context compression automation** (US-056) now advisory via hooks. Monitor SubagentStop regex matcher in live parallel waves (first validation: Phase 3c).
4. **Symbol-first context injection** (US-067) reduces doc task bloat; estimated 10-12k tokens/phase savings going forward.
5. **Pre-collected command catalog** (US-068) eliminates ~3k tokens per delegation (used in agent prompts).

**Combined estimated savings for Phase 3c+:** ~30-40k tokens per phase from automation + pattern fixes above.


---
