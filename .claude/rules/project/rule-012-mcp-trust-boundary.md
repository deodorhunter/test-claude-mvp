---
id: rule-012
trigger: "When an agent integrates, queries, or registers any MCP server"
updated: "2026-03-31"
paths:
  - "ai/mcp/**"
---

# Rule 012 — MCP Trust Boundary

<constraint>
Every MCP server integration must: (1) be on the configured allowlist, (2) validate ALL schema fields (not just description) against injection patterns before use, (3) never cache OAuth tokens across requests, (4) pass output through `ai/context/sanitizer.py` before context inclusion, and (5) never mix session state across tenants.
</constraint>

<why>
45% of MCP servers contain command injection vectors. Full-Schema Poisoning (FSP) embeds malicious instructions in tool names, parameter names, and enum values — not just the description field. Cross-tenant session mixing = data breach. OAuth SPOF = credential exfiltration.
</why>

<pattern>
```python
# ✅ All schema fields validated, output sanitized, tenant-scoped
result = mcp_client.query(server_id, params, tenant_id=current_user.tenant_id)
assert server_id in MCP_ALLOWLIST
sanitized = sanitizer.clean(result)  # validates ALL fields

# ❌ Trust server output directly or cache OAuth cross-request
raw_result = mcp_client.query(server_id, params)  # no tenant scope, no sanitize
```
</pattern>
