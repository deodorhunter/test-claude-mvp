# US-020 Done — plone-mcp Self-Hosted MCP Server + Python Adapter

**Status:** Complete
**Phase:** 2d (addition)
**Date:** 2026-03-31

## Summary

Integrazione di https://github.com/plone/plone-mcp come servizio self-hosted Docker,
con Python adapter per il MCP registry della piattaforma.

## Files Created / Modified

| File | Action |
|------|--------|
| `infra/plone-mcp/` | Cloned upstream (shallow, no .git) |
| `infra/plone-mcp/src/index.ts` | Patched: added SSE transport via `TRANSPORT=sse` env var |
| `infra/docker/Dockerfile.plone-mcp` | New — Node.js 20-alpine multi-stage build |
| `infra/docker-compose.yml` | Added `plone-mcp` service (port 9120) |
| `ai/mcp/servers/plone.py` | New — `PloneMCPServer(MCPServer)` calling Plone REST API directly |
| `ai/mcp/registry.py` | Added `MCP_ALLOWLIST`, optional `allowlist` param to `MCPRegistry` |
| `backend/tests/test_plone_mcp.py` | New — 12 tests covering happy path, errors, sanitization, allowlist |
| `.env.example` | Added `PLONE_USERNAME`, `PLONE_PASSWORD`, `PLONE_MCP_URL` |
| `docs/AI_REFERENCE.md` | Updated: new service, new env vars, new file paths |
| `docs/backlog/US-019.md` | Status → ✅ Done |
| `docs/backlog/BACKLOG.md` | US-019 ✅ Done, US-020 added Phase 2d, Phase 3 slot renumbered |
| `docs/backlog/US-020.md` | New US file |

## Architecture

```
plone-mcp Docker (port 9120)        Python PloneMCPServer
  Node.js 20-alpine                   ai/mcp/servers/plone.py
  upstream plone-mcp + SSE patch  ←─  calls Plone REST API directly
  TRANSPORT=sse                        (independent of Node.js service)
  depends_on: plone (8080)
```

- **Docker service**: self-hosted plone-mcp for external MCP clients (Claude Desktop)
- **Python adapter**: calls `PLONE_BASE_URL/@search` directly for internal platform use
- **Dual architecture**: both components are "plone-mcp integration"

## Key Design Decisions

1. **No proxy through Node.js**: Python adapter calls Plone REST API directly.
   Node.js service is for external MCP clients only.
2. **SSE patch minimal**: ~25 lines added to `run()` in `src/index.ts`, original stdio behavior unchanged.
3. **Allowlist opt-in**: `MCPRegistry(allowlist=MCP_ALLOWLIST)` in production; `MCPRegistry()` for tests (backward compat).
4. **trust_score = 0.85**: first-party CMS, above default min_confidence 0.5.

## Test Results

```
12 passed (test_plone_mcp.py)
59 passed (test_plone_mcp + test_mcp + test_mcp_full + test_context_builder)
0 regressions
```

## Constraints Respected

- All external calls mocked (no real Plone, no real network)
- Output always passed through `sanitizer.sanitize()` (rule-012)
- Allowlist enforcement available via `MCPRegistry(allowlist=MCP_ALLOWLIST)`
- PLONE_PASSWORD marked as `:?required` in docker-compose (never hardcoded)
- No OAuth tokens — Basic auth per-request (rule-012 § OAuth SPOF)
