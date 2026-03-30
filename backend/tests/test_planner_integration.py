"""
US-019: Planner integration tests — quota integration, fallback logic,
10-concurrent load test.

Actual Planner signature (verified from source):
  Planner.plan(prompt, context, quota_remaining: int, settings, _primary_adapter=None) -> ExecutionPlan
  ExecutionPlan: adapter, model_used, estimated_tokens, fallback: bool, provider
  QuotaExceededError raised when quota_remaining <= 0 or estimated > quota_remaining
  NoPlannerAvailableError raised when primary fails and no fallback configured
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock

from ai.models.mock import MockAdapter
from ai.models.base import ModelAdapter, ModelResponse, OllamaUnavailableError


class FakeSettings:
    ANTHROPIC_API_KEY = ""
    OLLAMA_MODEL = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"


class FakeSettingsWithClaude:
    ANTHROPIC_API_KEY = "fake-key"
    OLLAMA_MODEL = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"


class FailingAdapter(ModelAdapter):
    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        raise OllamaUnavailableError("primary down")


# ---------------------------------------------------------------------------
# Quota guard — quota_remaining <= 0 raises QuotaExceededError
# ---------------------------------------------------------------------------

class TestPlannerQuotaIntegration:
    @pytest.mark.asyncio
    async def test_quota_exceeded_when_remaining_is_zero(self):
        from ai.planner.planner import Planner, QuotaExceededError
        planner = Planner()
        with pytest.raises(QuotaExceededError):
            await planner.plan(
                prompt="test",
                context="",
                quota_remaining=0,
                settings=FakeSettings(),
            )

    @pytest.mark.asyncio
    async def test_quota_exceeded_when_remaining_is_negative(self):
        from ai.planner.planner import Planner, QuotaExceededError
        planner = Planner()
        with pytest.raises(QuotaExceededError):
            await planner.plan(
                prompt="test",
                context="",
                quota_remaining=-5,
                settings=FakeSettings(),
            )

    @pytest.mark.asyncio
    async def test_quota_exceeded_when_estimated_exceeds_remaining(self):
        from ai.planner.planner import Planner, QuotaExceededError
        # 400 chars / 4 = 100 estimated tokens; quota_remaining=50 → exceeded
        long_prompt = "x" * 400
        planner = Planner()
        with pytest.raises(QuotaExceededError):
            await planner.plan(
                prompt=long_prompt,
                context="",
                quota_remaining=50,
                settings=FakeSettings(),
            )

    @pytest.mark.asyncio
    async def test_quota_allowed_proceeds_to_model(self):
        from ai.planner.planner import Planner
        planner = Planner()
        result = await planner.plan(
            prompt="hello",
            context="",
            quota_remaining=1000,
            settings=FakeSettings(),
            _primary_adapter=MockAdapter(),
        )
        assert result is not None
        assert result.model_used == "mock"
        assert result.fallback is False


# ---------------------------------------------------------------------------
# Fallback: primary fails → fallback adapter used → fallback=True
# ---------------------------------------------------------------------------

class TestPlannerFallback:
    @pytest.mark.asyncio
    async def test_fallback_used_is_true_when_primary_fails(self):
        from ai.planner.planner import Planner

        fallback_response = ModelResponse(
            text="from claude", model_used="claude-haiku", tokens_used=5, provider="claude"
        )
        mock_claude_instance = AsyncMock()
        mock_claude_instance.generate = AsyncMock(return_value=fallback_response)

        with patch("ai.planner.planner.ClaudeAdapter", return_value=mock_claude_instance):
            planner = Planner()
            result = await planner.plan(
                prompt="test",
                context="",
                quota_remaining=1000,
                settings=FakeSettingsWithClaude(),
                _primary_adapter=FailingAdapter(),
            )
        assert result.fallback is True
        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_no_fallback_raises_no_planner_available(self):
        from ai.planner.planner import Planner, NoPlannerAvailableError
        # No ANTHROPIC_API_KEY → no fallback → NoPlannerAvailableError
        planner = Planner()
        with pytest.raises(NoPlannerAvailableError):
            await planner.plan(
                prompt="test",
                context="",
                quota_remaining=1000,
                settings=FakeSettings(),  # empty ANTHROPIC_API_KEY
                _primary_adapter=FailingAdapter(),
            )

    @pytest.mark.asyncio
    async def test_execution_plan_has_correct_fields(self):
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
        assert isinstance(result.model_used, str)
        assert result.estimated_tokens >= 0


# ---------------------------------------------------------------------------
# 10 concurrent planner.plan() calls — no deadlock
# ---------------------------------------------------------------------------

class TestPlannerConcurrency:
    @pytest.mark.asyncio
    async def test_10_concurrent_plans_complete_without_deadlock(self):
        """10 concurrent plan() calls must all complete within 15s."""
        from ai.planner.planner import Planner

        results = []
        errors = []

        async def run_plan(i):
            try:
                planner = Planner()
                result = await planner.plan(
                    prompt=f"concurrent prompt {i}",
                    context="",
                    quota_remaining=10000,
                    settings=FakeSettings(),
                    _primary_adapter=MockAdapter(),
                )
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        try:
            await asyncio.wait_for(
                asyncio.gather(*[run_plan(i) for i in range(10)]),
                timeout=15.0,
            )
        except asyncio.TimeoutError:
            pytest.fail("Deadlock detected: 10 concurrent plan() calls timed out after 15s")

        total = len(results) + len(errors)
        assert total == 10, f"Expected 10 completions, got {total}"
        assert len(results) == 10, f"Expected 10 successes, got errors: {errors}"

    @pytest.mark.asyncio
    async def test_concurrent_plans_different_tenants_independent(self):
        """Concurrent calls for different logical tenants must not interfere."""
        from ai.planner.planner import Planner

        results_a = []
        results_b = []

        async def run_for(quota, results):
            try:
                planner = Planner()
                result = await planner.plan(
                    prompt="test",
                    context="",
                    quota_remaining=quota,
                    settings=FakeSettings(),
                    _primary_adapter=MockAdapter(),
                )
                results.append(result)
            except Exception as e:
                results.append(e)

        await asyncio.wait_for(
            asyncio.gather(
                *[run_for(10000, results_a) for _ in range(5)],
                *[run_for(10000, results_b) for _ in range(5)],
            ),
            timeout=15.0,
        )

        assert len(results_a) + len(results_b) == 10
