---
description: "When any agent adds validation or enforcement logic to an existing registry or manager class that has existing callers"
paths:
  - "ai/mcp/**"
  - "backend/app/**"
---

<metadata>
  id: rule-014
  updated: "2026-03-31"
</metadata>

# Rule 014 — Registry Enforcement Must Be Opt-In

<constraint>
New enforcement added to an existing registry or manager class must be opt-in via an explicit parameter (e.g., allowlist=None) with the original permissive behavior as default.
</constraint>

<why>
Hardcoded enforcement against existing callers breaks all test fixtures using mock names — ~26 tests failed immediately in Phase 2d until allowlist was made a parameter (incident: MCPRegistry.register()).
</why>

<pattern>
```
✅ def register(self, server, allowlist=None):
       if allowlist is not None and server.name not in allowlist:
           raise ...
❌ def register(self, server):
       if server.name not in MCP_ALLOWLIST:   # hardcoded, breaks all fixtures
           raise ...
```
</pattern>
