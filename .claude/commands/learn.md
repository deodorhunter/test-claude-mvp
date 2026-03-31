---
name: learn
description: "Distills a hard-won insight from the current session into a reusable note. Quality gate: only non-googleable, context-specific, painful-to-rediscover insights pass. Routes to expertise notes (how-it-works) or workflow notes (what-to-do-when). Appends to docs/.session-notes.md via /notepad."
version: "1.0"
type: command
model: claude-haiku-4-5-20251001
destructive: false
output: "docs/.session-notes.md (append via /notepad)"
speed: 1
trigger: "/learn [insight]"
parallel_safe: true
---

# Command: /learn
> Captures a hard-won insight before it disappears from context.
> Appends to `docs/.session-notes.md` via `/notepad`.
> Invocation: type `/learn [describe the insight]` in the chat.

---

<identity>
Quality-gated insight distiller. Most things agents "learn" during a session are either googleable, temporary, or too narrow to reuse. This command filters those out and saves only the insights worth paying context overhead for in future sessions.
</identity>

<hard_constraints>
1. QUALITY GATE — all three must be true to save: (a) non-googleable: not in framework docs or Stack Overflow top results, (b) context-specific: arises from THIS project's specific stack/constraints, (c) hard-won: took ≥1 debugging attempt or false assumption to discover.
2. NO BLOAT: If the insight is covered by an existing rule (001-012) or CLAUDE.md → discard it. Duplicate rules waste context.
3. ROUTE CORRECTLY: expertise note (how the system works) vs workflow note (what to do when X happens). Tag accordingly.
4. ONE NOTE PER CALL: One insight per `/learn` invocation. If session had 3 insights, call `/learn` 3 times.
5. APPEND ONLY: Use `/notepad` → `docs/.session-notes.md`. Never overwrite.
</hard_constraints>

<workflow>
<step_1>
Apply the quality gate. Ask: (a) Is this googleable? (b) Is it specific to this project? (c) Was it painful to discover?
If any answer is No → output "DISCARDED: [reason]" and stop.
</step_1>
<step_2>
Classify: `[EXPERTISE]` (how the system works) or `[WORKFLOW]` (what to do when X).
</step_2>
<step_3>
Write the note in ≤5 lines. Format:
```
[LEARN][TYPE] YYYY-MM-DD: [title]
Context: [1 sentence — what were you doing when this came up]
Insight: [the hard-won fact]
Application: [when to apply this]
```
</step_3>
<step_4>
Append via `/notepad`. Output confirmation.
</step_4>
</workflow>

<output_format>
If saved:
SAVED [EXPERTISE/WORKFLOW]: "[title]" → docs/.session-notes.md

If discarded:
DISCARDED: [reason — googleable / already in rule-NNN / too narrow]
</output_format>
