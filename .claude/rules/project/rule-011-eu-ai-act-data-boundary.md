---
id: rule-011
trigger: "When any agent or tool integration could transmit code, schema, or session data outside the project directory"
updated: "2026-03-31"
---

# Rule 011 — EU AI Act Data Boundary

<constraint>
AI processing uses only configured providers (Ollama local, Claude API with EU DPA). No code/schema/session data transmitted to third-party services (Discord, Slack, plugin marketplaces, session sync). Phase-gate checkpoints mandatory — no autonomous bypass. Session replay never committed or synced.

Exception: Context7 MCP server (`mcp.context7.com`, Upstash US) receives library names and query strings only — not source code, schema, or session data — for documentation lookup. GDPR Art. 46 [Verified — EUR-Lex](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679) safeguard required: obtain Upstash DPA or verify Standard Contractual Clauses (SCCs) are in place before production use.
</constraint>

<why>
GDPR Art. 46 (data transfers), EU AI Act Art. 14 (human oversight), Art. 9 (supply chain risk). Non-compliance = regulatory exposure.
</why>

<pattern>
Permitted from oh-my-claudecode: critic agent, evidence-driven verification, notepad wisdom (local only), atomic changes, authoring/review separation.
Rejected: plugin marketplace, external notifications, `.omc/` session sync, multi-provider routing, autopilot mode.

<mcp_gap>
MCP-specific: stdio transport has no sandboxing; OAuth tokens cached cross-request = SPOF; cross-tenant session state = breach. Apply rule-012 for all MCP integrations.
</mcp_gap>
</pattern>
