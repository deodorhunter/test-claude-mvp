---
type: reference
version: "1.0"
audience: developers
updated: "2026-04-02"
related: [AI_PLAYBOOK.md, .claude/commands/]
---

# Cognitive Patterns — Learn, Judge, Notepad, Reflexion, Deep-Interview

Five reusable Claude Code commands that implement decision-making and insight capture rituals. Each pattern solves a specific problem in the development workflow.

---

## Pattern Catalog

| Command | Type | Classification | Trigger | Token Cost |
|---|---|---|---|---|
| `/learn` | Insight capture | Automatable | `/learn [insight]` | ~1.5k input / 500 output |
| `/judge` | Acceptance check | Manual-only | `/judge US-NNN` | ~2.0k input / 300 output |
| `/notepad` | Memory capture | Manual-only | `/notepad [category] [entry]` | ~200 input / 100 output |
| `/reflexion` | Rule extraction | Automatable (phase gate) | `/reflexion Phase-N` | ~3.0k input / 1.2k output |
| `/deep-interview` | Requirement elicitation | Manual-only | `/deep-interview [topic]` | ~2.5k input/round |

---

## Pattern Reference

### 1. `/learn` — Insight Distiller
**File:** `.claude/commands/learn.md`

**Purpose:** Captures non-googleable, context-specific insights from the session before they disappear from context.

**When to use:**
- After debugging a tricky issue tied to the project's specific stack
- When discovering an unexpected constraint that surprised you
- When learning about framework behavior not in docs

**Quality gate:** Passes only if all three are true:
- Non-googleable (not in Stack Overflow or framework docs)
- Context-specific (unique to this project)
- Hard-won (took ≥1 debugging attempt to discover)

**Output:** Appends to `docs/.session-notes.md` via `/notepad`

**Classification:** **Automatable** — can be hooked post-phase-gate to extract learnings from session history

**Token cost:** ~1.5k input (diff/context reading) + 500 output (formatted note)

---

### 2. `/judge` — Pre-QA Acceptance Verifier
**File:** `.claude/commands/judge.md`

**Purpose:** Lightweight post-implementation check. Reads git diff and US acceptance criteria, returns per-criterion PASS/FAIL/UNCLEAR verdict.

**When to use:**
- After an implementing agent finishes but before QA or DocWriter
- To catch obvious failures early (costs ~2k tokens vs. 10k+ QA cycle)
- Never if you ran the judge yourself — neutral third party required for approval

**Output:** Inline verdict table with evidence references

**Classification:** **Manual-only** — requires orchestrator judgment to interpret "UNCLEAR" and route re-delegation

**Token cost:** ~2.0k input (diff parsing + AC reading) + 300 output (verdict table)

---

### 3. `/notepad` — Session Memory Capture
**File:** `.claude/commands/notepad.md`

**Purpose:** Lightweight in-session institutional memory. Appends timestamped entries to `docs/.session-notes.md` under four categories.

**When to use:**
- Any time you discover something worth remembering in a future session
- Before running `/compress-state` (captures session state before clearing)
- Paired with `/learn` and `/deep-interview` for persistence

**Categories:**
- **Learnings:** Something discovered that changes approach to future work
- **Decisions:** Architectural or process decisions with rationale
- **Issues:** Active problems being tracked
- **Problems:** Patterns of failure observed

**Output:** Appends to `docs/.session-notes.md` (gitignored)

**Classification:** **Manual-only** — human judgment required to decide what's worth noting

**Token cost:** ~200 input (category validation) + 100 output (confirmation)

---

### 4. `/reflexion` — Phase-Gate Rule Extractor
**File:** `.claude/commands/reflexion.md`

**Purpose:** Extracts 1–3 durable rules from completed phase history and saves them to `.claude/rules/project/`. Run once per phase gate.

**When to use:**
- Mandatory at every phase gate (Phase 4, step 6)
- Never per-US — over-extraction creates rule bloat
- Only after reviewing circuit-breaker triggers and QA bounce-backs

**Token ROI test (mandatory):**
- Each rule saves ~15k tokens per avoided debugging loop (5 future sessions × 2 failures = breakeven)
- Each rule costs ~200 tokens per future session it's loaded
- Must pass survival test: "Would knowing this have prevented at least one circuit-breaker trigger or QA bounce-back?"

**Output:** 0–3 new rule files in `.claude/rules/project/`, plus CLAUDE.md import proposal

**Classification:** **Automatable** — technically self-contained, but human sign-off required (Tech Lead decides which rules activate in CLAUDE.md)

**Token cost:** ~3.0k input (phase history synthesis) + 1.2k output (rule files + report)

---

### 5. `/deep-interview` — Socratic Requirement Elicitation
**File:** `.claude/commands/deep-interview.md`

**Purpose:** Extracts precise, testable requirements from fuzzy user intent through one-question-per-round Socratic dialogue. Stops when AC can be written without ambiguity.

**When to use:**
- Before creating a vague User Story
- When user intent conflicts with feasibility
- When acceptance criteria would have >2 `[ASSUMPTION: ...]` annotations

**Constraints:**
- ONE QUESTION PER ROUND (ask exactly one, wait for answer)
- NO LEADING QUESTIONS (surface disagreement, don't confirm expectations)
- MAX 7 ROUNDS (if still ambiguous, write AC with explicit assumptions)
- NO STATE FILES (persist discoveries via `/notepad` only)

**Output:** 3–5 non-ambiguous acceptance criteria, persisted to `docs/.session-notes.md`

**Classification:** **Manual-only** — user must be present to answer questions

**Token cost:** ~2.5k input per round (reading intent + prior answers) + 300 output (next question)

---

## Automation & Hook Potential

### Automatable Patterns (Hook-Eligible)

**`/reflexion`** (Phase Gate)
```
Trigger: On `make up && make migrate && make test` passes
Action: Run /reflexion Phase-N automatically
Output: Proposed rules written, awaiting Tech Lead approval in CLAUDE.md
Estimated savings: 30 min orchestrator time per phase gate
```

**`/learn`** (Post-Phase-Gate Bulk Capture)
```
Trigger: Batch mode after phase gate
Action: Scan docs/.session-notes.md for high-confidence learnings
Filter: Quality gate (googleable check + context check)
Output: Pre-collected insights for next session's context
Estimated savings: 5 min insight review per session
```

### Manual-Only Patterns (Require Human Judgment)

**`/judge`** — Requires orchestrator to interpret ambiguity and decide re-delegation

**`/notepad`** — Requires human to decide what's important enough to persist

**`/deep-interview`** — Requires user to answer questions and guide requirements

---

## Integration with Speed 2 Workflow

| Phase | Applicable Patterns | Typical Invocation |
|---|---|---|
| **Planning (Phase 1)** | `/deep-interview` | Clarify vague requirements before creating US |
| **Delegation (Phase 2)** | `/judge` | Post-implementation check before QA |
| **Phase Gate (Phase 4)** | `/reflexion` + `/notepad` | Rule extraction + session memory capture |
| **Between Sessions** | `/learn` + `/compress-state` | Persist insights, clean context |

---

## Token Budget Reference

For a typical phase (6 US, 3 agents, phase gate):

| Operation | Count | Total Tokens |
|---|---|---|
| `/judge` (post-US) | 6× | ~14.4k |
| `/learn` (high-confidence insights) | 2–3× | ~4.5k |
| `/reflexion` (end-of-phase) | 1× | ~4.2k |
| `/notepad` (session memory) | ~5× | ~1.5k |
| **Phase subtotal** | — | ~24.6k |

---

## See Also

- `AI_PLAYBOOK.md` — Overview of Speed 1 vs. Speed 2 workflows
- `.claude/commands/` — Full command source files
- `CLAUDE.md` — Governance rules and phase workflow
