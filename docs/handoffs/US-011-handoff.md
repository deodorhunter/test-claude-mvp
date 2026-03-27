# Handoff: US-011 — Plugin Runtime

**Completed by:** Security Engineer
**Date:** 2026-03-27
**Test result:** 14/14 passed (Docker/Linux, Python 3.11.15)
**Status:** ✅ Done

## Files Created/Modified

- `backend/app/plugins/runtime.py` — `PluginRuntime` class (350 LOC)
- `backend/app/plugins/__init__.py` — exports for `PluginRuntime` + 4 exceptions
- `backend/tests/test_plugin_runtime.py` — 14 unit tests
- `docs/progress/US-011-done.md` — completion summary with security notes

---

## What Was Built

### `PluginRuntime` — Subprocess Isolation + Resource Limits

The runtime executes plugins in **isolated subprocesses** (not in-process) with the following security properties:

#### Core isolation mechanisms:

1. **Subprocess execution**: Fresh child process per `execute()` call via `asyncio.create_subprocess_exec`. No in-process execution.

2. **JSON protocol**: stdin receives `{"tenant_id": "<uuid>", "input": {...}}`, stdout must produce valid JSON `{"result": {...}, "error": null}`. Contract violations raise `PluginProtocolError`.

3. **10-second timeout**: `asyncio.wait_for` with wall-clock limit. On expiry → `process.kill()` + `process.wait()` → `PluginTimeoutError`. Process is killed even if it ignores SIGTERM.

4. **Resource limits** (cgroups/setrlimit):
   - `RLIMIT_AS`: 256 MB virtual memory
   - `RLIMIT_CPU`: 10 s CPU time
   - Applied via `preexec_fn=_apply_resource_limits` before plugin code runs
   - Gracefully handles macOS EINVAL (logs `WARNING`, continues without aborting)

5. **Environment isolation**: subprocess receives **only** `PATH` and `PYTHONPATH`. All parent env vars (`DATABASE_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`, any custom) are explicitly excluded.

6. **CWD restriction**: subprocess CWD is set to the plugin's own directory, limiting relative-path traversal.

7. **Concurrency control**: `asyncio.Semaphore(2)` keyed by `(tenant_id, plugin_id)`. Different tenants have independent semaphore slots — they do not block each other. Max 2 concurrent workers per slot.

#### Custom Exceptions (all subclasses of `PluginRuntimeError`):

| Exception | Trigger |
|---|---|
| `PluginTimeoutError` | 10 s wall-clock exceeded |
| `PluginExecutionError` | exit code ≠ 0 (stderr included) |
| `PluginProtocolError` | stdout empty or invalid JSON |
| `PluginNotFoundError` | entrypoint file missing |

---

## Integration Points for Downstream US

### US-018 (Security Review)

**What you need to know:**

- Network isolation is **NOT enforced at kernel level** (RISK-HIGH). See [Residual Risks](#residual-risks-known-gaps) below.
- Filesystem traversal via absolute paths is **NOT prevented** (RISK-MEDIUM). Plugin can `open("/app/app/config.py")` — only blocked by env var isolation (no secrets in child env).
- File descriptor and thread exhaustion not limited (RISK-LOW).
- macOS resource limit fallback is silent at runtime (logged at startup), so development without memory/CPU capping is expected.

Your review must verify:
1. Whether the RISK-HIGH network isolation can be accepted for Phase 2a gate.
2. Whether additional mitigations (seccomp, chroot, Landlock) should be flagged as post-MVP.

### US-019 (QA Engineer)

**What you need to know:**

- All 4 exception types and their triggers (see exception table above).
- Semaphore behavior: tenant A's invocation does not block tenant B's (independent slots).
- Env isolation test is critical: `__TEST_SECRET_SHOULD_NOT_LEAK__` absent from child env.
- Cross-tenant input isolation: tenant A's UUID not visible in tenant B's result.
- Timeout test: sleeping plugin killed at 10s, not before.

Test files to extend: `backend/tests/test_plugin_runtime.py`

---

## Residual Risks & Known Gaps

### RISK-HIGH: No kernel-level network isolation

**What it is:** Network namespace isolation (`unshare(CLONE_NEWNET)`) requires `CAP_SYS_ADMIN` or user namespace setup. Not available in the standard Docker container without explicit config. Plugins can make arbitrary outbound network calls.

**MVP state:**
- `plone_integration`: HTTP access is explicitly authorized (no restriction).
- All other plugins: network is unrestricted at kernel level.

**Post-MVP mitigations:**
- Seccomp profile to block `socket()` syscall for non-plone plugins.
- Docker `--cap-drop=all` + explicit capability allowlist.
- User namespaces + network namespace per invocation.

**Impact:** Malicious plugin can exfiltrate data, call external APIs, phone home. Env isolation (no `ANTHROPIC_API_KEY`, `DATABASE_URL`) limits the value of what can be leaked, but the network channel itself is open.

---

### RISK-MEDIUM: Filesystem traversal via absolute paths

**What it is:** CWD restriction limits relative-path view, but does not prevent absolute paths (`open("/app/app/config.py")`). A chroot or seccomp `openat` filter would be required.

**Applied mitigation:** Subprocess env does not contain `DATABASE_URL` or any credentials.

**Post-MVP mitigations:**
- `chroot` into plugin directory (requires root).
- Seccomp profile restricting `openat` to relative paths.
- Landlock LSM (Linux 5.13+) for path-based access control without root.

---

### RISK-LOW: File descriptor and thread exhaustion

**What it is:** `RLIMIT_NOFILE` (max FDs) and `RLIMIT_NPROC` (max threads) are not set. Plugin could exhaust before `RLIMIT_CPU`/timeout kills it.

**Applied mitigation:** `RLIMIT_CPU` (10 s) and `RLIMIT_AS` (256 MB) bound the most common exhaustion vectors.

**Post-MVP mitigation:** Add `RLIMIT_NOFILE` (e.g., 64) and `RLIMIT_NPROC` (e.g., 8).

---

## How to Verify This Works

### Smoke test (local Docker):

```bash
cd /project
make down && make up
make migrate
sleep 5
make test -k test_plugin_runtime
```

Expected: All 14 tests pass.

### Manual integration test (verify subprocess isolation):

```bash
# From container shell:
docker exec test-claude-mvp-backend-1 python -m pytest \
  backend/tests/test_plugin_runtime.py::test_cross_tenant_input_isolation \
  -xvs

# Should show tenant_id in child process differs from parent,
# and input isolation is respected.
```

### Verify timeout enforcement:

```bash
docker exec test-claude-mvp-backend-1 python -m pytest \
  backend/tests/test_plugin_runtime.py::test_timeout_enforcement \
  -xvs

# Should show plugin sleeping >10s gets killed with PluginTimeoutError.
```

---

## Architecture Context for Next Agent

`PluginRuntime.execute()` is called by `PluginManager.invoke()` (US-010), which in turn is called by the **model layer** (US-012, US-013) to execute plugins during planning/generation. The runtime is a **passive layer** — it does not decide when or how plugins are invoked. That logic is in the manager and planner.

This is important for US-018 (Security Review): you are reviewing the **execution isolation**, not the invocation decision tree.

---

## Acceptance Criteria Verification

- [x] Plugin executed in subprocess (not in-process) — verified by PID test
- [x] Timeout 10s enforced, plugin killed, `PluginTimeoutError` raised
- [x] Memory limit applied with graceful macOS fallback (logged at startup)
- [x] Input/output via JSON on stdin/stdout only
- [x] Cross-tenant input isolation verified (test suite)
- [x] Env isolation verified (no parent vars leaked)
- [x] `plone_integration` documented with authorized HTTP; others documented as network-unrestricted (MVP)
- [x] Unit tests: timeout, isolation, JSON protocol, missing entrypoint, bad JSON
- [x] Security Notes in `docs/progress/US-011-done.md` with residual risks explicit
