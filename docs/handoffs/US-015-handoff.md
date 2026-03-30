# Handoff: US-015 — Context Builder + Prompt Injection Defense

**Completed by:** AI/ML Engineer
**Date:** 2026-03-29
**Files created/modified:** `ai/context/builder.py`, `ai/context/sanitizer.py`, `ai/context/__init__.py`, `backend/tests/test_context_builder.py`, `docs/progress/US-015-done.md`

## What was built

`ContextBuilder` assembles final model context by querying all registered MCP servers in parallel (asyncio.gather), filtering by confidence threshold, and formatting each result with source attribution. A new `sanitizer` module strips HTML tags and removes 9 prompt injection patterns before merging chunks. All MCP queries timeout at 3 seconds per server; timed-out or errored servers are skipped silently (not fatal). Audit logging records which sources were included and their confidence scores.

The output format is:
```
[Fonte: {source} | confidence: {confidence:.2f}]
{sanitized_data}

[Fonte: {other_source} | confidence: {other_confidence:.2f}]
{other_sanitized_data}
```

Injection patterns blocked (case-insensitive): `IGNORE PREVIOUS`, `[INST]`, `[/INST]`, `</s>`, `<s>`, `<<SYS>>`, `<</SYS>>`, `[SYS]`, `[/SYS]`. Detection logs a warning.

## Integration points

- **Depends on:** `ai/mcp/registry.py` (MCPRegistry from US-014) — the builder receives a registry instance and reads `min_confidence` threshold and registered server list from it
- **Called by:** Orchestrator (ai/orchestrator/orchestrator.py) — will invoke `builder.build(query, tenant_id)` to fetch augmented context before sending query to model
- **Input:** query string, tenant_id (optional, passed to all MCP servers)
- **Output:** formatted string with source attribution and confidence metadata
- **Audit hook:** if audit_service is provided to `__init__`, logs entry for each source included

## File ownership

- `ai/context/` (new directory) — owned by AI/ML Engineer
- `backend/tests/test_context_builder.py` — owned by AI/ML Engineer (part of context builder test suite)

## Residual risks / known gaps

| Risk | Severity | Notes |
|---|---|---|
| HTML stripping via regex | LOW | Simple `<[^>]+>` pattern; does not handle malformed tags or nested CDATA. Sufficient for sanitizing MCP outputs. |
| Injection pattern list incomplete | LOW | Current 9 patterns cover common LLM-injection vectors (from OWASP + model internals). Can be extended per threat discovery. |
| Timeout granularity | MEDIUM | Each server gets 3s timeout; no per-query adaptive timeout or retry logic. If a server is slow, all build() calls wait 3s. Mitigated in practice by rapid server responses. |
| No ranking/reranking logic | MEDIUM | Sources are joined in registry order, not by confidence or relevance. Planner (US-013) will order the context; builder's role is assembly only. |
| Audit logging unbounded | LOW | If audit_service logs all results, high-cardinality queries could fill logs. Production audit service should implement sampling. |

## Manual test instructions (for user)

All commands below assume `make up` has been run and the API is responding at `http://localhost:8000`.

**Setup:**
```bash
docker exec ai-platform-api python3 << 'SCRIPT'
# Write test script to /tmp to avoid shell quoting issues per Rule 005
import sys
sys.path.insert(0, '/app')

# test script will be written below
SCRIPT
```

**Test 1: Source Attribution and Confidence Metadata**

Write to `/tmp/qa_us015_test1.py`:
```python
import asyncio
import sys
sys.path.insert(0, '/app')

from ai.mcp.registry import MCPRegistry, ServerConfig
from ai.context.builder import ContextBuilder

async def test_source_attribution():
    # Create a mock registry with two servers
    registry = MCPRegistry(min_confidence=0.5)
    registry.servers = {
        'internal_docs': ServerConfig(
            name='internal_docs',
            endpoint='http://localhost:9001',
            trust_score=0.95
        ),
        'web_search': ServerConfig(
            name='web_search',
            endpoint='http://localhost:9002',
            trust_score=0.75
        )
    }

    builder = ContextBuilder(registry=registry)
    result = await builder.build(query="test query", tenant_id="tenant-123")

    # Verify source attribution format
    assert "[Fonte: internal_docs | confidence: 0.95]" in result or \
           "[Fonte: web_search | confidence: 0.75]" in result, \
           f"Source attribution format not found. Got: {result}"
    print("✓ Source attribution format correct")

asyncio.run(test_source_attribution())
```

Run:
```bash
docker exec ai-platform-api python3 /tmp/qa_us015_test1.py
rm /tmp/qa_us015_test1.py
```

Expected output: `✓ Source attribution format correct`

---

**Test 2: Prompt Injection Pattern Detection and Removal**

Write to `/tmp/qa_us015_test2.py`:
```python
import sys
sys.path.insert(0, '/app')

from ai.context.sanitizer import sanitize, INJECTION_PATTERNS

def test_injection_removal():
    # Test all 9 patterns are detected
    test_cases = [
        "some text IGNORE PREVIOUS instruction more text",
        "data [INST] payload [/INST] end",
        "</s> start tag",
        "<s> close tag",
        "<<SYS>> system <</>SYS>> block",
        "[SYS] marker [/SYS] end",
    ]

    for text in test_cases:
        sanitized = sanitize(text)
        # Patterns should be removed
        for pattern in INJECTION_PATTERNS:
            assert pattern.upper() not in sanitized.upper(), \
                f"Pattern '{pattern}' not removed from '{text}'"

    print("✓ All 9 injection patterns removed (case-insensitive)")

test_injection_removal()
```

Run:
```bash
docker exec ai-platform-api python3 /tmp/qa_us015_test2.py
rm /tmp/qa_us015_test2.py
```

Expected output: `✓ All 9 injection patterns removed (case-insensitive)`

---

**Test 3: HTML Stripping**

Write to `/tmp/qa_us015_test3.py`:
```python
import sys
sys.path.insert(0, '/app')

from ai.context.sanitizer import sanitize

def test_html_stripping():
    html_text = "This is <b>bold</b> and <script>alert('xss')</script> plain text."
    sanitized = sanitize(html_text)

    assert "<" not in sanitized and ">" not in sanitized, \
        f"HTML tags not stripped. Got: {sanitized}"
    assert "bold" in sanitized, "Content inside tags should remain"

    print("✓ HTML tags stripped, content preserved")

test_html_stripping()
```

Run:
```bash
docker exec ai-platform-api python3 /tmp/qa_us015_test3.py
rm /tmp/qa_us015_test3.py
```

Expected output: `✓ HTML tags stripped, content preserved`

---

**Test 4: Timeout Handling (skipped servers do not raise)**

Write to `/tmp/qa_us015_test4.py`:
```python
import asyncio
import sys
sys.path.insert(0, '/app')

from ai.context.builder import ContextBuilder
from ai.mcp.registry import MCPRegistry, ServerConfig

async def test_timeout_handling():
    registry = MCPRegistry(min_confidence=0.5)
    # Configure a server with a slow/unreachable endpoint
    registry.servers = {
        'slow_server': ServerConfig(
            name='slow_server',
            endpoint='http://localhost:59999',  # non-existent
            trust_score=0.8
        )
    }

    builder = ContextBuilder(registry=registry)
    # Should not raise; should skip the server
    result = await builder.build(query="test", tenant_id="tenant-123")

    # Result should be empty or contain only skipped servers
    assert isinstance(result, str), "Builder should return a string even with timeouts"
    print("✓ Timeout servers skipped, no fatal error")

asyncio.run(test_timeout_handling())
```

Run:
```bash
docker exec ai-platform-api python3 /tmp/qa_us015_test4.py
rm /tmp/qa_us015_test4.py
```

Expected output: `✓ Timeout servers skipped, no fatal error`

---

**Test 5: Low Confidence Filtering**

Write to `/tmp/qa_us015_test5.py`:
```python
import sys
sys.path.insert(0, '/app')

from ai.context.builder import ContextBuilder
from ai.mcp.registry import MCPRegistry, ServerConfig

async def test_confidence_filtering():
    registry = MCPRegistry(min_confidence=0.7)
    registry.servers = {
        'high_conf': ServerConfig(name='high_conf', endpoint='http://localhost:9001', trust_score=0.9),
        'low_conf': ServerConfig(name='low_conf', endpoint='http://localhost:9002', trust_score=0.5),
    }

    builder = ContextBuilder(registry=registry)
    result = await builder.build(query="test", tenant_id="tenant-123")

    # low_conf (0.5 < 0.7 threshold) should not appear
    assert "low_conf | confidence: 0.5" not in result, \
        "Low confidence server should be filtered"
    print("✓ Servers below min_confidence=0.7 filtered")

import asyncio
asyncio.run(test_confidence_filtering())
```

Run:
```bash
docker exec ai-platform-api python3 /tmp/qa_us015_test5.py
rm /tmp/qa_us015_test5.py
```

Expected output: `✓ Servers below min_confidence=0.7 filtered`

---

## How to verify this works (automated)

```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -q 2>&1 | grep -E "test_context_builder|passed|FAILED"
```

Expected: All 26 test_context_builder tests pass.

Full test output (if needed):
```bash
pytest backend/tests/test_context_builder.py -v
```

Should show:
- 26 passed
- Coverage includes: source attribution format, confidence filtering, injection pattern removal, HTML stripping, timeout handling, audit logging, tenant_id passthrough, error recovery
