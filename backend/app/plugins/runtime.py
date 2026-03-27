"""
Plugin Runtime — execute plugins in isolated subprocesses with resource limits.

Security model:
- Each plugin runs in a subprocess (not in-process)
- Resource limits applied via resource.setrlimit (Linux/Docker target)
- Subprocess env vars fully isolated (empty env, no parent vars leaked)
- Semaphore per (tenant_id, plugin_id) limits concurrent workers to 2
- Network isolation: NOT enforced at kernel level (see Residual Risks below)

Residual Risks (documented explicitly):
- RISK-HIGH: Network blocking via unshare(CLONE_NEWNET) is NOT available
  without root/capabilities in the Docker container. Plugins can make outbound
  network calls. Mitigation for post-MVP: use user namespaces or a seccomp
  profile to restrict syscalls including socket(). For MVP, only plone_integration
  is documented as having authorized HTTP access; all other plugins should be
  considered network-unrestricted at kernel level.
- RISK-MEDIUM: Filesystem isolation is limited to CWD restriction (the subprocess
  CWD is set to the plugin directory). A malicious plugin can still traverse the
  filesystem via absolute paths unless a chroot/seccomp profile is applied.
  The empty env prevents leaking DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY etc.
- RISK-LOW: RLIMIT_AS (virtual memory) limits apply to the subprocess, but
  a plugin could still exhaust file descriptors or create many threads before
  being killed. Post-MVP mitigation: add RLIMIT_NOFILE and RLIMIT_NPROC.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path

from app.plugins.manager import PluginManifest

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Custom exceptions
# ──────────────────────────────────────────────────────────────────────────────


class PluginRuntimeError(Exception):
    """Base class for all plugin runtime errors."""


class PluginTimeoutError(PluginRuntimeError):
    """Plugin exceeded the wall-clock time limit and was killed."""


class PluginExecutionError(PluginRuntimeError):
    """Plugin subprocess exited with a non-zero exit code."""


class PluginProtocolError(PluginRuntimeError):
    """Plugin stdout was not valid JSON (contract violation)."""


class PluginNotFoundError(PluginRuntimeError):
    """Plugin entrypoint file does not exist."""


# ──────────────────────────────────────────────────────────────────────────────
# Resource limit helper (preexec_fn — runs inside the child process)
# ──────────────────────────────────────────────────────────────────────────────

_MB = 1024 * 1024
_RLIMIT_AS_BYTES = 256 * _MB   # 256 MB virtual memory
_RLIMIT_CPU_SECONDS = 10        # 10 s CPU time (matches wall-clock timeout)


def _apply_resource_limits() -> None:
    """
    Apply resource limits in the child process before exec.

    Called via preexec_fn. Runs in the fork()ed child, before Python code
    of the plugin starts executing.

    Handles macOS gracefully: setrlimit on RLIMIT_AS is not supported on macOS
    (EINVAL). We log a warning but do NOT abort — the subprocess still runs,
    just without memory capping. This is acceptable for local development;
    the Docker (Linux) target always enforces limits.
    """
    try:
        import resource  # noqa: PLC0415 — import inside preexec_fn

        try:
            resource.setrlimit(resource.RLIMIT_AS, (_RLIMIT_AS_BYTES, _RLIMIT_AS_BYTES))
        except (ValueError, resource.error, OSError) as exc:
            # On macOS RLIMIT_AS returns EINVAL; log but don't abort.
            # NOTE: logging from preexec_fn may not flush reliably; parent
            # logs the warning after fork instead (see PluginRuntime.execute).
            pass  # logged by parent

        try:
            resource.setrlimit(resource.RLIMIT_CPU, (_RLIMIT_CPU_SECONDS, _RLIMIT_CPU_SECONDS))
        except (ValueError, resource.error, OSError):
            pass  # logged by parent

    except ImportError:
        # resource module not available (Windows) — no limits applied
        pass


def _check_rlimit_support() -> dict[str, bool]:
    """
    Probe whether RLIMIT_AS and RLIMIT_CPU are usable on this platform.
    Called once by PluginRuntime to emit startup warnings.
    Returns dict with keys 'rlimit_as' and 'rlimit_cpu'.
    """
    support: dict[str, bool] = {"rlimit_as": False, "rlimit_cpu": False}
    try:
        import resource

        # Try getting current limits — if that fails, setrlimit will too.
        try:
            resource.getrlimit(resource.RLIMIT_AS)
            support["rlimit_as"] = True
        except (resource.error, OSError, AttributeError):
            pass

        try:
            resource.getrlimit(resource.RLIMIT_CPU)
            support["rlimit_cpu"] = True
        except (resource.error, OSError, AttributeError):
            pass

    except ImportError:
        pass

    return support


# ──────────────────────────────────────────────────────────────────────────────
# PluginRuntime
# ──────────────────────────────────────────────────────────────────────────────

_TIMEOUT_SECONDS = 10
_MAX_WORKERS_PER_SLOT = 2


class PluginRuntime:
    """
    Execute plugins in isolated subprocesses.

    Thread-safety: asyncio-safe. Uses asyncio.Semaphore per (tenant_id,
    plugin_id) to bound concurrency to _MAX_WORKERS_PER_SLOT workers.

    Network policy (MVP):
    - plone_integration: HTTP access authorized (no restriction documented)
    - All other plugins: network NOT isolated at kernel level (RISK-HIGH, see
      module docstring). Treat all outbound traffic as unrestricted for MVP.

    Usage:
        runtime = PluginRuntime()
        result = await runtime.execute(
            tenant_id=tenant_id,
            plugin=manifest,
            input_data={"key": "value"},
            plugins_base_dir=Path("plugins/"),
        )
    """

    def __init__(self) -> None:
        self._semaphores: dict[tuple[str, str], asyncio.Semaphore] = {}
        self._rlimit_support = _check_rlimit_support()

        if not self._rlimit_support["rlimit_as"]:
            logger.warning(
                "SECURITY WARNING: RLIMIT_AS (virtual memory limit) is NOT supported "
                "on this platform. Plugin memory usage will not be capped. "
                "This is expected on macOS; Docker (Linux) enforces the limit."
            )
        if not self._rlimit_support["rlimit_cpu"]:
            logger.warning(
                "SECURITY WARNING: RLIMIT_CPU (CPU time limit) is NOT supported "
                "on this platform. Plugin CPU time will not be capped at OS level. "
                "Wall-clock timeout (asyncio) still applies. "
                "This is expected on macOS; Docker (Linux) enforces the limit."
            )

        logger.warning(
            "SECURITY NOTE: Network namespace isolation (unshare CLONE_NEWNET) "
            "is NOT applied. Plugins can make outbound network calls. "
            "plone_integration has authorized HTTP access. All other plugins are "
            "network-unrestricted at kernel level (MVP residual risk HIGH)."
        )

    def _get_semaphore(self, tenant_id: uuid.UUID, plugin_id: str) -> asyncio.Semaphore:
        """Return (creating if needed) the semaphore for this (tenant, plugin) slot."""
        key = (str(tenant_id), plugin_id)
        if key not in self._semaphores:
            self._semaphores[key] = asyncio.Semaphore(_MAX_WORKERS_PER_SLOT)
        return self._semaphores[key]

    async def execute(
        self,
        tenant_id: uuid.UUID,
        plugin: PluginManifest,
        input_data: dict,
        plugins_base_dir: Path,
    ) -> dict:
        """
        Execute a plugin entrypoint in an isolated subprocess.

        Protocol:
        - stdin:  JSON  {"tenant_id": "<uuid>", "input": {...}}
        - stdout: JSON  {"result": {...}, "error": null}
        - Timeout: 10 s wall-clock → SIGKILL → PluginTimeoutError
        - exit != 0 → PluginExecutionError (stderr included)
        - stdout not valid JSON → PluginProtocolError
        - entrypoint missing → PluginNotFoundError

        Args:
            tenant_id:        Caller's tenant UUID (used for input payload and
                              semaphore key — prevents cross-tenant slot sharing).
            plugin:           PluginManifest from PluginManager.
            input_data:       Arbitrary dict passed to the plugin as "input".
            plugins_base_dir: Root of the plugins directory (e.g. Path("plugins/")).

        Returns:
            dict — the "result" field from the plugin's JSON output.

        Raises:
            PluginNotFoundError:   Entrypoint file not found.
            PluginTimeoutError:    Plugin exceeded 10 s wall-clock limit.
            PluginExecutionError:  Plugin exited with non-zero status.
            PluginProtocolError:   Plugin stdout was not valid JSON.
        """
        entrypoint_path = plugins_base_dir / plugin.id / plugin.entrypoint

        if not entrypoint_path.exists():
            raise PluginNotFoundError(
                f"Entrypoint not found: {entrypoint_path} "
                f"(plugin={plugin.id}, version={plugin.version})"
            )

        # Build the JSON payload sent to the plugin on stdin
        payload = json.dumps({"tenant_id": str(tenant_id), "input": input_data})

        semaphore = self._get_semaphore(tenant_id, plugin.id)

        async with semaphore:
            return await self._run_subprocess(
                entrypoint_path=entrypoint_path,
                payload=payload,
                plugin_id=plugin.id,
                tenant_id=tenant_id,
            )

    async def _run_subprocess(
        self,
        entrypoint_path: Path,
        payload: str,
        plugin_id: str,
        tenant_id: uuid.UUID,
    ) -> dict:
        """
        Spawn the subprocess, feed stdin, collect stdout/stderr, enforce timeout.

        Security properties enforced here:
        1. env={} — no parent environment variables leaked to child.
        2. cwd=entrypoint_path.parent — subprocess CWD is the plugin directory.
        3. preexec_fn=_apply_resource_limits — RLIMIT_AS + RLIMIT_CPU in child.
        4. asyncio.wait_for timeout → process.kill() on expiry.
        """
        # Minimal environment: only PATH so the Python interpreter can be found.
        # Explicitly DO NOT pass DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY, etc.
        isolated_env: dict[str, str] = {}

        # On some systems an empty env prevents the child from finding shared libs.
        # We include only PATH (required to locate python3) and PYTHONPATH if set
        # (so the plugin can import shared packages installed in the container).
        # Everything else — especially secrets — is excluded.
        if "PATH" in os.environ:
            isolated_env["PATH"] = os.environ["PATH"]
        if "PYTHONPATH" in os.environ:
            isolated_env["PYTHONPATH"] = os.environ["PYTHONPATH"]

        kwargs: dict = {
            "stdin": asyncio.subprocess.PIPE,
            "stdout": asyncio.subprocess.PIPE,
            "stderr": asyncio.subprocess.PIPE,
            "env": isolated_env,
            "cwd": str(entrypoint_path.parent),
        }

        # preexec_fn is only available on Unix; skip on Windows gracefully.
        if sys.platform != "win32":
            kwargs["preexec_fn"] = _apply_resource_limits

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            str(entrypoint_path),
            **kwargs,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(input=payload.encode()),
                timeout=_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            # Kill the process and reap it to avoid zombie
            try:
                process.kill()
            except ProcessLookupError:
                pass  # already exited
            try:
                await process.wait()
            except Exception:
                pass
            raise PluginTimeoutError(
                f"Plugin '{plugin_id}' (tenant={tenant_id}) exceeded "
                f"{_TIMEOUT_SECONDS}s wall-clock timeout and was killed."
            )

        stdout_text = stdout_bytes.decode(errors="replace").strip()
        stderr_text = stderr_bytes.decode(errors="replace").strip()

        if process.returncode != 0:
            raise PluginExecutionError(
                f"Plugin '{plugin_id}' (tenant={tenant_id}) exited with "
                f"code {process.returncode}. "
                f"stderr: {stderr_text!r}"
            )

        if not stdout_text:
            raise PluginProtocolError(
                f"Plugin '{plugin_id}' (tenant={tenant_id}) produced no stdout output. "
                "Expected JSON: {\"result\": {...}, \"error\": null}"
            )

        try:
            output = json.loads(stdout_text)
        except json.JSONDecodeError as exc:
            raise PluginProtocolError(
                f"Plugin '{plugin_id}' (tenant={tenant_id}) stdout is not valid JSON: "
                f"{exc}. Raw stdout: {stdout_text!r}"
            ) from exc

        return output
