---
name: notepad
description: "Lightweight in-session institutional memory. Appends timestamped entries to docs/.session-notes.md under four categories: Learnings, Decisions, Issues, Problems. Inspired by oh-my-claudecode's notepad wisdom system. Gitignored — operational state only."
version: "1.0.0"
type: command
model: claude-haiku-4-5-20251001
allowed_tools: [bash, write]
destructive: false
output: docs/.session-notes.md
trigger: "/notepad [category] [entry]"
parallel_safe: true
---

<identity>
Session notepad. Captures timestamped, categorized observations during a session so they survive /compress-state and can be synthesized into rules at the next /reflexion run. Operates entirely in append mode — never overwrites.
</identity>

<hard_constraints>
1. FOUR CATEGORIES ONLY: Learnings, Decisions, Issues, Problems. Reject any other category.
2. APPEND-ONLY: Always `echo >>`. Never overwrite docs/.session-notes.md.
3. NO AUTO-LOAD: Notes are NOT injected into agent context automatically. Only read when explicitly requested.
4. NO COMMIT: docs/.session-notes.md must remain gitignored (add to .gitignore if not present).
5. ARCHIVE ON COMPRESS: /compress-state archives the current notes block with a datestamp before synthesizing. Each new session starts fresh.
6. EU AI ACT (rule-011): Notes stay in the project directory. Never sync to external services.
</hard_constraints>

<workflow>
1. Validate category is one of: Learnings, Decisions, Issues, Problems.
2. Append to `docs/.session-notes.md`:
   ```bash
   echo "### [$(date +%Y-%m-%dT%H:%M)] [CATEGORY]" >> docs/.session-notes.md
   echo "[entry text]" >> docs/.session-notes.md
   echo "" >> docs/.session-notes.md
   ```
3. Ensure `docs/.session-notes.md` is gitignored:
   ```bash
   grep -q '.session-notes.md' .gitignore 2>/dev/null || echo 'docs/.session-notes.md' >> .gitignore
   ```
4. Confirm with 1-line acknowledgement.

### Categories
- **Learnings**: Something discovered that changes how to approach future work (e.g. "Serena doesn't index files >5MB")
- **Decisions**: Architectural or process decisions made this session with rationale
- **Issues**: Active problems being tracked (e.g. "docker exec fails with PYTHONPATH missing")
- **Problems**: Patterns of failure observed (e.g. "third time alembic autogenerate missed enum change")
</workflow>

<output_format>
✅ Noted [CATEGORY]: [first 60 chars of entry]
</output_format>
