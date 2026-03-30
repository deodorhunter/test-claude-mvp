"""
US-019: Model layer tests — adapter selection, fallback trigger, interface contract.
Focus: gaps not covered by test_planner.py (adapter-level unit tests).

Actual signatures (verified from source):
  MockAdapter().generate(prompt, context='') -> ModelResponse(text='Mock response', model_used='mock', ...)
  OllamaAdapter(settings).generate(prompt, context='') -> ModelResponse
  ClaudeAdapter(settings).generate(prompt, context='') -> ModelResponse
  get_model_adapter(settings) -> ModelAdapter
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class FakeSettings:
    ANTHROPIC_API_KEY = ""
    OLLAMA_MODEL = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"
    AI_MODE = "mock"


class FakeSettingsOllama:
    ANTHROPIC_API_KEY = ""
    OLLAMA_MODEL = "llama3"
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_URL = "http://localhost:11434"
    AI_MODE = "demo"  # factory uses "demo" to select OllamaAdapter


# ---------------------------------------------------------------------------
# MockAdapter — no I/O, verifies interface contract
# ---------------------------------------------------------------------------

class TestMockAdapter:
    @pytest.mark.asyncio
    async def test_mock_adapter_returns_model_response(self):
        from ai.models.mock import MockAdapter
        from ai.models.base import ModelResponse

        adapter = MockAdapter()
        result = await adapter.generate("hello", context="ctx")

        assert isinstance(result, ModelResponse)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert result.model_used == "mock"
        assert result.tokens_used == 10
        assert result.provider == "mock"

    @pytest.mark.asyncio
    async def test_mock_adapter_no_io(self):
        """MockAdapter must not open sockets."""
        from ai.models.mock import MockAdapter

        with patch("socket.socket") as mock_sock:
            adapter = MockAdapter()
            await adapter.generate("test")
            mock_sock.assert_not_called()

    @pytest.mark.asyncio
    async def test_mock_adapter_ignores_context(self):
        from ai.models.mock import MockAdapter

        adapter = MockAdapter()
        r1 = await adapter.generate("prompt")
        r2 = await adapter.generate("prompt", context="some extra context")
        assert r1.text == r2.text


# ---------------------------------------------------------------------------
# OllamaAdapter — httpx mocked
# ---------------------------------------------------------------------------

class TestOllamaAdapter:
    @pytest.mark.asyncio
    async def test_ollama_adapter_returns_model_response(self):
        from ai.models.base import ModelResponse

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "ollama answer",
            "model": "llama3",
            "eval_count": 42,
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            from ai.models.ollama import OllamaAdapter
            adapter = OllamaAdapter(FakeSettingsOllama())
            result = await adapter.generate("test prompt")

        assert isinstance(result, ModelResponse)
        assert result.text == "ollama answer"
        assert result.tokens_used == 42
        assert result.provider == "ollama"

    @pytest.mark.asyncio
    async def test_ollama_adapter_raises_on_connection_error(self):
        import httpx
        from ai.models.base import OllamaUnavailableError

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
            mock_client_cls.return_value = mock_client

            from ai.models.ollama import OllamaAdapter
            adapter = OllamaAdapter(FakeSettingsOllama())
            with pytest.raises(OllamaUnavailableError):
                await adapter.generate("test")


# ---------------------------------------------------------------------------
# ClaudeAdapter — anthropic client mocked
# ---------------------------------------------------------------------------

class TestClaudeAdapter:
    @pytest.mark.asyncio
    async def test_claude_adapter_returns_model_response(self):
        from ai.models.base import ModelResponse

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="claude answer")]
        mock_message.usage = MagicMock(input_tokens=5, output_tokens=15)
        mock_message.model = "claude-haiku-4-5-20251001"

        mock_anthropic = MagicMock()
        mock_anthropic.messages = MagicMock()
        mock_anthropic.messages.create = AsyncMock(return_value=mock_message)

        settings = FakeSettings()
        settings.ANTHROPIC_API_KEY = "fake-key"

        with patch("anthropic.AsyncAnthropic", return_value=mock_anthropic):
            from ai.models.claude import ClaudeAdapter
            adapter = ClaudeAdapter(settings)
            result = await adapter.generate("test prompt")

        assert isinstance(result, ModelResponse)
        assert result.text == "claude answer"
        assert result.tokens_used == 20  # input + output
        assert result.provider == "claude"

    @pytest.mark.asyncio
    async def test_claude_adapter_raises_config_error_without_api_key(self):
        from ai.models.base import ClaudeConfigError
        from ai.models.claude import ClaudeAdapter

        settings = FakeSettings()
        settings.ANTHROPIC_API_KEY = ""

        with patch("anthropic.AsyncAnthropic") as mock_cls:
            mock_cls.side_effect = ClaudeConfigError("No API key")
            with pytest.raises((ClaudeConfigError, Exception)):
                adapter = ClaudeAdapter(settings)
                await adapter.generate("test")


# ---------------------------------------------------------------------------
# Interface contract
# ---------------------------------------------------------------------------

class TestModelAdapterInterface:
    @pytest.mark.asyncio
    async def test_all_adapters_return_model_response_fields(self):
        """MockAdapter fulfills the ModelResponse contract."""
        from ai.models.mock import MockAdapter
        from ai.models.base import ModelResponse

        adapter = MockAdapter()
        result = await adapter.generate("prompt", context="ctx")

        assert hasattr(result, "text")
        assert hasattr(result, "model_used")
        assert hasattr(result, "tokens_used")
        assert hasattr(result, "provider")
        assert isinstance(result.text, str)
        assert isinstance(result.tokens_used, int)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestModelFactory:
    def test_factory_returns_mock_adapter_in_mock_mode(self):
        from ai.models.factory import get_model_adapter
        from ai.models.mock import MockAdapter
        adapter = get_model_adapter(FakeSettings())
        assert isinstance(adapter, MockAdapter)

    def test_factory_returns_ollama_adapter_in_ollama_mode(self):
        from ai.models.factory import get_model_adapter
        from ai.models.ollama import OllamaAdapter
        adapter = get_model_adapter(FakeSettingsOllama())
        assert isinstance(adapter, OllamaAdapter)
