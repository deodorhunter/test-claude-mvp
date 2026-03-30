# Handoff: US-014 — MCP Registry + Trust Scoring

**Completed by:** AI/ML Engineer
**Date:** 2026-03-29
**Files created/modified:**
- ai/mcp/base.py (new)
- ai/mcp/registry.py (new)
- ai/mcp/servers/internal_docs.py (new)
- ai/mcp/servers/web.py (new)
- backend/tests/test_mcp.py (new, 17 tests)

## What was built

Implemented the MCP (Model Context Protocol) server registry layer with trust-based filtering. The `MCPRegistry` class manages multiple MCP server implementations, each with a configurable `trust_score` (0.0–1.0). When `query_all()` is called, it queries all registered servers and filters results by `min_confidence` (default 0.5) before returning. Audit logging is performed once per server queried, **before** confidence filtering, ensuring all queries are tracked regardless of trust score.

Two stub server implementations were created: `InternalDocsServer` (trust_score=0.95) and `WebServer` (trust_score=0.4). These demonstrate the interface contract for future server implementations.

All 17 unit tests pass, covering registry operations, trust filtering, and audit logging.

## Integration points

- **MCPRegistry.query_all():** Called by the planner or orchestration layer. Accepts `input_text`, optional `audit_service`, and optional `tenant_id` (for scoping). Returns `list[MCPResult]` filtered by `min_confidence`.
- **Audit logging:** Expects `audit_service` parameter in `query_all()`. If provided, logs one `mcp_query` entry per server with server name, input, confidence, and tenant_id.
- **MCPServer interface:** Base class for all future MCP servers. Subclasses implement `async query(input_text: str) -> MCPResult` and set `name` and `trust_score` as class attributes.

## File ownership

- `ai/mcp/` — owned by AI/ML Engineer. New server implementations added here.
- `backend/tests/test_mcp.py` — owned by QA Engineer (maintenance only).

## Residual risks / known gaps

- **MEDIUM:** Stub servers (`InternalDocsServer`, `WebServer`) return hardcoded confidence scores. Real implementations (RAG integration for internal docs, web search client for web) not yet built. These are Phase 3+ dependencies.
- **LOW:** `MCPRegistry` does not yet handle server timeout or exception propagation. If a server hangs or raises, the entire `query_all()` call blocks. Recommend adding timeout + error isolation in Phase 3.
- **LOW:** No persistence of MCP server configuration (registry state, trust scores). Registry is in-memory only.

## Manual test instructions (for user)

### Setup
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make up  # ensure API container is running
```

### Test 1: Registry register and query with trust filtering
Write and execute a test script that registers both stub servers and queries with min_confidence=0.5:

```bash
cat > /tmp/qa_us014_trust.py << 'EOF'
import asyncio
from ai.mcp.registry import MCPRegistry
from ai.mcp.servers.internal_docs import InternalDocsServer
from ai.mcp.servers.web import WebServer

async def test_trust_filtering():
    registry = MCPRegistry(min_confidence=0.5)
    registry.register(InternalDocsServer())
    registry.register(WebServer())

    results = await registry.query_all("test query")

    # Internal docs (confidence 0.95) should pass min_confidence threshold
    assert any(r.source == "internal_docs" for r in results), \
        "InternalDocsServer result missing (confidence=0.95 should pass 0.5 threshold)"

    # Web (confidence 0.4) should be filtered out
    assert not any(r.source == "web" for r in results), \
        "WebServer result should be filtered (confidence=0.4 below 0.5 threshold)"

    print("✓ Trust filtering works: internal_docs passed, web filtered")

asyncio.run(test_trust_filtering())
EOF

docker exec ai-platform-api python3 /tmp/qa_us014_trust.py && rm /tmp/qa_us014_trust.py
```

Expected output: `✓ Trust filtering works: internal_docs passed, web filtered`

### Test 2: Audit logging
Verify that audit logging is called once per server before confidence filtering:

```bash
cat > /tmp/qa_us014_audit.py << 'EOF'
import asyncio
from unittest.mock import AsyncMock
from ai.mcp.registry import MCPRegistry
from ai.mcp.servers.internal_docs import InternalDocsServer
from ai.mcp.servers.web import WebServer

async def test_audit_logging():
    registry = MCPRegistry(min_confidence=0.5)
    registry.register(InternalDocsServer())
    registry.register(WebServer())

    mock_audit = AsyncMock()

    results = await registry.query_all("test", audit_service=mock_audit, tenant_id="tenant-1")

    # Audit service should be called twice (once per server), even though web is filtered
    assert mock_audit.call_count == 2, \
        f"Audit service called {mock_audit.call_count} times, expected 2"

    print("✓ Audit logging: called once per server (before confidence filter)")

asyncio.run(test_audit_logging())
EOF

docker exec ai-platform-api python3 /tmp/qa_us014_audit.py && rm /tmp/qa_us014_audit.py
```

Expected output: `✓ Audit logging: called once per server (before confidence filter)`

### Test 3: Get all servers
Verify registry returns all registered servers:

```bash
cat > /tmp/qa_us014_getall.py << 'EOF'
from ai.mcp.registry import MCPRegistry
from ai.mcp.servers.internal_docs import InternalDocsServer
from ai.mcp.servers.web import WebServer

registry = MCPRegistry()
registry.register(InternalDocsServer())
registry.register(WebServer())

servers = registry.get_all_servers()
assert len(servers) == 2, f"Expected 2 servers, got {len(servers)}"
assert any(s.name == "internal_docs" for s in servers), "InternalDocsServer not found"
assert any(s.name == "web" for s in servers), "WebServer not found"

print("✓ Registry.get_all_servers() returns both servers")
EOF

docker exec ai-platform-api python3 /tmp/qa_us014_getall.py && rm /tmp/qa_us014_getall.py
```

Expected output: `✓ Registry.get_all_servers() returns both servers`

## How to verify this works (automated)

```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -q backend/tests/test_mcp.py
```

Expected output: `17 passed in X.XXs`

All tests should pass:
- `test_registry_register_and_get` — register a server and retrieve it
- `test_registry_get_unknown_server` — get() returns None for unknown name
- `test_registry_get_all_servers` — get_all_servers() returns all registered
- `test_query_all_trust_filtering` — web filtered at min_confidence=0.5, internal_docs passes
- `test_query_all_audit_logging` — audit service called once per server before filtering
- 12 additional integration and edge case tests

Test file: `/Users/martina/personal-projects/test-claude-mvp/backend/tests/test_mcp.py`
