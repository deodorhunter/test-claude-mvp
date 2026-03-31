---
id: rule-NNN
trigger: "When an agent [action that triggers this rule]"
updated: "YYYY-MM-DD"
---

# Rule NNN — [Title]

<constraint>
[One sentence: the exact behavioural constraint the agent must follow.]
</constraint>

<why>
[One sentence: consequence if ignored — token cost, data breach, etc.]
</why>

<pattern>
```
✅ [Correct usage]
❌ [What to avoid]
```
</pattern>

<!--
TEMPLATE USAGE
──────────────────────────────────────────────────────────────────
1. Copy to .claude/rules/project/rule-NNN-[kebab-name].md
2. Fill id, trigger, updated
3. Keep <constraint> to 1 sentence. <why> to 1 sentence.
4. <pattern> is optional — only add if it prevents misreading
5. Keep file under 20 lines — rules are loaded every session
-->
