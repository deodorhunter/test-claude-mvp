← [Back to DEVLOG index](../DEVLOG.md)

## Entry 3 — Research Synthesis: What the Ecosystem Had Learned

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

Before building further, we reviewed the external literature and frameworks. The sources consulted:

- [Ultrathink (claudelog.com)](https://claudelog.com/mechanics/ultrathink/)
- [Bash Scripts batch writes (claudelog.com)](https://claudelog.com/mechanics/bash-scripts/)
- [Context Window Depletion (claudelog.com)](https://claudelog.com/mechanics/context-window-depletion/)
- [Tactical Model Selection (claudelog.com)](https://claudelog.com/mechanics/tactical-model-selection/)
- [Sub-agent Tactics (claudelog.com)](https://claudelog.com/mechanics/sub-agent-tactics/)
- [Anthropic Skills Spec](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [NeoLab Context Engineering Kit](https://github.com/NeoLabHQ/context-engineering-kit)
- [oh-my-claudecode](https://github.com/Yeachan-Heo/oh-my-claudecode)

**What we adopted:**

- `ultrathink` keyword for HIGH-complexity tasks — triggers extended thinking in Sonnet at near-zero extra token cost
- Proactive context budget threshold — rather than waiting for degradation, trigger state compression after 15+ tool calls
- Destructive/non-destructive task classification before parallelizing — a more fundamental question than "do these touch different files?"
- "Consolidate → clear → act" between parallel agent waves — prevents context pollution from half-finished parallel threads
- Critic agent pattern (from oh-my-claudecode) — a dedicated agent challenges plans before any implementing agent is spawned
- Evidence-driven verification — every "pass" verdict requires actual terminal output, not assertions
- Separation of authoring and review — the agent that implements a feature must never be the one that verifies it

**What we rejected and why:**

- NeoLab CEK as a package — their orchestration instructions would collide with our custom Tech Lead agent
- Mandatory Tree-of-Thoughts on every task — 3–5× token cost for marginal gain over `ultrathink`
- LLM-as-Judge on every User Story — ~5,000–10,000 tokens per US × 35 US = up to 350,000 extra tokens with no meaningful QA improvement over human checkpoints
- oh-my-claudecode's plugin marketplace, external notifications, session sync, multi-provider auto-routing — all ruled out by EU AI Act compliance requirements (data boundary, provider allowlist, mandatory human checkpoints)

---
