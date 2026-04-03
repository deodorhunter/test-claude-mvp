← [Back to DEVLOG index](../DEVLOG.md)

## Entry 9 — The Rule / Skill / Command Architecture Decision

A recurring design question when adding governance: *which format does this belong in?* The question surfaced concretely when encoding Hart's Rules for audience-aware writing. It felt like a rule, but the decision revealed a cleaner architecture.

**The three formats and their jobs:**

- **Rule** = a behavioral red line. Any agent could violate it. The constraint must be active whenever a matching action is possible. Example: tenant isolation — any backend agent writing a DB query could accidentally omit the `tenant_id` filter. The rule loads for all `backend/**` work.
- **Skill** = a procedure for doing something well, loaded when a specific task type begins. The agent self-activates it at task entry. Example: speed2-delegation — only the orchestrator needs it, only when delegating. Zero cost otherwise.
- **Command** = a user-invoked macro. The human decides when to run it. Example: `/compress-state`, `/reflexion`. Zero cost until called.

**The token cost model is the deciding factor:**

Rules are always-loaded (within their path scope) — every token in a rule costs tokens in every matching session, forever. Skills and commands cost zero until triggered. This means the Rule format should be reserved for constraints where the *cost of not loading it* (a data breach, a QA bounce-back, a compliance violation) exceeds the *cost of loading it* in every session.

**Hart's Rules as the worked example:**

Audience-aware writing *feels* like a governance rule. But only `doc-writer` uses it, only during Mode B. A path-scoped Rule on `docs/**` would load for any agent injecting a `<file>` tag pointing at a doc — the orchestrator, backend-dev, anyone. Most of those agents have no use for writing register guidance. Result: rule loads in dozens of sessions where it does nothing.

As a Skill (`writing-audience.md`), it costs zero until `doc-writer` enters Mode B and explicitly loads it. The constraint is equally enforced; the token cost is a fraction.

**Decision rule (meta-rule for future governance additions):**
> Could any agent violate this, on any task? → Rule. 
> Is this a procedure for one specific agent or task type? → Skill. 
> Does a human need to invoke this explicitly? → Command.

---
