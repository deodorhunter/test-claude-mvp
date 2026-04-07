---
name: command-name
description: "One sentence: what this command does and when to invoke it."
version: "1.0"
type: command
model: haiku
destructive: false
output: "[where output goes, e.g., docs/file.md (append-only)]"
speed: 1
trigger: "/command-name"
parallel_safe: true
---

# Command: /command-name
> [Brief one-line description of purpose]
> Invocation: type `/command-name` in the chat.

---

<identity>
[What this command does, what it produces, and what it does NOT do.]
</identity>

<hard_constraints>
1. [Command-specific constraint]
2. MAX OUTPUT: [what to output and what NOT to output]
3. NO SIDE EFFECTS: [what the command must not modify]
</hard_constraints>

<workflow>
<step_1>
[What to do first — typically: read from context, recall from history, or ask user]
</step_1>
<step_2>
[Main processing step]
</step_2>
<step_3>
[Output step — write to file or return to user]
</step_3>
</workflow>

<output_format>
[Exact structure of what this command returns. Use markdown tables, lists, or code blocks as needed.]
</output_format>

<!--
TEMPLATE USAGE
──────────────────────────────────────────────────────────────────
1. Copy to .claude/commands/[name].md
2. Fill all frontmatter fields
3. Keep workflow steps concrete and sequential
4. Specify output_format exactly — commands are called programmatically
5. Keep file under 60 lines
-->
