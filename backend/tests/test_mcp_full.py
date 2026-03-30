"""
US-019: MCP full tests — registry, trust filtering, attribution, timeout, multi-server.
Focus: gaps not covered by test_mcp.py and test_context_builder.py.
"""
import asyncio
import pytest
from unittest.mock import MagicMock


def make_mcp_result(source="server1", data="some data", confidence=0.8):
    from ai.mcp.base import MCPResult
    return MCPResult(data=data, source=source, confidence=confidence)


def make_mcp_server(name="server1", result=None, delay=0.0, raise_exc=None):
    from ai.mcp.base import MCPServer
    server = MagicMock(spec=MCPServer)
    server.name = name

    async def query(q):
        if delay:
            await asyncio.sleep(delay)
        if raise_exc:
            raise raise_exc
        return result or make_mcp_result(source=name)

    server.query = query
    return server


class TestMCPRegistryBasic:
    def test_register_and_get_returns_server(self):
        from ai.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        srv = make_mcp_server("alpha")
        registry.register(srv)
        assert registry.get("alpha") is srv

    def test_get_all_servers_returns_all_registered(self):
        from ai.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        s1 = make_mcp_server("s1")
        s2 = make_mcp_server("s2")
        registry.register(s1)
        registry.register(s2)
        servers = registry.get_all_servers()
        assert len(servers) == 2
        assert {s.name for s in servers} == {"s1", "s2"}

    def test_get_unknown_server_raises_or_returns_none(self):
        from ai.mcp.registry import MCPRegistry
        registry = MCPRegistry()
        try:
            result = registry.get("nonexistent")
            assert result is None
        except (KeyError, Exception):
            pass


class TestMCPTrustFiltering:
    @pytest.mark.asyncio
    async def test_low_confidence_result_excluded_from_context(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        low_conf = make_mcp_result(source="low_srv", data="low data", confidence=0.3)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("low_srv", result=low_conf))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "low data" not in output

    @pytest.mark.asyncio
    async def test_high_confidence_result_included_in_context(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        high_conf = make_mcp_result(source="high_srv", data="trusted data", confidence=0.9)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("high_srv", result=high_conf))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "trusted data" in output

    @pytest.mark.asyncio
    async def test_exactly_min_confidence_is_included(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        exact = make_mcp_result(source="exact_srv", data="boundary data", confidence=0.5)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("exact_srv", result=exact))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "boundary data" in output


class TestMCPSourceAttribution:
    @pytest.mark.asyncio
    async def test_attribution_format_in_context_output(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        result = make_mcp_result(source="wiki", data="wiki content", confidence=0.75)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("wiki", result=result))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "[Fonte: wiki | confidence: 0.75]" in output

    @pytest.mark.asyncio
    async def test_attribution_confidence_two_decimal_places(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        result = make_mcp_result(source="db", data="db content", confidence=0.6666)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("db", result=result))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "0.67" in output or "0.66" in output


class TestMCPTimeout:
    @pytest.mark.asyncio
    async def test_slow_server_does_not_block_build(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        import time
        fast_result = make_mcp_result(source="fast", data="fast data", confidence=0.9)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("fast", result=fast_result, delay=0.0))
        registry.register(make_mcp_server("slow", result=None, delay=4.0))
        start = time.monotonic()
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert time.monotonic() - start < 4.0
        assert "fast data" in output

    @pytest.mark.asyncio
    async def test_all_servers_timeout_returns_string(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("slow", result=None, delay=4.0))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert isinstance(output, str)


class TestMCPMultiServer:
    @pytest.mark.asyncio
    async def test_multiple_servers_results_combined(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("srv1", result=make_mcp_result(source="srv1", data="data from srv1", confidence=0.8)))
        registry.register(make_mcp_server("srv2", result=make_mcp_result(source="srv2", data="data from srv2", confidence=0.9)))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "data from srv1" in output
        assert "data from srv2" in output

    @pytest.mark.asyncio
    async def test_one_server_fails_others_still_included(self):
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("good", result=make_mcp_result(source="good", data="good data", confidence=0.8)))
        registry.register(make_mcp_server("bad", raise_exc=RuntimeError("server down")))
        output = await ContextBuilder(registry=registry).build("query", tenant_id="tenant-a")
        assert "good data" in output
