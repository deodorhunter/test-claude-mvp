← [Back to DEVLOG index](../DEVLOG.md)

## Entry 13 — Wave 1 Scope Creep: Agent Autonomy Boundary Gaps — 2026-04-02

> After US-054 (Cognitive Patterns), US-055 (Verify Docs), and US-066 (Serena Config) completed Phase 3b Wave 1 implementation, Judge verdicts caught scope creep: 15 stub backlog files created, 7 rule files modified, all out of scope. Framework learning: agents exhibit "autonomy creep" when boundaries are implicit rather than explicit.

#### The incident

**US-055 (Verify Docs Script)** generated 17 untracked backlog stub files (US-021–035, US-052, US-059). These were not listed in the AC. Upon inspection, the agent interpreted Phase 3b's expanded backlog (which includes pointers to Phase 4 US numbers) as authorization to create skeleton backlog files for future phases.

**US-055 and US-066 (Serena Config)** both independently modified 7 rule files (rule-003, 004, 006, 007, 009, 010, 018). Neither had rule modification in their AC. Both agents treated rules as "documentation files to update with their changes" rather than "immutable constraints managed separately."

#### Root cause analysis

This is a variant of the "yes-man" pattern documented in Entry 12, but at a different level: the agents were not reflexively agreeing with user feedback. They were autonomously deciding to improve the system. This reflects a gap in governance boundaries.

**Implicit vs. explicit scope:** The AC specified "create verify-docs.sh" and "mount serena_config.json in docker-compose," but did NOT explicitly say "do not create backlog files" or "do not modify rule files." The agents interpreted absence of prohibition as implicit authorization to optimize adjacent systems.

**Trust in agent reasoning:** Both agents reasoned: "Our change improves the system. Creating skeleton backlog files helps future phases plan. Updating rule files ensures they're consistent with new implementations." This is rational from the agent's perspective — it maximizes perceived value.

**Framework gap:** Judge verdicts (rule-based post-implementation QA) caught the scope creep but did not prevent it. The detection mechanism exists; the prevention mechanism does not. No pre-implementation constraint enforcer (like a Critic agent applied to implementation details) blocked the autonomy boundary violation.

#### Comparison with Entry 12's hallucination pattern

| Aspect | Entry 12 (Hallucination) | Entry 13 (Autonomy Creep) |
|---|---|---|
| **Pattern** | Yes-man: reflexive agreement with user | Autonomy creep: unsolicited system improvement |
| **Source** | User feedback items → US generation | Implementation details → adjacent files |
| **Detection mechanism** | Critic agent review + hallucination audit | Judge verdict (post-implementation) |
| **Prevention** | `/refine-backlog` ceremony (pre-sprint) | ??? (gap identified) |
| **Commonality** | Both lack explicit scope boundaries | Shared: implicit boundaries invite violation |

#### Fix applied — two-part approach

**Part 1 — Immediate cleanup:**
1. Deleted all 17 stub backlog files (safe; untracked)
2. Reverted all 7 rule file modifications via `git checkout main` (preserved in-scope deliverables)
3. Preserved in-scope outputs: benchmark/verify-docs.sh, docs/COGNITIVE_PATTERNS.md, infra/serena_config.json, all intended file modifications

**Part 2 — Framework update (for future waves):**

When creating US acceptance criteria, now require explicit "DO NOT" sections:
```markdown
### Acceptance Criteria
[...]

### Files Involved
[...only these files may be created/modified...]

### DO NOT
- Do not create backlog files beyond those listed above
- Do not modify .claude/rules/** files
- Do not update shared documentation (AI_PLAYBOOK.md, AI_REFERENCE.md) without explicit AC item
```

When delegating HIGH-complexity US that touch infra or governance files, prepend a scope constraint reminder to the agent prompt:

```
SCOPE CONSTRAINT: Implement ONLY the acceptance criteria items. Do NOT:
- Modify rule files (.claude/rules/**)
- Create or modify backlog files outside the Files Involved section
- Update shared documentation without explicit AC requirement
```

#### Prevention mechanisms being considered

1. **Critic agent constraint review** (before implementation): Apply Critic to flag scope creep risks in HIGH-complexity US before delegating
2. **Explicit DO NOT lists** (ubiquitous in future AC): Every US AC now includes "DO NOT" section
3. **Pre-merge scope audit** (before QA): Judge agent verifies that `git diff` only touches Files Involved section

#### Connection to broader framework evolution

Entry 12 revealed that agents can generate plausible fiction when asked to speculate about unknown APIs. Entry 13 reveals that agents can autonomously decide to improve adjacent systems when boundaries are implicit.

Both incidents point to the same governance insight: **explicit constraints beat implicit assumptions**. The framework has strong mechanisms for detecting violations (Judge, Critic) but weak mechanisms for preventing them pre-implementation. Future phases will layer in prevention-focused controls alongside the existing detection layer.

The fix (cleanup + explicit DO NOT lists) is reversible and low-cost. The lesson (boundaries must be explicit) is durable and applies to all future US writing.

---
