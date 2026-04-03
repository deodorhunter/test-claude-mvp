← [Back to DEVLOG index](../DEVLOG.md)

## Entry 1 — Naming the Problem: Agentic Bloat

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The first discovery when switching from a passive assistant (Copilot) to an autonomous agent (Claude Code): if you ask the agent to "fix a bug" without any structure, it doesn't fix the bug. It first needs to *understand* the project. So it runs `ls`, `find`, `cat` — it explores the entire codebase before touching a single file, consuming tens of thousands of tokens on reconnaissance before writing a single line of code. For a trivial task this could cost $2–3 and introduce hallucinations from stale context.

We called this **Agentic Bloat**: the tendency of autonomous AI loops to expand their context window with irrelevant information until most of the compute is spent processing the agent's own previous mistakes rather than the actual task.

The insight was that this isn't a model quality problem — it's a governance problem. An agent with no constraints will always seek to maximize its context before acting, because that's the safe strategy from the model's perspective. We needed to make exploration impossible and surgical action the only available path.

---
