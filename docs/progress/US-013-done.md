# US-013 Done — Cost-Aware Planner

**Date:** 2026-03-29

## Summary

US-013 delivered the `Planner` class that wraps the three model adapters from US-012 in a cost-aware orchestration layer. The planner estimates token costs pre-execution, enforces tenant quota guards, and implements a deterministic fallback chain (Ollama → Claude → error). All quota validation happens before model selection, ensuring no token spend occurs on out-of-quota tenants.

## What Was Implemented

- **`Planner.plan()` method** — orchestrates model selection with quota checks and fallback logic
  - Estimates tokens using: `(len(prompt) + len(context)) // 4`
  - Raises `QuotaExceededError(429)` if `quota_remaining <= 0` or estimate exceeds quota
  - Probes primary adapter availability with 5-second timeout
  - Falls back to Claude if primary times out and `ANTHROPIC_API_KEY` is set
  - Raises `NoPlannerAvailableError(503)` if both primary and fallback are unavailable

- **`ExecutionPlan` dataclass** — immutable execution contract
  - `adapter: ModelAdapter` — selected adapter instance
  - `model_used: str` — model name (e.g., "llama3", "claude-haiku-4-5-20251001")
  - `estimated_tokens: int` — pre-execution token estimate
  - `fallback: bool` — True if primary adapter was skipped
  - `provider: str` — "ollama" | "claude" | "mock"

- **Exception hierarchy**
  - `PlannerError` — base exception
  - `QuotaExceededError(PlannerError)` — tenant out of quota (429 mapping)
  - `NoPlannerAvailableError(PlannerError)` — no reachable adapter (503 mapping)

- **Dependency injection** — `_primary_adapter` parameter for testing
  - Allows unit tests to inject mock adapters without real API calls
  - Defaults to `get_model_adapter(settings)` in production

## Fallback Chain

```
1. Primary adapter (Ollama or configured default)
   ├─ timeout 5s → FALLBACK
   └─ success → return ExecutionPlan(fallback=False)

2. Claude adapter (if ANTHROPIC_API_KEY is set)
   ├─ timeout 5s → FALLBACK
   └─ success → return ExecutionPlan(fallback=True)

3. No fallback available
   └─ raise NoPlannerAvailableError(503)
```

**MVP behavior:** If primary Ollama times out and Claude is configured, silently switch to Claude. Caller is informed via `ExecutionPlan.fallback=True` for logging/audit purposes.

## Token Estimation Formula

```
estimated_tokens = (len(prompt) + len(context)) // 4
```

**Rationale:** Average token density is approximately 1 token per 4 characters in ASCII text. This is a conservative approximation suitable for MVP quota checks; exact token counts are deferred to per-model post-execution validation in Phase 3.

## Test Coverage

All tests inject `_primary_adapter` — **zero real API calls**.

1. **test_plan_happy_path_returns_execution_plan**
   - MockAdapter, quota=1000, 100-char prompt
   - Asserts: `ExecutionPlan.fallback=False`, `provider="mock"`

2. **test_plan_quota_zero_raises_quota_exceeded**
   - quota=0
   - Asserts: `QuotaExceededError` raised immediately (no probe attempt)

3. **test_plan_estimated_exceeds_quota_raises_quota_exceeded**
   - 400-char prompt, quota=10 (estimate ~100 tokens)
   - Asserts: `QuotaExceededError` raised before primary adapter touched

4. **test_plan_primary_unavailable_falls_back_to_claude**
   - FailingAdapter (raises `OllamaUnavailableError` on generate)
   - ClaudeMockAdapter injected as fallback
   - Asserts: `ExecutionPlan.fallback=True`, `provider="claude"`

5. **test_plan_primary_unavailable_no_fallback_raises_no_planner**
   - FailingAdapter, `ANTHROPIC_API_KEY=None`
   - Asserts: `NoPlannerAvailableError` raised

6. **test_execution_plan_fields_are_correct**
   - Dataclass instantiation with all field types verified
   - Asserts: adapter is `ModelAdapter` subclass, model_used is `str`, estimated_tokens is `int`, fallback is `bool`, provider in ["ollama", "claude", "mock"]

## Integration Notes

### Audit Logging Deferred
The planner raises `QuotaExceededError` but does **not** write to the database `AuditLog` table. Audit log writes on quota exhaustion are assigned to **US-020 (API Layer — Request Validation)** in Phase 3.

**Flow:**
- Phase 2b: Planner raises exception in memory
- Phase 3 (US-020+): API layer catches exception and writes `AuditLog(event="quota_exceeded", tenant_id=...)` before returning 429 HTTP response

This separation keeps the planner agnostic to the database layer and allows quota enforcement to work in offline/CLI contexts during Phase 2.

### HTTP Mapping (Phase 3)
- `QuotaExceededError` → **429 Too Many Requests**
- `NoPlannerAvailableError` → **503 Service Unavailable**

## Files Created/Modified

| File | Status | Notes |
|---|---|---|
| `ai/planner/planner.py` | ✅ Created | Planner + exception classes |
| `ai/planner/plan.py` | ✅ Created | ExecutionPlan dataclass |
| `ai/planner/__init__.py` | ✅ Created | Public API exports |
| `backend/tests/test_planner.py` | ✅ Created | 6 unit tests, 100% mocked |
| `ai/__init__.py` | ✅ Updated | Import Planner, ExecutionPlan at package level |

## Dependencies Met

- ✅ US-012 (Model adapters + factory) — Planner uses get_model_adapter factory and all three adapter subclasses
- ✅ No new dependencies added — uses only existing imports (asyncio, dataclasses, typing, ai.models)
- ✅ Quota checks pre-execution — cost-aware guard in place
- ✅ Fallback chain deterministic — always tries Ollama first, then Claude if available, then fails

**Smoke test:** ✅ PASS
- `make test` — all 6 tests green
- `make up` — Docker services running
- `curl http://localhost:8000/health` — 200 OK

---

**Ready for:** Phase 2c (MCP Registry + Context Builder). Planner can now be integrated into the orchestrator layer in Phase 3 (US-020+) or used by downstream modules in Phase 2c as needed.
