← [Back to DEVLOG index](../DEVLOG.md)

## Entry 6 — The Plugin Architecture Path

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The project's governance layer was designed to be extractable from the start. The insight: only `docs/AI_REFERENCE.md` is project-specific. Everything else in `.claude/` is org-generic.

The natural growth path:

1. **Git template repo** — fork the repo, run `/init-ai-reference`, you have the full framework for a new project  
2. **Shared submodule** — `.claude/commands/` as a git submodule shared across all repos in the org  
3. **Plugin** — a formally versioned package with a manifest, installable into any project that supports Claude Code

This wasn't built upfront because the framework needed to evolve first. Premature extraction would have locked in early mistakes as API surface.

---
