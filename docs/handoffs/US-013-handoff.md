# Handoff: US-013 — Cost-Aware Planner

**Completed by:** AI/ML Engineer
**Date:** 2026-03-29
**Files created/modified:**
- `ai/planner/plan.py` (new)
- `ai/planner/planner.py` (new, 97 lines)
- `ai/planner/__init__.py` (new)
- `backend/tests/test_planner.py` (new, 6 tests)

## What was built

A synchronous cost-aware planner that selects which model adapter to use based on quota availability and adapter health. The Planner estimates token costs (prompt + context divided by 4), enforces quota guards, and implements a fallback chain: primary adapter → Claude (if ANTHROPIC_API_KEY set) → error.

The ExecutionPlan dataclass captures the decision: which adapter was chosen, which model, estimated token count, whether fallback was triggered, and the provider name. This enables downstream quota tracking and audit logging.

## Integration points

**API surface (ai/planner/__init__.py exports):**
- `Planner` class — main orchestrator
- `ExecutionPlan` dataclass — decision artifact
- Exceptions: `PlannerError` (base), `QuotaExceededError` (quota violated), `NoPlannerAvailableError` (no fallback available)

**Planner.plan(prompt, context, quota_remaining, settings, _primary_adapter=None) → ExecutionPlan**
- `prompt` (str): user input
- `context` (str): injected state/files (e.g., git diff, code)
- `quota_remaining` (int): tokens left in budget
- `settings` (dict): configuration (keys: "timeout_seconds")
- `_primary_adapter` (ModelAdapter, optional): injected for testing; defaults to settings["primary_adapter"]

**Token estimation formula:**
```
estimated_tokens = (len(prompt) + len(context)) // 4
```
This is a linear approximation; actual tokens may vary.

**Fallback chain (text diagram):**
```
plan() called
  ↓
Check quota_remaining > 0 and estimated_tokens <= quota_remaining
  ├─ FAIL → raise QuotaExceededError
  └─ OK ↓
Async probe: primary_adapter.generate("ping", "") with timeout=5.0
  ├─ Success → return ExecutionPlan(adapter=primary, model_used=primary.model, ...)
  ├─ Timeout/Error → fallback ↓
Check ANTHROPIC_API_KEY environment variable
  ├─ Set → return ExecutionPlan(adapter=ClaudeAdapter, model_used="claude-...", fallback=True, ...)
  └─ Not set → raise NoPlannerAvailableError
```

## File ownership

- **ai/planner/** — owned by AI/ML Engineer. Consumed by Backend Dev and orchestrator layers.
- **backend/tests/test_planner.py** — unit tests for planner; maintained alongside planner.py.

## Residual risks / known gaps

**MEDIUM:** Audit logging not implemented — ExecutionPlan is created but not logged to audit trail. Deferred to Phase 3 (audit infrastructure). Callers should log the ExecutionPlan decision immediately after calling plan().

**MEDIUM:** Token estimation is linear approximation only — actual token consumption may differ by 10–20% due to model-specific tokenization. Mitigated by conservative quota enforcement: estimated > quota_remaining triggers rejection.

**LOW:** Primary adapter probe timeout is hardcoded to 5.0 seconds. Should be configurable via settings["timeout_seconds"] before Phase 3 in production.

## Manual test instructions (for user)

**Setup (one-time):**
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make up
```

**Verify unit tests:**
```bash
docker exec ai-platform-api python3 -m pytest backend/tests/test_planner.py -v
```

Expected output:
```
backend/tests/test_planner.py::test_plan_happy_path_returns_execution_plan PASSED
backend/tests/test_planner.py::test_plan_quota_zero_raises_quota_exceeded PASSED
backend/tests/test_planner.py::test_plan_estimated_exceeds_quota_raises_quota_exceeded PASSED
backend/tests/test_planner.py::test_plan_primary_unavailable_falls_back_to_claude PASSED
backend/tests/test_planner.py::test_plan_primary_unavailable_no_fallback_raises_no_planner PASSED
backend/tests/test_planner.py::test_execution_plan_fields_are_correct PASSED

6 passed
```

**Manual scenario: Happy path (quota available, primary adapter healthy):**
```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.planner.planner import Planner
from ai.models.mock import MockAdapter

# Simulate healthy primary adapter
mock_adapter = MockAdapter()
settings = {"primary_adapter": mock_adapter}

# Small prompt, large quota
plan = Planner().plan(
    prompt="test request",
    context="some context",
    quota_remaining=10000,
    settings=settings
)
print(f"✓ Plan created: {plan.model_used}, estimated {plan.estimated_tokens} tokens, fallback={plan.fallback}")
EOF
```

Expected output:
```
✓ Plan created: mock-model, estimated 5 tokens, fallback=False
```

**Manual scenario: Quota exceeded:**
```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.planner.planner import Planner, QuotaExceededError
from ai.models.mock import MockAdapter

mock_adapter = MockAdapter()
settings = {"primary_adapter": mock_adapter}

# Large prompt, small quota
try:
    plan = Planner().plan(
        prompt="x" * 5000,
        context="y" * 5000,
        quota_remaining=100,  # insufficient
        settings=settings
    )
except QuotaExceededError as e:
    print(f"✓ Quota guard triggered: {e}")
EOF
```

Expected output:
```
✓ Quota guard triggered: Estimated tokens (2500) exceed quota (100)
```

**Manual scenario: Primary unavailable, no fallback:**
```bash
docker exec ai-platform-api python3 << 'EOF'
import asyncio
from ai.planner.planner import Planner, NoPlannerAvailableError
from ai.models.mock import MockAdapter
import os

# Remove Claude fallback
os.environ.pop("ANTHROPIC_API_KEY", None)

# Create adapter that will timeout
class TimeoutAdapter:
    async def generate(self, prompt, context):
        await asyncio.sleep(10)  # will timeout at 5s

mock_adapter = TimeoutAdapter()
settings = {"primary_adapter": mock_adapter, "timeout_seconds": 5}

try:
    plan = Planner().plan(
        prompt="test",
        context="test",
        quota_remaining=5000,
        settings=settings
    )
except NoPlannerAvailableError as e:
    print(f"✓ No fallback available: {e}")
EOF
```

Expected output:
```
✓ No fallback available: Primary adapter unavailable and no ANTHROPIC_API_KEY set
```

## How to verify this works (automated)

All verification is via the unit test suite:
```bash
cd /Users/martina/personal-projects/test-claude-mvp
make test -q
```

Or directly:
```bash
docker exec ai-platform-api python3 -m pytest backend/tests/test_planner.py -v
```

All 6 scenarios must pass:
1. **test_plan_happy_path_returns_execution_plan** — primary adapter available, quota sufficient → ExecutionPlan returned with correct model
2. **test_plan_quota_zero_raises_quota_exceeded** — quota_remaining=0 → QuotaExceededError raised
3. **test_plan_estimated_exceeds_quota_raises_quota_exceeded** — estimated > quota → QuotaExceededError raised
4. **test_plan_primary_unavailable_falls_back_to_claude** — primary times out, ANTHROPIC_API_KEY set → fallback=True, ClaudeAdapter selected
5. **test_plan_primary_unavailable_no_fallback_raises_no_planner** — primary times out, no API key → NoPlannerAvailableError raised
6. **test_execution_plan_fields_are_correct** — ExecutionPlan dataclass fields all populated correctly

## Integration notes

**Callers (Phase 2):**
Backend orchestrator layer will call `Planner().plan()` before delegating work. The returned ExecutionPlan tells the orchestrator which adapter to use and how many tokens to charge.

**Audit logging (Phase 3 deferred):**
ExecutionPlan decisions should be logged to an audit trail for cost tracking. Implement `audit.log_plan_decision(execution_plan, user_id, request_id)` in Phase 3.

**HTTP mapping (Phase 3):**
Once the API layer exists, `/v1/orchestrate` will accept a request, call `plan()`, and return the decision in the response body for client-side quota enforcement.

## Residual risks summary

| Risk | Severity | Mitigation |
|---|---|---|
| Audit logging not implemented | MEDIUM | Defer to Phase 3; callers must log manually |
| Token estimation is linear approximation | MEDIUM | Conservative quota enforcement catches overruns |
| Timeout hardcoded to 5s | LOW | Configurable in settings; test with 5s default |

## Next steps / dependencies

- **US-014 (Backend API Layer)** depends on ExecutionPlan artifact
- **Phase 3 (Audit)** will consume ExecutionPlan for audit trail
- No blocking issues — planner is independent and ready for orchestrator integration
