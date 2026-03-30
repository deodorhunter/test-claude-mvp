"""
US-019: End-to-end mock pipeline tests.
Full pipeline: ContextBuilder.build() → Planner.plan() → adapter.generate().

Actual signatures (verified from source):
  Planner.plan(prompt, context, quota_remaining: int, settings, _primary_adapter=None) -> ExecutionPlan
  ExecutionPlan: adapter, model_used, estimated_tokens, fallback: bool, provider
  ContextBuilder.build(query, tenant_id) -> str
  QuotaService.check_quota(tenant_id, tokens_estimated) -> bool
  QuotaService.consume_quota(tenant_id, tokens_used) -> None
"""
import asyncio
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from ai.models.mock import MockAdapter
from ai.models.base import ModelAdapter, ModelResponse, OllamaUnavailableError

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


class FakeSettings:
    ANTHROPIC_API_KEY = ""
    OLLAMA_MODEL = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"


def make_mcp_result(source="e2e-src", data="e2e context data", confidence=0.8):
    from ai.mcp.base import MCPResult
    return MCPResult(data=data, source=source, confidence=confidence)


def make_mcp_server(name="e2e-server", result=None):
    from ai.mcp.base import MCPServer
    server = MagicMock(spec=MCPServer)
    server.name = name

    async def query(q):
        return result or make_mcp_result(source=name)

    server.query = query
    return server


# ---------------------------------------------------------------------------
# Full pipeline: ContextBuilder → Planner
# ---------------------------------------------------------------------------

class TestE2EFullPipeline:
    @pytest.mark.asyncio
    async def test_context_builder_output_is_string(self):
        """ContextBuilder.build() must return a string for any tenant."""
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder

        mcp_result = make_mcp_result(source="wiki", data="context info", confidence=0.8)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("wiki", result=mcp_result))
        builder = ContextBuilder(registry=registry)

        context = await builder.build("what is AI?", tenant_id=str(TENANT_A))
        assert isinstance(context, str)
        assert "context info" in context

    @pytest.mark.asyncio
    async def test_planner_with_context_returns_execution_plan(self):
        """Planner.plan() with context from ContextBuilder returns a valid ExecutionPlan."""
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        from ai.planner.planner import Planner

        mcp_result = make_mcp_result(source="wiki", data="wiki facts", confidence=0.8)
        registry = MCPRegistry(min_confidence=0.5)
        registry.register(make_mcp_server("wiki", result=mcp_result))
        builder = ContextBuilder(registry=registry)

        context = await builder.build("what is AI?", tenant_id=str(TENANT_A))

        planner = Planner()
        result = await planner.plan(
            prompt="what is AI?",
            context=context,
            quota_remaining=10000,
            settings=FakeSettings(),
            _primary_adapter=MockAdapter(),
        )
        assert result is not None
        assert result.model_used == "mock"
        assert result.fallback is False

    @pytest.mark.asyncio
    async def test_execution_plan_adapter_can_generate(self):
        """The adapter in ExecutionPlan must be callable and return a ModelResponse."""
        from ai.planner.planner import Planner

        planner = Planner()
        result = await planner.plan(
            prompt="generate test",
            context="some context",
            quota_remaining=10000,
            settings=FakeSettings(),
            _primary_adapter=MockAdapter(),
        )
        response = await result.adapter.generate("generate test", "some context")
        assert isinstance(response.text, str)
        assert isinstance(response.model_used, str)

    @pytest.mark.asyncio
    async def test_execution_plan_fields_present(self):
        """ExecutionPlan returned by pipeline has all required fields."""
        from ai.planner.planner import Planner

        planner = Planner()
        result = await planner.plan(
            prompt="field check",
            context="some context",
            quota_remaining=10000,
            settings=FakeSettings(),
            _primary_adapter=MockAdapter(),
        )
        assert hasattr(result, "adapter")
        assert hasattr(result, "model_used")
        assert hasattr(result, "estimated_tokens")
        assert hasattr(result, "fallback")
        assert hasattr(result, "provider")
        assert isinstance(result.fallback, bool)


# ---------------------------------------------------------------------------
# Quota exceeded → QuotaExceededError propagates cleanly
# ---------------------------------------------------------------------------

class TestE2EQuotaExceeded:
    @pytest.mark.asyncio
    async def test_quota_exceeded_raises_quota_exceeded_error(self):
        """quota_remaining=0 must raise QuotaExceededError."""
        from ai.planner.planner import Planner, QuotaExceededError

        planner = Planner()
        with pytest.raises(QuotaExceededError):
            await planner.plan(
                prompt="this should fail quota",
                context="",
                quota_remaining=0,
                settings=FakeSettings(),
            )

    @pytest.mark.asyncio
    async def test_quota_exceeded_error_type_is_planner_error(self):
        """QuotaExceededError must be a subclass of PlannerError."""
        from ai.planner.planner import QuotaExceededError, PlannerError
        assert issubclass(QuotaExceededError, PlannerError)

    @pytest.mark.asyncio
    async def test_quota_exceeded_error_is_catchable_as_exception(self):
        """QuotaExceededError must be catchable as a plain Exception."""
        from ai.planner.planner import QuotaExceededError
        with pytest.raises(Exception):
            raise QuotaExceededError("test quota exceeded")


# ---------------------------------------------------------------------------
# Cross-tenant: QuotaService isolates per tenant
# ---------------------------------------------------------------------------

class TestE2ECrossTenantQuota:
    @pytest.mark.asyncio
    async def test_two_tenants_independent_quota_checks(self):
        """check_quota called for different tenants must not share state."""
        from app.quota.quota_service import QuotaService

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.execute = AsyncMock(return_value=MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)  # no quota row → unlimited
        ))
        mock_session_factory = MagicMock(return_value=mock_session)

        service = QuotaService(session_factory=mock_session_factory)

        result_a = await service.check_quota(tenant_id=TENANT_A, tokens_estimated=100)
        result_b = await service.check_quota(tenant_id=TENANT_B, tokens_estimated=100)

        assert result_a is True
        assert result_b is True

    @pytest.mark.asyncio
    async def test_tenant_a_quota_exceeded_does_not_block_tenant_b(self):
        """Tenant A's quota exhaustion must not affect Tenant B."""
        from app.quota.quota_service import QuotaService

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        call_count = {"n": 0}

        async def mock_execute(stmt, *args, **kwargs):
            call_count["n"] += 1
            mock_result = MagicMock()
            if call_count["n"] == 1:
                # Tenant A: over quota — use a real object so int comparison works
                class QuotaRow:
                    tokens_used = 1000
                    max_tokens = 500
                mock_result.scalar_one_or_none = MagicMock(return_value=QuotaRow())
            else:
                # Tenant B: no row → unlimited
                mock_result.scalar_one_or_none = MagicMock(return_value=None)
            return mock_result

        mock_session.execute = AsyncMock(side_effect=mock_execute)
        mock_session_factory = MagicMock(return_value=mock_session)

        service = QuotaService(session_factory=mock_session_factory)

        result_a = await service.check_quota(tenant_id=TENANT_A, tokens_estimated=100)
        result_b = await service.check_quota(tenant_id=TENANT_B, tokens_estimated=100)

        assert result_a is False, "Tenant A quota should be exceeded"
        assert result_b is True, "Tenant B quota must not be affected by tenant A"


# ---------------------------------------------------------------------------
# Error path: model failure
# ---------------------------------------------------------------------------

class TestE2EModelFailure:
    @pytest.mark.asyncio
    async def test_primary_fails_no_fallback_raises(self):
        """Primary down + no ANTHROPIC_API_KEY → NoPlannerAvailableError."""
        from ai.planner.planner import Planner, NoPlannerAvailableError

        class FailAdapter(ModelAdapter):
            async def generate(self, prompt, context=""):
                raise OllamaUnavailableError("down")

        planner = Planner()
        with pytest.raises(NoPlannerAvailableError):
            await planner.plan(
                prompt="will fail in model",
                context="",
                quota_remaining=10000,
                settings=FakeSettings(),
                _primary_adapter=FailAdapter(),
            )

    @pytest.mark.asyncio
    async def test_context_builder_failure_does_not_crash_pipeline(self):
        """If all MCP servers fail, ContextBuilder must return a string, not raise."""
        from ai.mcp.registry import MCPRegistry
        from ai.context.builder import ContextBuilder
        from ai.mcp.base import MCPServer

        bad_srv = MagicMock(spec=MCPServer)
        bad_srv.name = "broken"

        async def bad_query(q):
            raise RuntimeError("MCP server down")

        bad_srv.query = bad_query

        registry = MCPRegistry(min_confidence=0.5)
        registry.register(bad_srv)
        builder = ContextBuilder(registry=registry)

        result = await builder.build("query", tenant_id=str(TENANT_A))
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Concurrent cross-tenant pipeline calls
# ---------------------------------------------------------------------------

class TestE2EConcurrency:
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_calls_two_tenants(self):
        """5 calls per tenant concurrently — no deadlock, no cross-tenant contamination."""
        from ai.planner.planner import Planner

        results = {str(TENANT_A): [], str(TENANT_B): []}
        errors = []

        async def run_plan(tenant_id):
            try:
                planner = Planner()
                result = await planner.plan(
                    prompt="concurrent e2e",
                    context="",
                    quota_remaining=10000,
                    settings=FakeSettings(),
                    _primary_adapter=MockAdapter(),
                )
                results[str(tenant_id)].append(result)
            except Exception as e:
                errors.append((str(tenant_id), str(e)))

        tasks = (
            [run_plan(TENANT_A) for _ in range(5)] +
            [run_plan(TENANT_B) for _ in range(5)]
        )

        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=15.0)
        except asyncio.TimeoutError:
            pytest.fail("Deadlock: concurrent pipeline calls timed out after 15s")

        total = sum(len(v) for v in results.values()) + len(errors)
        assert total == 10, f"Expected 10 completions, got {total}"
        assert len(errors) == 0, f"Unexpected errors: {errors}"
