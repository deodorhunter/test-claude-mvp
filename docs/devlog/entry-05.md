← [Back to DEVLOG index](../DEVLOG.md)

## Entry 5 — Reflexion: Honest Token Math

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

We debated whether to run a "reflexion" cycle (extract session learnings into permanent rules) after every User Story. The math argued against it:

- Running reflexion: ~3,000 tokens
- Loading the resulting rule in every future session: ~200 tokens/session
- Break-even: the rule must prevent one debugging loop in its first 5 sessions

The real leverage is cross-project. A rule discovered in project 1 that prevents the same mistake in projects 2–N pays back N-fold. But rule bloat is a real risk — dozens of reflexion rules accumulate and start costing more than they save.

The correct cadence: run reflexion once per **phase gate** (not per US). Each run should produce at most 1–3 rules. The bar: "if an agent had known this from the start, would it have saved at least one circuit-breaker trigger?" If yes, keep it. If no, discard it.

---
