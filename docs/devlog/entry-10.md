← [Back to DEVLOG index](../DEVLOG.md)

## Entry 10 — EU AI Act Citations, Confidence Scores, and the Auto-Review Mechanism

Three separate decisions landed in the same session and reinforced each other.

### The EU AI Act coverage problem

The framework had a compliance section in `FRAMEWORK_README.md`, but it was thin: six table rows, no article citations, no audience differentiation. "EU AI Act compliant" in the header was closer to a badge than a proof. A systematic review of all front-door documents (README.md, AI_PLAYBOOK.md, HOW-TO-ADOPT.md) found that none of them named the regulation at all — they used "compliance" and "data boundary" as stand-in phrases.

This is a real problem for a specific audience. A CEO evaluating whether to adopt the framework doesn't know what "compliance" means without context — it could mean anything from PCI-DSS to internal code review policy. A DPO doing an audit needs article numbers and evidence locations, not prose assertions. The fix was to differentiate coverage by audience:

- **CEO/board**: lead with the liability exposure — Regulation (EU) 2024/1689 Art. 99(3) specifies penalties up to €30M or 6% of global turnover. Name the regulation; cite the penalty.
- **PM/project lead**: a control-mapping table showing each article, the framework's concrete control, and exactly which file proves it.
- **Security/DPO**: technical control descriptions — not "we protect your data" but "append-only `echo >>` enforced by command constraint, evidence at `docs/ARCHITECTURE_STATE.md`."
- **Developer**: two sentences explaining what Art. 14 (human oversight) and GDPR Art. 46 (data transfers) mean in day-to-day workflow.

The canonical compliance map lives in `docs/FRAMEWORK_README.md`. All other documents reference it rather than duplicating it. This means a single update to the compliance map propagates everywhere.

### The confidence score convention

The harder problem: we can't verify every article citation with certainty from within a coding session. The EU AI Act's Annex III (high-risk AI classification) is particularly context-dependent — whether a specific system qualifies depends on its deployment scope and sector, which requires legal judgment we can't substitute.

The established convention: every regulatory citation carries a confidence score inline.

- ★★★ = verified against official regulation text
- ★★☆ = cross-referenced, plausible, but not confirmed against primary source
- ★☆☆ = inferred — flag explicitly for legal review before relying on it

This isn't defensive hedging — it's accurate communication. A DPO reading a document with all ★★★ citations and no caveats would have no signal about which claims need independent verification. The ★★☆ on Annex III classification is more honest than a silent ★★★ would be. And it's actionable: anyone reading it knows to take that specific point to legal counsel.

The convention was also added as a formal register to `writing-audience.md` (Security/Legal/DPO register), so any future document targeting compliance audiences inherits the citation discipline automatically.

### The benchmark number problem

A subtler error surfaced during the review: the README claimed "a reduction of more than 90%" as a single figure. This conflated two different measurements:

1. **Context loading reduction**: from 60,764 to 32,936 bytes = −46%, measured by `benchmark/measure-context-size.sh`. This is about what loads in the model's context at session start.
2. **Per-task cost reduction**: 200,000+ API units (unstructured) down to <10,000 (structured) = up to 20×. This is about how many tokens a single task consumes when the agent role is bounded.

These are different claims about different things measured different ways. "90% reduction" implied they were the same metric. Someone checking the benchmark files would immediately see the −46% figure and distrust the rest of the claims. The fix was to state both metrics separately with their sources.

The lesson: performance claims in evaluator-facing docs must be traceable to a specific measurement, stated with the correct unit, and never averaged or combined across incompatible metrics.

### The auto-review mechanism

All of the above issues — wrong register, missing citations, conflated metrics, residual jargon — were found by a manual review pass at the end of the session. There was no systematic checklist. The review relied on the reviewer remembering what to look for.

The `/review-session` command formalizes this as a repeatable 7-check procedure: register audit, EU AI Act coverage, benchmark accuracy, citation confidence, link validity, ADAPT marker scan, residual jargon. Running it takes the same time as the manual pass but produces a structured report and catches things that manual review misses under cognitive load at the end of a long session.

The meta-insight: governance quality degrades fastest at session end, when the implementer is closest to the work and farthest from the reader's perspective. A command that runs the reviewer's checklist mechanically is most valuable precisely when the implementer least wants to run it.

---
