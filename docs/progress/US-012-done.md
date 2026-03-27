## US-012: Model Layer — Completion Summary

**Status:** Done
**Date:** 2026-03-27

### What was implemented

#### New files created

- `ai/models/base.py` — `ModelAdapter` ABC, `ModelResponse` dataclass, custom exceptions (`ModelError`, `OllamaUnavailableError`, `ClaudeConfigError`)
- `ai/models/ollama.py` — `OllamaAdapter`: async httpx POST to `{OLLAMA_URL}/api/generate`, 30s timeout, raises `OllamaUnavailableError` on timeout/connect error
- `ai/models/claude.py` — `ClaudeAdapter`: uses `anthropic.AsyncAnthropic`, raises `ClaudeConfigError` on missing API key, model `claude-haiku-4-5-20251001`
- `ai/models/mock.py` — `MockAdapter`: fixed response, configurable `response_text` for test scenarios
- `ai/models/factory.py` — `get_model_adapter(settings)`: routes `demo` → Ollama, `demo-api` → Claude, anything else → Mock
- `ai/models/__init__.py` — exports all public symbols
- `backend/tests/test_models.py` — 10 unit tests, zero real API calls

#### Files modified

- `backend/app/config.py` — added `AI_MODE`, `OLLAMA_URL`, `OLLAMA_MODEL`, `ANTHROPIC_API_KEY` fields to `Settings`
- `backend/pyproject.toml` — added `anthropic>=0.25.0` dependency

### Test results

```
tests/test_models.py::test_mock_adapter_returns_model_response PASSED
tests/test_models.py::test_mock_adapter_custom_response_text PASSED
tests/test_models.py::test_ollama_adapter_sends_correct_payload_and_parses_response PASSED
tests/test_models.py::test_ollama_adapter_timeout_raises_ollama_unavailable_error PASSED
tests/test_models.py::test_ollama_adapter_connect_error_raises_ollama_unavailable_error PASSED
tests/test_models.py::test_claude_adapter_raises_config_error_when_api_key_missing PASSED
tests/test_models.py::test_claude_adapter_generate_returns_model_response PASSED
tests/test_models.py::test_get_model_adapter_demo_mode_returns_ollama_adapter PASSED
tests/test_models.py::test_get_model_adapter_demo_api_mode_returns_claude_adapter PASSED
tests/test_models.py::test_get_model_adapter_unknown_mode_returns_mock_adapter PASSED

10 passed in 0.13s
```

### Notes

- `anthropic` package installed in container via `pip install anthropic` (as root). The `pyproject.toml` entry ensures it is included on next image build.
- The 6 pre-existing failures in `test_auth.py` (plone-login integration tests requiring a live DB) are unrelated to this US and were failing before this work.
- No real Ollama or Anthropic API calls are made in any test.
