# US-018 Security Review — Done

**Date:** 2026-03-30
**Status:** Complete — all 27 security tests pass; full suite 213/213 green.

---

## What Was Implemented

### 1. Prompt Injection Defense (ai/context/sanitizer.py)

Added 10 new injection patterns on top of the original 9 LLaMA-style tokens:

| Pattern | Threat |
|---|---|
| `^(SYSTEM\|USER\|ASSISTANT)\s*:` | ChatML role-override prefix injection |
| `<\|im_start\|>` / `<\|im_end\|>` | OpenAI ChatML special tokens |
| `DAN\s+mode` | DAN jailbreak activation phrase |
| `\bjailbreak\b` | Literal jailbreak keyword |
| `ignore\s+all\s+previous\s+instructions?` | Classic prompt injection phrase |
| `you\s+are\s+now\s+(an?\s+)?(different\|new\|unrestricted\|evil\|uncensored)` | Persona hijack / role reversal |
| `-{3,}\s*(END\|STOP\|RESET)\s*-{3,}` | Prompt boundary delimiter injection |
| `###\s*(SYSTEM\|INSTRUCTION)` | Markdown heading as instruction separator |
| `\{\{.*?\}\}` | Jinja/template literal injection |

All compiled with `re.IGNORECASE | re.MULTILINE`.

### 2. Refresh Token JTI Rotation (backend/app/auth/token_store.py — new)

`RefreshTokenStore` provides Redis-backed JTI blacklisting:
- `mark_used(jti, ttl_seconds)` — stores `refresh:used:<jti>` with TTL matching token expiry
- `is_used(jti)` — returns True if JTI is in the blacklist (replay attack detected)
- TTL prevents unbounded Redis growth; keys expire when the underlying token would have expired naturally

### 3. JTI Claim in Refresh Tokens (backend/app/auth/jwt.py)

`create_refresh_token()` now generates and embeds a UUID `jti` claim on every token. Old tokens without JTI are rejected at the `/refresh` endpoint to force re-login.

### 4. /refresh Endpoint — JTI Rotation + Audit (backend/app/api/v1/auth.py)

The `/refresh` endpoint now:
1. Extracts `jti` from the refresh token payload; rejects if absent
2. Checks `token_store.is_used(jti)` — returns HTTP 401 if replayed
3. Issues new access + refresh token pair
4. Calls `token_store.mark_used(old_jti, ttl)` to invalidate the old token
5. Emits `AuditAction.LOGIN_SUCCESS` with `metadata={"action": "token_refresh", "old_jti": <jti>}`

### 5. Redis Initialization (backend/app/main.py)

App lifespan now initializes a `redis.asyncio` client from `REDIS_URL` and injects it into `token_store.init_redis()`. Client is gracefully closed (`aclose()`) on shutdown.

### 6. Test Coverage (backend/tests/test_security_review.py)

27 new tests across 4 test classes:
- `TestPluginIsolation` (5 tests) — semaphore key isolation, tenant_id in subprocess payload
- `TestSanitizerInjectionPatterns` (14 tests) — ≥10 new patterns + 2 regression tests + clean-text passthrough
- `TestRefreshTokenStore` (4 tests) — JTI mark/check lifecycle, key format, TTL
- `TestRefreshEndpointRotation` (5 tests) — replay rejection, JTI blacklisting, audit emission, missing cookie, no-JTI token rejection

---

## Residual Risks

### RISK-HIGH: Plugin Network Isolation (carried from US-011)

**Status: OPEN**

`PluginRuntime` does not apply network namespace isolation (`unshare CLONE_NEWNET`). Plugins can make arbitrary outbound HTTP calls. The empty subprocess environment (`env={}`) prevents leaking `DATABASE_URL`, `SECRET_KEY`, etc., but does not block sockets at the kernel level.

**Mitigation for post-MVP:** Apply a seccomp profile to block `socket()` syscalls, or use user namespaces. For the Docker target, a `--network=none` flag on the container running plugins would be the simplest mitigation.

**Current authorization:** `plone_integration` plugin only is documented as having authorized HTTP access.

### RISK-MEDIUM: Plugin Filesystem Access (carried from US-011)

**Status: OPEN**

CWD is restricted to the plugin directory, but a malicious plugin can still traverse to absolute paths (e.g., `/app/`, `/etc/`). `RLIMIT_AS` caps memory but not filesystem access.

**Mitigation for post-MVP:** chroot or a seccomp profile blocking `openat()` on paths outside the plugin sandbox.

### RISK-LOW: Plugin File Descriptors / Thread Exhaustion (carried from US-011)

**Status: OPEN**

`RLIMIT_NOFILE` and `RLIMIT_NPROC` are not set. A plugin could exhaust file descriptors or spawn many threads before hitting the CPU/memory wall-clock limit.

**Mitigation for post-MVP:** Add `resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))` and `RLIMIT_NPROC` to `_apply_resource_limits()`.

### RISK-LOW: Redis Availability for Token Rotation

**Status: ACCEPTABLE for MVP**

If Redis is unavailable when `/refresh` is called, `token_store.mark_used()` will raise. This will surface as an HTTP 500 to the client. The trade-off is intentional: we prefer failing closed (denying the rotation) over silently skipping the JTI blacklist.

If Redis is unavailable when `token_store.is_used()` is called, replay attacks could succeed during the outage window.

**Mitigation for post-MVP:** Add a Redis health check in the `/health` endpoint; consider circuit breaker with fail-open/fail-closed policy documented and reviewed.

### RISK-LOW: Audit Log Tamper-Evidence

**Status: OPEN — DB-level only**

The audit log is append-only from the application perspective (no UPDATE/DELETE in app code). However, tamper-evidence at the storage level (e.g., hash-chaining, WORM storage) is not implemented. Any DB administrator can alter records.

**Mitigation for post-MVP:** Hash-chain audit entries or export to an append-only store (e.g., object storage with object lock).

---

## Resolved Risks (from Phase 1 residual list)

- **Refresh token replay:** Resolved via JTI rotation in this US.
- **Missing audit events on /refresh:** Resolved — LOGIN_SUCCESS emitted with `action=token_refresh` metadata.
- **Missing injection patterns in sanitizer:** Resolved — 10 new patterns cover role override, jailbreak, persona hijack, template injection, and delimiter injection.
