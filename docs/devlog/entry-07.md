← [Back to DEVLOG index](../DEVLOG.md)

## Entry 7 — EU AI Act Compliance Layer

*(Original notes, in Italian, written during the first experiments with Claude Code.)*

As the framework matured, a compliance audit found five categories of risk from common agentic tooling (multi-provider routing, external session sync, plugin marketplaces, autonomous modes):

- **GDPR Art. 46** (data transfers) — sending code to non-EEA AI providers without a data processing agreement
- **EU AI Act Art. 10** (data governance) — session replay files that capture code and sync externally
- **EU AI Act Art. 12** (logging) — mutable local files don't satisfy tamper-proof logging requirements for high-risk AI
- **EU AI Act Art. 14** (human oversight) — autonomous modes that advance without human checkpoints
- **Supply chain risk** — public plugin marketplaces with unreviewed code execution

The framework's explicit provider allowlist, mandatory phase-gate checkpoints, local-only session notes, and rejection of external notification services are all responses to these risks — not over-engineering, but minimum necessary controls for enterprise deployment.

---
