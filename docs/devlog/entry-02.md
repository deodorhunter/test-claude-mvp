← [Back to DEVLOG index](../DEVLOG.md)

## Entry 2 — The Deterministic Compiler Mental Model

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

The shift that unlocked the framework: stop thinking of Claude as a chatbot and start thinking of it as a **deterministic compiler**.

A compiler doesn't explore your filesystem. You hand it exactly the files it needs, and it produces exactly the output you specified. If you hand it bad input, it errors with a clear message rather than guessing. This is the contract we wanted.

Six architectural pillars emerged from this mental model:

1. **Push Context** — agents are forbidden from exploring the file system. Files must be explicitly passed to them. The agent never discovers; it receives.
2. **Tool Muzzling** — all commands the AI runs (`pytest`, `pip`, `npm`) must be silenced. Install logs, build output, test runner noise — none of it should enter the context window.
3. **Circuit Breakers** — maximum 2 debug attempts per failing command. On the third failure, stop and ask a human. This prevents the infinite retry loops that burn through token budgets.
4. **Targeted Editing** — no full-file rewrites. The agent uses surgical edit tools. A 300-line file that needs 3 lines changed should produce exactly 3 changed lines, not 300.
5. **Git Diff Reviews** — QA agents and documentation agents don't read source files; they read `git diff`. This enforces the "smallest correct change" principle on the reviewer side too.
6. **Dual-Speed Workflow** — Speed 1 for fast fixes (the agent acts like a senior developer with scoped files), Speed 2 for full features (an orchestrator decomposes the work and delegates to specialist subagents). These two modes have different cost profiles, different models, and different governance requirements.

---
