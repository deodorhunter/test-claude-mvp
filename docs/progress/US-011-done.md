# US-011: Plugin Runtime — Completion Summary

**Status:** Done
**Date:** 2026-03-27
**Agent:** Security Engineer
**Test result:** 14/14 passed on Docker (Linux, Python 3.11.15)

---

## What Was Implemented

### `backend/app/plugins/runtime.py` — `PluginRuntime`

Core class that executes plugins in isolated subprocesses. Key properties:

- **Subprocess isolation**: uses `asyncio.create_subprocess_exec` with `sys.executable`. Each invocation spawns a fresh child process. No in-process execution.
- **Input/output protocol**: JSON on stdin (`{"tenant_id": "...", "input": {...}}`), JSON on stdout (`{"result": {...}, "error": null}`). Contract violation raises `PluginProtocolError`.
- **Timeout**: `asyncio.wait_for` with 10 s limit. On expiry → `process.kill()` + `process.wait()` (reaps zombie) → `PluginTimeoutError`. Process is definitively killed even if it ignores SIGTERM.
- **Resource limits**: `preexec_fn=_apply_resource_limits` runs in the child before Python code executes. Sets `RLIMIT_AS` (256 MB virtual memory) and `RLIMIT_CPU` (10 s CPU time). Gracefully handles platforms where `setrlimit` fails (macOS EINVAL), logs `WARNING` at startup, continues without aborting.
- **Concurrency control**: `asyncio.Semaphore(2)` keyed by `(tenant_id, plugin_id)`. Different tenants have independent semaphore slots — they do not block each other.
- **Environment isolation**: subprocess receives only `PATH` and `PYTHONPATH` (required for the Python interpreter and container packages). All other env vars — `DATABASE_URL`, `SECRET_KEY`, `ANTHROPIC_API_KEY`, `REDIS_URL`, any custom vars — are excluded. Verified by test.
- **CWD restriction**: subprocess CWD is set to the plugin's own directory.

### Custom exceptions (all subclasses of `PluginRuntimeError`)

| Exception | Trigger |
|---|---|
| `PluginTimeoutError` | 10 s wall-clock exceeded |
| `PluginExecutionError` | exit code != 0 (stderr included in message) |
| `PluginProtocolError` | stdout is empty or not valid JSON |
| `PluginNotFoundError` | entrypoint file does not exist |

### `backend/app/plugins/__init__.py`

Updated to export `PluginRuntime` and all four custom exceptions.

### `backend/tests/test_plugin_runtime.py`

14 tests covering:
- Basic echo execution (well-behaved plugin)
- Subprocess separation (plugin PID != parent PID)
- Timeout enforcement (sleeping plugin killed, `PluginTimeoutError` raised)
- Non-zero exit code → `PluginExecutionError` with stderr in message
- Invalid JSON stdout → `PluginProtocolError`
- Missing entrypoint → `PluginNotFoundError`
- Empty stdout → `PluginProtocolError`
- Env isolation: injected `__TEST_SECRET_SHOULD_NOT_LEAK__` absent in child env
- Cross-tenant input isolation: tenant A's UUID not present in tenant B's result
- Independent semaphores per (tenant, plugin) slot
- JSON stdin protocol (tenant_id + input fields present)
- tenant_id field matches caller's UUID
- Exception hierarchy (all subclasses of PluginRuntimeError)

---

## Security Notes — Residual Risks

### RISK-HIGH: No kernel-level network isolation

**Description:** Network namespace isolation (`unshare(CLONE_NEWNET)`) requires `CAP_SYS_ADMIN` or a user namespace setup, which is not available in the standard Docker container without explicit configuration. Plugins can make arbitrary outbound network calls.

**Current state for MVP:**
- `plone_integration`: HTTP access is explicitly authorized and expected.
- All other plugins: network is unrestricted at kernel level.

**Mitigations NOT applied (post-MVP):**
- Seccomp profile to block `socket()` syscall for non-`plone_integration` plugins.
- Docker `--cap-drop=all` + explicit allowlist of capabilities.
- User namespaces + network namespace per plugin invocation.

**Impact:** A malicious or compromised plugin could exfiltrate data, call external APIs, or phone home. The env isolation (no `ANTHROPIC_API_KEY`, no `DATABASE_URL` in child env) limits the value of what can be leaked, but the network channel itself is open.

---

### RISK-MEDIUM: Filesystem traversal via absolute paths

**Description:** Setting `cwd` to the plugin directory limits the plugin's relative-path view, but does not prevent a malicious plugin from using absolute paths (e.g., `open("/app/app/config.py")`). A chroot or seccomp `openat` filter would be required for full filesystem isolation.

**Mitigations applied:**
- Subprocess env does not contain `DATABASE_URL` or any credentials, limiting the value of reading config files.

**Post-MVP mitigations:**
- `chroot` into the plugin directory (requires root, not ideal).
- Seccomp profile restricting `openat` to relative paths only.
- Landlock LSM (Linux 5.13+) for fine-grained path-based access control without root.

---

### RISK-LOW: File descriptor and thread exhaustion

**Description:** `RLIMIT_NOFILE` (max open file descriptors) and `RLIMIT_NPROC` (max threads/processes) are not currently set. A malicious plugin could exhaust FDs or threads before the `RLIMIT_CPU`/wall-clock timeout kills it.

**Mitigations applied:** `RLIMIT_CPU` (10 s) and `RLIMIT_AS` (256 MB) bound the most common resource exhaustion vectors.

**Post-MVP mitigations:** Add `RLIMIT_NOFILE` (e.g., 64) and `RLIMIT_NPROC` (e.g., 8) to `_apply_resource_limits`.

---

### RISK-INFO: macOS resource limit fallback

**Description:** On macOS, `RLIMIT_AS` raises `EINVAL` and cannot be set. `RLIMIT_CPU` may or may not work depending on the macOS version. The runtime logs explicit `WARNING` messages at startup when either limit cannot be applied, so the condition is never silent.

**Impact:** Zero impact in production (Docker/Linux target). Local macOS development runs without memory/CPU capping at OS level; the asyncio wall-clock timeout still applies.

---

## Acceptance Criteria Verification

- [x] Plugin executed in subprocess separato (non in-process) — verified by PID test
- [x] Timeout 10s: plugin che supera il limite viene killato e ritorna `PluginTimeoutError`
- [x] Limite memoria applicato con warning esplicito se non supportato (macOS)
- [x] Input/output solo via JSON su stdin/stdout
- [x] Plugin di tenant A non può leggere dati di tenant B (verified by cross-tenant test)
- [x] Subprocess env vars isolate (nessuna var del padre passata) — verified by env dump test
- [x] `plone_integration` documentato con accesso HTTP; altri plugin documentati come "network not isolated at kernel level (MVP)" — see RISK-HIGH above
- [x] Unit test: timeout enforcement, isolation cross-tenant, JSON protocol, missing entrypoint, bad JSON output
- [x] Security Notes in `docs/progress/US-011-done.md` con rischi residui espliciti — this document
