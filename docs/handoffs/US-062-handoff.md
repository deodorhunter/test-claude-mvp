# US-062 Handoff — Plone-MCP Architecture Clarification

**Date:** 2026-04-03 | **Agent:** doc-writer | **Status:** COMPLETE

---

## What Was Built

Clarified Plone integration architecture across three distinct components (auth bridge, MCP server, Python adapter, plugin placeholder) via docstrings, README sections, architecture diagram, and plugin manifest notes. Eliminated confusion between PloneIdentityAdapter (JWT auth layer) and plone-mcp Node.js server (content operations layer).

**Key Decisions:**
- Module-level docstring in `plone_bridge.py` explicitly states "NOT an MCP adapter" and cross-references architecture document
- "Architecture Note" section in `infra/plone-mcp/README.md` clarifies purpose and distinguishes from auth bridge
- Text diagram in `docs/ARCHITECTURE_STATE.md` shows all 4 touchpoints (auth adapter, MCP server, Python wrapper, plugin placeholder) with data flow
- `PLUGIN_MANIFEST.md` clarifies `plone_integration` is a project-specific placeholder (not part of org plugin); documents future purpose (content sync)

---

## Integration Points

**File Ownership:**
- `backend/app/auth/plone_bridge.py` — JWT auth layer; module docstring added; consumed by: auth endpoints, Plone identity lookup
- `infra/plone-mcp/README.md` — content operations guide; "Architecture Note" section added; clarifies purpose vs auth bridge
- `docs/ARCHITECTURE_STATE.md` — append-only architecture log; "Plone Integration Points" section added with diagram
- `PLUGIN_MANIFEST.md` — org plugin roadmap; "Project-Specific Plugins" section clarifies plone_integration status

**Documentation Consumers:**
- New developers onboarding: reference the text diagram in ARCHITECTURE_STATE.md
- MCP integration work (Phase 3+): refer to plone-mcp README "Architecture Note" to avoid confusing with auth
- Plugin roadmap discussions: see PLUGIN_MANIFEST.md "plone_integration" section for future sync plugin context

---

## Residual Risks

**LOW:** Cross-repo documentation sync. If `infra/plone-mcp/` is pulled from upstream (plone/plone-mcp), the "Architecture Note" section must be re-added (not in upstream). Mitigation: document in PR checklist.

**LOW:** Plugin implementation timing. `plone_integration` plugin is marked as placeholder; implementation depends on project scope creep decisions (Phase 4+). No risk to current phase.

---

## Manual Test Instructions

```bash
# Verify plone_bridge.py has module docstring
head -25 /Users/martina/personal-projects/test-claude-mvp/backend/app/auth/plone_bridge.py | grep -A 3 '"""'
# Expected: docstring starting with "Plone JWT Authentication Bridge"

# Verify plone-mcp README has Architecture Note section
grep -A 5 "## Architecture Note" /Users/martina/personal-projects/test-claude-mvp/infra/plone-mcp/README.md
# Expected: section explaining MCP != auth, with clear distinction

# Verify ARCHITECTURE_STATE.md has Plone Integration Points section
tail -50 /Users/martina/personal-projects/test-claude-mvp/docs/ARCHITECTURE_STATE.md | grep -A 10 "Plone Integration"
# Expected: text diagram showing 4 components, data flow, and clear purpose labels

# Verify PLUGIN_MANIFEST.md has plone_integration clarification
grep -A 10 "### plone_integration Plugin" /Users/martina/personal-projects/test-claude-mvp/PLUGIN_MANIFEST.md
# Expected: status "Placeholder", capabilities: [] shown, future purpose described
```

---

## Automated Test Commands

```bash
# Check that no hyperlinks are broken (internal references only)
grep -r "plone_bridge\|plone-mcp\|plone_integration" \
  /Users/martina/personal-projects/test-claude-mvp/docs/ARCHITECTURE_STATE.md \
  /Users/martina/personal-projects/test-claude-mvp/PLUGIN_MANIFEST.md \
  /Users/martina/personal-projects/test-claude-mvp/infra/plone-mcp/README.md
# Expected: all file paths exist and can be verified

# Verify no conflicting statements in docstring vs README
grep "JWT\|MCP" /Users/martina/personal-projects/test-claude-mvp/backend/app/auth/plone_bridge.py | head -3
grep "MCP" /Users/martina/personal-projects/test-claude-mvp/infra/plone-mcp/README.md | grep "Architecture Note" -A 2
# Expected: both consistently explain separation of concerns
```

---

## Acceptance Criteria Checklist

- [x] `backend/app/auth/plone_bridge.py`: module-level docstring added; clarifies JWT auth only, NOT MCP
- [x] `infra/plone-mcp/README.md`: "Architecture Note" section added; distinguishes MCP from auth adapter
- [x] `docs/ARCHITECTURE_STATE.md`: "Plone Integration Points" section appended; includes text diagram of 3+ touchpoints + data flow
- [x] `PLUGIN_MANIFEST.md`: clarified `plone_integration` plugin status (placeholder, `capabilities: []`, future purpose documented)

---

## Data Flow Summary (for quick reference)

```
User Login Request
  ↓
PloneIdentityAdapter.get_identity(token, tenant_id)
  ↓ (validates Bearer token via Plone REST API /@users/@current)
  ↓
PloneIdentity(username, roles, tenant_id)  [stored in JWT]
  ↓
AI Platform auth layer accepts request
  ↓
[Later] AI agent needs Plone content
  ↓
MCPRegistry.get_server("plone")  [lists plone-mcp as trusted]
  ↓
PloneMCPServer adapter
  ↓
plone-mcp Node.js server (port 9120)
  ↓
Plone REST API (/@@search, /@content, etc.)
  ↓
Content CRUD operations, Volto blocks management
  ↓
[Future] plone_integration plugin runs async sync
  ↓
Qdrant vector database (content indexed for RAG)
```

---

## Next Steps

- **For Phase 3c+:** If Plone integration needs testing, reference the "Architecture Note" in plone-mcp README before writing tests.
- **For Phase 4+:** When implementing `plone_integration` plugin, refer to PLUGIN_MANIFEST.md clarification on purpose (content sync) and timing.
- **For upstream updates:** If plone-mcp is synced from upstream, ensure "Architecture Note" is re-applied post-merge (not in upstream).

