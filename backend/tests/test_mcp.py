"""
MCP Registry and server unit tests — no real external service calls.

Tests cover:
- Registry registration and lookup
- Trust score filtering (results below min_confidence are excluded)
- Stub server implementations (internal_docs, web)
- Audit logging for every MCP query
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ai.mcp.base import MCPServer, MCPResult
from ai.mcp.registry import MCPRegistry
from ai.mcp.servers import InternalDocsServer, WebServer


# ──────────────────────────────────────────────────────────────────────────────
# Test MCPRegistry registration and lookup
# ──────────────────────────────────────────────────────────────────────────────


def test_registry_registers_and_retrieves_server():
    """Test that registry can register and retrieve servers by name."""
    registry = MCPRegistry()
    server = InternalDocsServer()

    registry.register(server)

    retrieved = registry.get("internal_docs")
    assert retrieved is not None
    assert retrieved.name == "internal_docs"
    assert retrieved.trust_score == 0.95


def test_registry_get_returns_none_for_unknown_server():
    """Test that registry returns None for unregistered server names."""
    registry = MCPRegistry()
    result = registry.get("nonexistent")
    assert result is None


def test_registry_register_multiple_servers():
    """Test that registry can register and retrieve multiple servers."""
    registry = MCPRegistry()
    server1 = InternalDocsServer()
    server2 = WebServer()

    registry.register(server1)
    registry.register(server2)

    assert registry.get("internal_docs") is not None
    assert registry.get("web") is not None


def test_registry_register_requires_server_name():
    """Test that registry raises error if server has no name."""
    registry = MCPRegistry()

    # Create a server without a name
    class NoNameServer(MCPServer):
        async def query(self, input_text: str) -> MCPResult:
            return MCPResult(data="test", source="test", confidence=0.5)

    server = NoNameServer()
    with pytest.raises(ValueError, match="must have a 'name' attribute"):
        registry.register(server)


# ──────────────────────────────────────────────────────────────────────────────
# Test trust score filtering
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_all_filters_results_below_min_confidence():
    """Test that results below min_confidence are filtered out."""
    registry = MCPRegistry(min_confidence=0.5)

    # Register web server (trust_score=0.4, will be filtered at 0.5 threshold)
    web_server = WebServer()
    registry.register(web_server)

    results = await registry.query_all("test query")

    # Web server has confidence 0.4 < 0.5, so it should be filtered
    assert len(results) == 0


@pytest.mark.asyncio
async def test_query_all_includes_results_above_min_confidence():
    """Test that results above min_confidence are included."""
    registry = MCPRegistry(min_confidence=0.5)

    # Register internal_docs server (trust_score=0.95, will pass filter)
    docs_server = InternalDocsServer()
    registry.register(docs_server)

    results = await registry.query_all("test query")

    # Internal docs has confidence 0.95 > 0.5, so it should be included
    assert len(results) == 1
    assert results[0].source == "internal_docs"
    assert results[0].confidence == 0.95


@pytest.mark.asyncio
async def test_query_all_mixed_filtering():
    """Test filtering with both passing and failing servers."""
    registry = MCPRegistry(min_confidence=0.5)

    # Register both servers
    docs_server = InternalDocsServer()  # confidence 0.95
    web_server = WebServer()  # confidence 0.4
    registry.register(docs_server)
    registry.register(web_server)

    results = await registry.query_all("test query")

    # Only internal_docs should pass the filter
    assert len(results) == 1
    assert results[0].source == "internal_docs"
    assert results[0].confidence == 0.95


@pytest.mark.asyncio
async def test_query_all_with_zero_threshold():
    """Test that all results pass with min_confidence=0.0."""
    registry = MCPRegistry(min_confidence=0.0)

    docs_server = InternalDocsServer()
    web_server = WebServer()
    registry.register(docs_server)
    registry.register(web_server)

    results = await registry.query_all("test query")

    # Both should pass with threshold 0.0
    assert len(results) == 2
    sources = {r.source for r in results}
    assert sources == {"internal_docs", "web"}


@pytest.mark.asyncio
async def test_query_all_with_high_threshold():
    """Test that only very high confidence results pass with high threshold."""
    registry = MCPRegistry(min_confidence=0.9)

    docs_server = InternalDocsServer()  # confidence 0.95
    web_server = WebServer()  # confidence 0.4
    registry.register(docs_server)
    registry.register(web_server)

    results = await registry.query_all("test query")

    # Only internal_docs (0.95) passes 0.9 threshold
    assert len(results) == 1
    assert results[0].source == "internal_docs"


# ──────────────────────────────────────────────────────────────────────────────
# Test audit logging
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_all_logs_audit_entry_for_each_server():
    """Test that audit service is called for each server query."""
    registry = MCPRegistry(min_confidence=0.5)

    docs_server = InternalDocsServer()
    web_server = WebServer()
    registry.register(docs_server)
    registry.register(web_server)

    # Mock audit service
    audit_mock = AsyncMock()
    tenant_id = "test-tenant-123"

    await registry.query_all("test query", audit_service=audit_mock, tenant_id=tenant_id)

    # Audit should be called twice (once per server), regardless of filtering
    assert audit_mock.log.call_count == 2

    # Verify audit calls
    calls = audit_mock.log.call_args_list
    call_kwargs_list = [call.kwargs for call in calls]

    # Both calls should have action="mcp_query"
    actions = [kw["action"] for kw in call_kwargs_list]
    assert all(a == "mcp_query" for a in actions)

    # Both calls should have the tenant_id
    tenant_ids = [kw["tenant_id"] for kw in call_kwargs_list]
    assert all(t == tenant_id for t in tenant_ids)

    # Calls should include the server names as resources
    resources = {kw["resource"] for kw in call_kwargs_list}
    assert resources == {"internal_docs", "web"}


@pytest.mark.asyncio
async def test_query_all_audit_metadata_includes_confidence():
    """Test that audit metadata includes confidence and filtering info."""
    registry = MCPRegistry(min_confidence=0.5)

    web_server = WebServer()
    registry.register(web_server)

    audit_mock = AsyncMock()

    await registry.query_all("test query", audit_service=audit_mock, tenant_id="tenant-1")

    # Check that metadata includes confidence and filtering info
    call_kwargs = audit_mock.log.call_args.kwargs
    metadata = call_kwargs["metadata"]

    assert "confidence" in metadata
    assert metadata["confidence"] == 0.4  # Web server's confidence
    assert metadata["min_confidence"] == 0.5
    assert metadata["filtered"] is True  # Should be filtered


@pytest.mark.asyncio
async def test_query_all_without_audit_service():
    """Test that query_all works when audit_service is None."""
    registry = MCPRegistry(min_confidence=0.5)

    docs_server = InternalDocsServer()
    registry.register(docs_server)

    # Should not raise an error
    results = await registry.query_all("test query", audit_service=None, tenant_id=None)

    assert len(results) == 1
    assert results[0].source == "internal_docs"


@pytest.mark.asyncio
async def test_query_all_logs_error_on_server_failure():
    """Test that audit service logs errors when a server query fails."""
    registry = MCPRegistry(min_confidence=0.5)

    # Create a failing server
    class FailingServer(MCPServer):
        name = "failing"
        trust_score = 0.8

        async def query(self, input_text: str) -> MCPResult:
            raise ValueError("Server failure")

    registry.register(FailingServer())
    audit_mock = AsyncMock()

    results = await registry.query_all("test query", audit_service=audit_mock, tenant_id="tenant-1")

    # Should log the error
    audit_mock.log.assert_called()
    call_kwargs = audit_mock.log.call_args.kwargs
    assert "error" in call_kwargs["metadata"]
    assert "Server failure" in call_kwargs["metadata"]["error"]

    # Query should return empty results (error didn't produce data)
    assert len(results) == 0


# ──────────────────────────────────────────────────────────────────────────────
# Test stub server implementations
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_internal_docs_server_query():
    """Test InternalDocsServer stub implementation."""
    server = InternalDocsServer()

    result = await server.query("What is authentication?")

    assert isinstance(result, MCPResult)
    assert result.source == "internal_docs"
    assert result.confidence == 0.95
    assert "Internal Documentation" in result.data
    assert "authentication?" in result.data  # Input echoed in stub


@pytest.mark.asyncio
async def test_web_server_query():
    """Test WebServer stub implementation."""
    server = WebServer()

    result = await server.query("What is REST?")

    assert isinstance(result, MCPResult)
    assert result.source == "web"
    assert result.confidence == 0.4
    assert "Web Search Result" in result.data
    assert "REST?" in result.data  # Input echoed in stub


@pytest.mark.asyncio
async def test_server_properties():
    """Test server name and trust_score properties."""
    docs = InternalDocsServer()
    web = WebServer()

    assert docs.name == "internal_docs"
    assert docs.trust_score == 0.95

    assert web.name == "web"
    assert web.trust_score == 0.4


# ──────────────────────────────────────────────────────────────────────────────
# Integration tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_workflow_with_audit_and_filtering():
    """Integration test: register, query, filter, and audit in one workflow."""
    registry = MCPRegistry(min_confidence=0.5)

    # Register servers
    registry.register(InternalDocsServer())
    registry.register(WebServer())

    # Mock audit service
    audit_mock = AsyncMock()

    # Execute full query
    results = await registry.query_all(
        "How do I integrate MCP?",
        audit_service=audit_mock,
        tenant_id="acme-corp",
    )

    # Verify results (only internal_docs passes filter)
    assert len(results) == 1
    assert results[0].source == "internal_docs"

    # Verify audit logging
    assert audit_mock.log.call_count == 2  # Called for both servers
    resources = {call.kwargs["resource"] for call in audit_mock.log.call_args_list}
    assert resources == {"internal_docs", "web"}

    # Verify metadata shows filtering
    calls = audit_mock.log.call_args_list
    web_call = [c for c in calls if c.kwargs["resource"] == "web"][0]
    assert web_call.kwargs["metadata"]["filtered"] is True

    internal_call = [c for c in calls if c.kwargs["resource"] == "internal_docs"][0]
    assert internal_call.kwargs["metadata"]["filtered"] is False
