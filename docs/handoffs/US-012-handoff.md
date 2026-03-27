# Handoff: US-012 — Model Layer

**Completed by:** AI/ML Engineer
**Date:** 2026-03-27
**Status:** ✅ Done

---

## What was built

A production-ready **model layer** with three async adapters and a factory router.

### Core interface: `ModelAdapter`

```python
@dataclass
class ModelResponse:
    text: str                    # Generated text
    model_used: str             # e.g. "llama3", "claude-haiku-4-5-20251001"
    tokens_used: int            # Total tokens (input + output)
    provider: str               # "ollama" | "claude" | "mock"

class ModelAdapter(ABC):
    async def generate(self, prompt: str, context: str = "") -> ModelResponse: ...
```

All adapters concatenate `prompt + context` before sending to the provider.

### Three adapters implemented

1. **OllamaAdapter** (`ai/models/ollama.py`)
   - HTTP POST to `{OLLAMA_URL}/api/generate`
   - Reads `settings.OLLAMA_URL` and `settings.OLLAMA_MODEL` (defaults: `http://ollama:11434`, `llama3`)
   - 30s timeout; raises `OllamaUnavailableError` on timeout or connection failure
   - Extracts response text and token count from JSON

2. **ClaudeAdapter** (`ai/models/claude.py`)
   - Uses `anthropic.AsyncAnthropic` SDK
   - Requires `settings.ANTHROPIC_API_KEY` (raises `ClaudeConfigError` if missing)
   - Model: `claude-haiku-4-5-20251001` (most economical for MVP)
   - Returns token count from `message.usage`

3. **MockAdapter** (`ai/models/mock.py`)
   - Always returns fixed response: `"Mock response"`
   - Configurable via `response_text` parameter for test scenarios
   - No external calls; instant response

### Factory router: `get_model_adapter(settings)`

Routes based on `settings.AI_MODE`:

| `AI_MODE` | Result |
|-----------|--------|
| `"demo"` | `OllamaAdapter(settings)` |
| `"demo-api"` | `ClaudeAdapter(settings)` |
| (anything else) | `MockAdapter()` |

Exported from `ai/models/__init__.py` along with all exceptions and adapter classes.

---

## Files created/modified

| File | Type | Purpose |
|------|------|---------|
| `ai/models/__init__.py` | Created | Public API exports |
| `ai/models/base.py` | Created | `ModelAdapter` ABC, `ModelResponse`, exceptions |
| `ai/models/ollama.py` | Created | `OllamaAdapter` implementation |
| `ai/models/claude.py` | Created | `ClaudeAdapter` implementation |
| `ai/models/mock.py` | Created | `MockAdapter` for testing |
| `ai/models/factory.py` | Created | `get_model_adapter()` router |
| `backend/app/config.py` | Modified | Added `AI_MODE`, `OLLAMA_URL`, `OLLAMA_MODEL`, `ANTHROPIC_API_KEY` to `Settings` |
| `backend/pyproject.toml` | Modified | Added `anthropic>=0.25.0` dependency |
| `backend/tests/test_models.py` | Created | 10 unit tests, 100% pass, zero real API calls |

---

## Integration points for US-013 (Cost-Aware Planner)

The planner will use this model layer to select and invoke generation. Key imports:

```python
from ai.models import get_model_adapter, ModelResponse, ModelError, OllamaUnavailableError, ClaudeConfigError
from backend.app.config import settings

# Route to correct provider
adapter = get_model_adapter(settings)

# Generate response
try:
    response: ModelResponse = await adapter.generate(
        prompt="Your query here",
        context="Optional context string"
    )
    print(f"Generated: {response.text}")
    print(f"Tokens: {response.tokens_used}")
    print(f"Provider: {response.provider}")
except OllamaUnavailableError as e:
    # Handle Ollama unavailable (timeout/connection error)
    print(f"Ollama error: {e}")
except ClaudeConfigError as e:
    # Handle missing API key
    print(f"Claude config error: {e}")
except ModelError as e:
    # Catch-all for model layer errors
    print(f"Model error: {e}")
```

**Key contract:**
- All adapters are async; always `await` calls
- `ModelResponse` has stable fields: `text`, `model_used`, `tokens_used`, `provider`
- Exceptions inherit from `ModelError` for granular catching or broad fallback

---

## Residual risks / known gaps

- **Ollama availability:** If Ollama container doesn't start or crashes, demo mode will fail with `OllamaUnavailableError`. Planner must implement fallback logic (e.g., try Ollama → on failure, try Claude if key is available → else use Mock).
- **Claude API latency:** Real network latency for Claude calls; no caching or retry logic yet. Planner should implement timeouts if needed.
- **Token counting:** Claude token count from SDK is accurate; Ollama's `eval_count` is approximate (model-dependent).
- **Context size limits:** Neither adapter validates prompt+context length against model limits. Oversized inputs will fail at provider side.

---

## Manual test instructions

Run these in the container. Each command should pass silently (exit code 0) or display the expected output.

### 1. Test MockAdapter (always works)

```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.models import MockAdapter, ModelResponse

async def test():
    adapter = MockAdapter(response_text="Test successful")
    result = await adapter.generate("test prompt")
    assert isinstance(result, ModelResponse)
    assert result.text == "Test successful"
    assert result.provider == "mock"
    print("✓ MockAdapter test passed")

asyncio.run(test())
EOF
```

**Expected output:**
```
✓ MockAdapter test passed
```

---

### 2. Test OllamaAdapter with Ollama available (demo mode)

First, verify Ollama is running:

```bash
docker exec ai-platform-ollama ollama list
```

**Expected output:**
```
NAME                    ID              SIZE    MODIFIED
llama3:latest           1234567890abcd  4.7GB   2 minutes ago
```

Then test the adapter:

```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.models import OllamaAdapter, ModelResponse, OllamaUnavailableError
from dataclasses import dataclass

@dataclass
class Settings:
    OLLAMA_URL = "http://ollama:11434"
    OLLAMA_MODEL = "llama3"

async def test():
    adapter = OllamaAdapter(Settings)
    try:
        result = await adapter.generate("Say 'hello'")
        assert isinstance(result, ModelResponse)
        assert len(result.text) > 0
        assert result.provider == "ollama"
        print(f"✓ OllamaAdapter test passed. Generated: {result.text[:50]}...")
    except OllamaUnavailableError as e:
        print(f"⚠ Ollama unavailable: {e}")

asyncio.run(test())
EOF
```

**Expected output (Ollama available):**
```
✓ OllamaAdapter test passed. Generated: hello [response continues...]
```

**Expected output (Ollama unavailable):**
```
⚠ Ollama unavailable: Ollama service unreachable at http://ollama:11434: [error details]
```

---

### 3. Test OllamaAdapter timeout behavior

Simulate an unavailable Ollama by pointing to a non-existent address:

```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.models import OllamaAdapter, OllamaUnavailableError
from dataclasses import dataclass

@dataclass
class Settings:
    OLLAMA_URL = "http://invalid-host:11434"
    OLLAMA_MODEL = "llama3"

async def test():
    adapter = OllamaAdapter(Settings)
    try:
        await adapter.generate("test")
        print("✗ Expected OllamaUnavailableError but got no error")
    except OllamaUnavailableError as e:
        print(f"✓ Correctly raised OllamaUnavailableError: {str(e)[:60]}...")

asyncio.run(test())
EOF
```

**Expected output:**
```
✓ Correctly raised OllamaUnavailableError: Ollama service unreachable at http://invalid-host:11434...
```

---

### 4. Test ClaudeAdapter without API key

```bash
docker exec ai-platform-api python3 << 'EOF'
from ai.models import ClaudeAdapter, ClaudeConfigError
from dataclasses import dataclass

@dataclass
class Settings:
    ANTHROPIC_API_KEY = ""

try:
    adapter = ClaudeAdapter(Settings)
    print("✗ Expected ClaudeConfigError but got no error")
except ClaudeConfigError as e:
    print(f"✓ Correctly raised ClaudeConfigError: {str(e)[:60]}...")

EOF
```

**Expected output:**
```
✓ Correctly raised ClaudeConfigError: ANTHROPIC_API_KEY is not set...
```

---

### 5. Test Factory routing: AI_MODE=demo → Ollama

```bash
docker exec ai-platform-api python3 << 'EOF'
from ai.models import get_model_adapter, OllamaAdapter
from dataclasses import dataclass

@dataclass
class Settings:
    AI_MODE = "demo"
    OLLAMA_URL = "http://ollama:11434"
    OLLAMA_MODEL = "llama3"
    ANTHROPIC_API_KEY = ""

adapter = get_model_adapter(Settings)
assert isinstance(adapter, OllamaAdapter)
print("✓ Factory correctly routed 'demo' mode to OllamaAdapter")

EOF
```

**Expected output:**
```
✓ Factory correctly routed 'demo' mode to OllamaAdapter
```

---

### 6. Test Factory routing: AI_MODE=demo-api → Claude (requires API key)

```bash
docker exec ai-platform-api python3 << 'EOF'
from ai.models import get_model_adapter, ClaudeAdapter, ClaudeConfigError
from dataclasses import dataclass

@dataclass
class Settings:
    AI_MODE = "demo-api"
    OLLAMA_URL = "http://ollama:11434"
    OLLAMA_MODEL = "llama3"
    ANTHROPIC_API_KEY = ""

try:
    adapter = get_model_adapter(Settings)
    print("✗ Expected ClaudeConfigError due to missing key")
except ClaudeConfigError:
    print("✓ Factory correctly raises ClaudeConfigError when API_KEY missing")

EOF
```

**Expected output:**
```
✓ Factory correctly raises ClaudeConfigError when API_KEY missing
```

---

### 7. Test automated test suite

```bash
docker exec ai-platform-api python3 -m pytest backend/tests/test_models.py -v
```

**Expected output:**
```
backend/tests/test_models.py::test_mock_adapter_returns_model_response PASSED
backend/tests/test_models.py::test_mock_adapter_custom_response_text PASSED
backend/tests/test_models.py::test_ollama_adapter_sends_correct_payload_and_parses_response PASSED
backend/tests/test_models.py::test_ollama_adapter_timeout_raises_ollama_unavailable_error PASSED
backend/tests/test_models.py::test_ollama_adapter_connect_error_raises_ollama_unavailable_error PASSED
backend/tests/test_models.py::test_claude_adapter_raises_config_error_when_api_key_missing PASSED
backend/tests/test_models.py::test_claude_adapter_generate_returns_model_response PASSED
backend/tests/test_models.py::test_get_model_adapter_demo_mode_returns_ollama_adapter PASSED
backend/tests/test_models.py::test_get_model_adapter_demo_api_mode_returns_claude_adapter PASSED
backend/tests/test_models.py::test_get_model_adapter_unknown_mode_returns_mock_adapter PASSED

======================== 10 passed in 0.13s ========================
```

---

## How to verify this works (automated)

The smoke test suite confirms all components:

```bash
cd /Users/martina/personal-projects/test-claude-mvp

# Start containers
make up

# Run model layer tests (should all pass)
make test FILTER=test_models

# Check health
curl -s http://localhost:8000/health
```

All 10 unit tests pass with zero external API calls.
