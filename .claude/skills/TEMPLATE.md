---
name: skill-name
description: "One sentence: what this skill teaches and when to apply it."
---

<insight>
[Core idea in 1-2 sentences. What is the key insight this skill captures?]
</insight>

<why_this_matters>
[1-2 sentences. What goes wrong without this skill? What does it save — time, tokens, failures?]
</why_this_matters>

<recognition_pattern>
[Describe the situation where this skill applies. Agent should self-activate when it sees this pattern.]
</recognition_pattern>

<approach>
[Step-by-step or bullet-point procedure. Concrete and actionable. Max 10 bullets.]
</approach>

<example>
```
✅ [Concrete correct usage]
❌ [What to avoid]
```
</example>

<!--
TEMPLATE USAGE
──────────────────────────────────────────────────────────────────
1. Copy to .claude/skills/[kebab-name].md
2. Fill name, description, trigger, updated
3. Keep each XML section concise — skills are loaded on-demand but still cost tokens
4. No external state files (.omc/, .json) — persist state via /notepad → docs/.session-notes.md
5. Keep file under 50 lines
-->
