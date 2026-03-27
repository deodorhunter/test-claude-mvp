"""
Model layer unit tests — no real Ollama or Anthropic API calls.

All external HTTP calls are mocked with respx (httpx) or unittest.mock (anthropic SDK).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass

from ai.models.base import ModelResponse, OllamaUnavailableError, ClaudeConfigError
from ai.models.mock import MockAdapter
from ai.models.ollama import OllamaAdapter
from ai.models.claude import ClaudeAdapter
from ai.models.factory import get_model_adapter


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class FakeSettings:
    AI_MODE: str = "demo"
    OLLAMA_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    ANTHROPIC_API_KEY: str = ""


# ──────────────────────────────────────────────────────────────────────────────
# MockAdapter tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mock_adapter_returns_model_response():
    adapter = MockAdapter()
    result = await adapter.generate("hello")
    assert isinstance(result, ModelResponse)
    assert result.text == "Mock response"
    assert result.model_used == "mock"
    assert result.tokens_used == 10
    assert result.provider == "mock"


@pytest.mark.asyncio
async def test_mock_adapter_custom_response_text():
    adapter = MockAdapter(response_text="custom text")
    result = await adapter.generate("test prompt", context=" with context")
    assert result.text == "custom text"
    assert result.provider == "mock"


# ──────────────────────────────────────────────────────────────────────────────
# OllamaAdapter tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ollama_adapter_sends_correct_payload_and_parses_response():
    settings = FakeSettings(OLLAMA_URL="http://ollama:11434", OLLAMA_MODEL="llama3")
    adapter = OllamaAdapter(settings)

    fake_response = MagicMock()
    fake_response.json.return_value = {"response": "Hello from Ollama", "eval_count": 42}
    fake_response.raise_for_status = MagicMock()

    captured_payload = {}

    async def fake_post(url, json=None, **kwargs):
        captured_payload.update({"url": url, "json": json})
        return fake_response

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=fake_post)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ai.models.ollama.httpx.AsyncClient", return_value=mock_client):
        result = await adapter.generate("tell me a joke", context=" about cats")

    assert captured_payload["url"] == "http://ollama:11434/api/generate"
    assert captured_payload["json"]["model"] == "llama3"
    assert captured_payload["json"]["prompt"] == "tell me a joke about cats"
    assert captured_payload["json"]["stream"] is False

    assert isinstance(result, ModelResponse)
    assert result.text == "Hello from Ollama"
    assert result.model_used == "llama3"
    assert result.tokens_used == 42
    assert result.provider == "ollama"


@pytest.mark.asyncio
async def test_ollama_adapter_timeout_raises_ollama_unavailable_error():
    import httpx

    settings = FakeSettings()
    adapter = OllamaAdapter(settings)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ai.models.ollama.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(OllamaUnavailableError):
            await adapter.generate("hello")


@pytest.mark.asyncio
async def test_ollama_adapter_connect_error_raises_ollama_unavailable_error():
    import httpx

    settings = FakeSettings()
    adapter = OllamaAdapter(settings)

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("ai.models.ollama.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(OllamaUnavailableError):
            await adapter.generate("hello")


# ──────────────────────────────────────────────────────────────────────────────
# ClaudeAdapter tests
# ──────────────────────────────────────────────────────────────────────────────


def test_claude_adapter_raises_config_error_when_api_key_missing():
    settings = FakeSettings(AI_MODE="demo-api", ANTHROPIC_API_KEY="")
    with pytest.raises(ClaudeConfigError):
        ClaudeAdapter(settings)


@pytest.mark.asyncio
async def test_claude_adapter_generate_returns_model_response():
    settings = FakeSettings(AI_MODE="demo-api", ANTHROPIC_API_KEY="sk-ant-test-key")

    # Build a fake response matching the anthropic SDK structure
    fake_content_block = MagicMock()
    fake_content_block.text = "Hello from Claude"

    fake_usage = MagicMock()
    fake_usage.input_tokens = 15
    fake_usage.output_tokens = 20

    fake_message = MagicMock()
    fake_message.content = [fake_content_block]
    fake_message.usage = fake_usage

    mock_messages = MagicMock()
    mock_messages.create = AsyncMock(return_value=fake_message)

    mock_anthropic_client = MagicMock()
    mock_anthropic_client.messages = mock_messages

    with patch("ai.models.claude.anthropic.AsyncAnthropic", return_value=mock_anthropic_client):
        adapter = ClaudeAdapter(settings)
        result = await adapter.generate("explain quantum computing", context=" briefly")

    assert isinstance(result, ModelResponse)
    assert result.text == "Hello from Claude"
    assert result.model_used == "claude-haiku-4-5-20251001"
    assert result.tokens_used == 35  # 15 + 20
    assert result.provider == "claude"

    # Verify the correct call was made
    mock_messages.create.assert_called_once()
    call_kwargs = mock_messages.create.call_args.kwargs
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
    assert call_kwargs["max_tokens"] == 1024
    assert call_kwargs["messages"][0]["role"] == "user"
    assert call_kwargs["messages"][0]["content"] == "explain quantum computing briefly"


# ──────────────────────────────────────────────────────────────────────────────
# Factory tests
# ──────────────────────────────────────────────────────────────────────────────


def test_get_model_adapter_demo_mode_returns_ollama_adapter():
    settings = FakeSettings(AI_MODE="demo")
    adapter = get_model_adapter(settings)
    assert isinstance(adapter, OllamaAdapter)


def test_get_model_adapter_demo_api_mode_returns_claude_adapter():
    settings = FakeSettings(AI_MODE="demo-api", ANTHROPIC_API_KEY="sk-ant-test-key")
    with patch("ai.models.claude.anthropic.AsyncAnthropic"):
        adapter = get_model_adapter(settings)
    assert isinstance(adapter, ClaudeAdapter)


def test_get_model_adapter_unknown_mode_returns_mock_adapter():
    settings = FakeSettings(AI_MODE="other")
    adapter = get_model_adapter(settings)
    assert isinstance(adapter, MockAdapter)
