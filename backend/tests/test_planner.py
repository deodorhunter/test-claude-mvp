"""
Unit tests for ai/planner — no real Ollama or Anthropic API calls.

All adapter calls are replaced with MockAdapter or custom fakes.
The _primary_adapter parameter is used for dependency injection in every test
so get_model_adapter() is never invoked from within the test suite.
"""

import asyncio
import pytest
from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

from ai.models.base import ModelAdapter, ModelResponse, OllamaUnavailableError
from ai.models.mock import MockAdapter
from ai.planner import (
    Planner,
    ExecutionPlan,
    QuotaExceededError,
    NoPlannerAvailableError,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers / fakes
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class FakeSettings:
    AI_MODE: str = "demo"
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    ANTHROPIC_API_KEY: str = ""


class FailingAdapter(ModelAdapter):
    """Simulates a primary adapter that is unreachable (raises OllamaUnavailableError)."""

    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        raise OllamaUnavailableError("Simulated Ollama unavailable")


class ClaudeMockAdapter(ModelAdapter):
    """Simulates Claude adapter returning a predictable response — no real API call."""

    async def generate(self, prompt: str, context: str = "") -> ModelResponse:
        return ModelResponse(
            text="Claude mock response",
            model_used="claude-haiku-4-5-20251001",
            tokens_used=15,
            provider="claude",
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 1 — Happy path: quota sufficient, primary adapter available
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plan_happy_path_returns_execution_plan():
    """Primary adapter is healthy and quota is sufficient — should succeed."""
    planner = Planner()
    settings = FakeSettings()
    primary = MockAdapter()

    prompt = "What is the capital of France?"
    context = " Answer in one word."
    expected_tokens = (len(prompt) + len(context)) // 4

    result = await planner.plan(
        prompt=prompt,
        context=context,
        quota_remaining=1000,
        settings=settings,
        _primary_adapter=primary,
    )

    assert isinstance(result, ExecutionPlan)
    assert result.adapter is primary
    assert result.estimated_tokens == expected_tokens
    assert result.fallback is False
    assert result.model_used == "mock"
    assert result.provider == "mock"


# ──────────────────────────────────────────────────────────────────────────────
# Test 2 — Quota zero → QuotaExceededError
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plan_quota_zero_raises_quota_exceeded():
    planner = Planner()
    settings = FakeSettings()

    with pytest.raises(QuotaExceededError):
        await planner.plan(
            prompt="Hello",
            context="",
            quota_remaining=0,
            settings=settings,
            _primary_adapter=MockAdapter(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 3 — Estimated tokens > quota → QuotaExceededError
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plan_estimated_exceeds_quota_raises_quota_exceeded():
    planner = Planner()
    settings = FakeSettings()

    # prompt length = 400 chars → estimated = 400 // 4 = 100 tokens
    long_prompt = "a" * 400
    quota = 10  # deliberately less than 100

    with pytest.raises(QuotaExceededError):
        await planner.plan(
            prompt=long_prompt,
            context="",
            quota_remaining=quota,
            settings=settings,
            _primary_adapter=MockAdapter(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 4 — Primary unavailable, Claude fallback available
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plan_primary_unavailable_falls_back_to_claude():
    planner = Planner()
    settings = FakeSettings(ANTHROPIC_API_KEY="sk-ant-test-key")

    claude_mock = ClaudeMockAdapter()

    # Patch ClaudeAdapter constructor to return our mock — no real Anthropic client
    with patch("ai.planner.planner.ClaudeAdapter", return_value=claude_mock):
        result = await planner.plan(
            prompt="Hello",
            context="",
            quota_remaining=1000,
            settings=settings,
            _primary_adapter=FailingAdapter(),
        )

    assert isinstance(result, ExecutionPlan)
    assert result.fallback is True
    assert result.provider == "claude"
    assert result.model_used == "claude-haiku-4-5-20251001"
    assert result.adapter is claude_mock


# ──────────────────────────────────────────────────────────────────────────────
# Test 5 — Primary unavailable, no fallback → NoPlannerAvailableError
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_plan_primary_unavailable_no_fallback_raises_no_planner():
    planner = Planner()
    # No ANTHROPIC_API_KEY → fallback path skipped
    settings = FakeSettings(ANTHROPIC_API_KEY="")

    with pytest.raises(NoPlannerAvailableError):
        await planner.plan(
            prompt="Hello",
            context="",
            quota_remaining=1000,
            settings=settings,
            _primary_adapter=FailingAdapter(),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Test 6 — ExecutionPlan fields are correctly populated
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execution_plan_fields_are_correct():
    planner = Planner()
    settings = FakeSettings()
    primary = MockAdapter()

    prompt = "ping"
    context = " pong"
    expected_tokens = (len(prompt) + len(context)) // 4

    result = await planner.plan(
        prompt=prompt,
        context=context,
        quota_remaining=500,
        settings=settings,
        _primary_adapter=primary,
    )

    # Verify all mandatory ExecutionPlan fields are present and typed correctly
    assert hasattr(result, "adapter")
    assert hasattr(result, "model_used")
    assert hasattr(result, "estimated_tokens")
    assert hasattr(result, "fallback")
    assert hasattr(result, "provider")

    assert isinstance(result.model_used, str)
    assert isinstance(result.estimated_tokens, int)
    assert isinstance(result.fallback, bool)
    assert isinstance(result.provider, str)

    assert result.estimated_tokens == expected_tokens
    assert result.fallback is False
