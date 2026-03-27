"""
Plugin Runtime tests — subprocess isolation, timeout, JSON protocol, cross-tenant isolation.

All tests use real subprocesses (no mocking of the subprocess layer) because the
security properties under test (timeout enforcement, env isolation, resource limits)
can only be verified end-to-end.

Tests create temporary plugin directories with minimal plugin.py scripts.
No running DB required.
"""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

from app.plugins.manager import PluginManifest
from app.plugins.runtime import (
    PluginRuntime,
    PluginExecutionError,
    PluginNotFoundError,
    PluginProtocolError,
    PluginTimeoutError,
)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _make_plugin(
    plugins_dir: Path,
    plugin_id: str,
    script: str,
    version: str = "0.1.0",
    capabilities: list[str] | None = None,
) -> PluginManifest:
    """
    Write a plugin.py script into plugins_dir/{plugin_id}/plugin.py and return
    the corresponding PluginManifest.
    """
    plugin_dir = plugins_dir / plugin_id
    plugin_dir.mkdir(parents=True, exist_ok=True)
    (plugin_dir / "plugin.py").write_text(script)
    return PluginManifest(
        id=plugin_id,
        version=version,
        capabilities=capabilities or [],
        entrypoint="plugin.py",
        description=f"Test plugin {plugin_id}",
    )


# Minimal well-behaved plugin: reads JSON from stdin, echoes it back as result.
_ECHO_SCRIPT = """\
import sys, json
payload = json.loads(sys.stdin.read())
print(json.dumps({"result": payload, "error": None}))
"""

# Plugin that sleeps forever (triggers timeout).
_SLEEP_SCRIPT = """\
import time
time.sleep(999)
"""

# Plugin that exits with code 1.
_EXIT_ERROR_SCRIPT = """\
import sys
sys.stderr.write("something went wrong")
sys.exit(1)
"""

# Plugin that writes invalid JSON to stdout.
_BAD_JSON_SCRIPT = """\
print("this is not json")
"""

# Plugin that dumps its own environment variables as the result.
_ENV_DUMP_SCRIPT = """\
import sys, json, os
env = dict(os.environ)
print(json.dumps({"result": env, "error": None}))
"""

# Plugin that reads input and returns only the tenant_id field.
_TENANT_ECHO_SCRIPT = """\
import sys, json
payload = json.loads(sys.stdin.read())
print(json.dumps({"result": {"tenant_id": payload["tenant_id"]}, "error": None}))
"""


# ──────────────────────────────────────────────────────────────────────────────
# Basic execution tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_basic_echo():
    """Well-behaved plugin receives JSON input and returns JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "echo_plugin", _ECHO_SCRIPT)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()
        result = await runtime.execute(
            tenant_id=tenant_id,
            plugin=manifest,
            input_data={"hello": "world"},
            plugins_base_dir=plugins_dir,
        )

        assert isinstance(result, dict)
        # Echo plugin returns the full payload (tenant_id + input) as result
        assert result["result"]["input"] == {"hello": "world"}
        assert result["result"]["tenant_id"] == str(tenant_id)


@pytest.mark.asyncio
async def test_execute_runs_in_subprocess():
    """Plugin execution is in a subprocess, not in-process (no shared state)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        # Plugin writes its own PID to the result
        pid_script = """\
import sys, json, os
payload = json.loads(sys.stdin.read())
print(json.dumps({"result": {"pid": os.getpid()}, "error": None}))
"""
        manifest = _make_plugin(plugins_dir, "pid_plugin", pid_script)
        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()
        result = await runtime.execute(
            tenant_id=tenant_id,
            plugin=manifest,
            input_data={},
            plugins_base_dir=plugins_dir,
        )

        plugin_pid = result["result"]["pid"]
        # The plugin PID must differ from the current process PID
        assert plugin_pid != os.getpid()


# ──────────────────────────────────────────────────────────────────────────────
# Timeout enforcement
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_timeout_kills_plugin():
    """Plugin that sleeps forever is killed after 10s and raises PluginTimeoutError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "sleep_plugin", _SLEEP_SCRIPT)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        with pytest.raises(PluginTimeoutError) as exc_info:
            await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )

        assert "sleep_plugin" in str(exc_info.value)
        assert "timeout" in str(exc_info.value).lower() or "killed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_timeout_error_is_subclass_of_plugin_runtime_error():
    """PluginTimeoutError is a PluginRuntimeError."""
    from app.plugins.runtime import PluginRuntimeError
    assert issubclass(PluginTimeoutError, PluginRuntimeError)


# ──────────────────────────────────────────────────────────────────────────────
# Error handling tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_execute_nonzero_exit_raises_execution_error():
    """Plugin exiting with code != 0 raises PluginExecutionError with stderr."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "error_plugin", _EXIT_ERROR_SCRIPT)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        with pytest.raises(PluginExecutionError) as exc_info:
            await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )

        error_msg = str(exc_info.value)
        assert "error_plugin" in error_msg
        # stderr content should be present in the error message
        assert "something went wrong" in error_msg


@pytest.mark.asyncio
async def test_execute_bad_json_raises_protocol_error():
    """Plugin outputting non-JSON stdout raises PluginProtocolError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "badjson_plugin", _BAD_JSON_SCRIPT)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        with pytest.raises(PluginProtocolError) as exc_info:
            await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )

        assert "badjson_plugin" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_missing_entrypoint_raises_not_found():
    """Manifest pointing to a non-existent entrypoint raises PluginNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        # Create the directory but NOT the entrypoint file
        (plugins_dir / "missing_plugin").mkdir()
        manifest = PluginManifest(
            id="missing_plugin",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",  # does not exist
        )

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        with pytest.raises(PluginNotFoundError) as exc_info:
            await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )

        assert "missing_plugin" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_empty_stdout_raises_protocol_error():
    """Plugin that writes nothing to stdout raises PluginProtocolError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        silent_script = "import sys\n"  # no stdout output
        manifest = _make_plugin(plugins_dir, "silent_plugin", silent_script)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        with pytest.raises(PluginProtocolError):
            await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Environment isolation tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_subprocess_env_is_isolated():
    """
    Subprocess does NOT receive parent process env vars.

    Verifies that DATABASE_URL, SECRET_KEY, ANTHROPIC_API_KEY and similar
    sensitive variables are not passed to the plugin subprocess.
    """
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "env_plugin", _ENV_DUMP_SCRIPT)

        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        # Inject a fake secret into the current process environment
        os.environ["__TEST_SECRET_SHOULD_NOT_LEAK__"] = "super_secret_value"
        try:
            result = await runtime.execute(
                tenant_id=tenant_id,
                plugin=manifest,
                input_data={},
                plugins_base_dir=plugins_dir,
            )
        finally:
            del os.environ["__TEST_SECRET_SHOULD_NOT_LEAK__"]

        child_env = result["result"]
        assert "__TEST_SECRET_SHOULD_NOT_LEAK__" not in child_env, (
            "Secret env var leaked into plugin subprocess!"
        )
        # Common secrets that must never appear
        for secret_key in ("DATABASE_URL", "SECRET_KEY", "ANTHROPIC_API_KEY", "REDIS_URL"):
            assert secret_key not in child_env, (
                f"{secret_key} was found in plugin subprocess environment — "
                "this is a security violation."
            )


# ──────────────────────────────────────────────────────────────────────────────
# Cross-tenant isolation tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cross_tenant_input_isolation():
    """
    Tenant A's input is NOT visible in Tenant B's plugin execution.

    Each call passes only the caller's tenant_id and input; the subprocess
    receives exactly the payload it was given and nothing from another tenant.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "tenant_echo", _TENANT_ECHO_SCRIPT)

        runtime = PluginRuntime()
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        result_a = await runtime.execute(
            tenant_id=tenant_a,
            plugin=manifest,
            input_data={"secret": "tenant_a_secret"},
            plugins_base_dir=plugins_dir,
        )
        result_b = await runtime.execute(
            tenant_id=tenant_b,
            plugin=manifest,
            input_data={"secret": "tenant_b_secret"},
            plugins_base_dir=plugins_dir,
        )

        # Each result carries only the respective tenant's tenant_id
        assert result_a["result"]["tenant_id"] == str(tenant_a)
        assert result_b["result"]["tenant_id"] == str(tenant_b)
        # tenant_a result must not contain tenant_b's UUID
        assert str(tenant_b) not in json.dumps(result_a)
        # tenant_b result must not contain tenant_a's UUID
        assert str(tenant_a) not in json.dumps(result_b)


@pytest.mark.asyncio
async def test_semaphore_per_tenant_plugin_slot():
    """
    Semaphore is keyed by (tenant_id, plugin_id).

    Two different tenants running the same plugin have independent semaphores
    (so they don't block each other up to the max-worker limit).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "echo_plugin", _ECHO_SCRIPT)

        runtime = PluginRuntime()
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()

        # Both tenants should be able to run concurrently without deadlock
        import asyncio
        results = await asyncio.gather(
            runtime.execute(tenant_id=tenant_a, plugin=manifest,
                            input_data={"t": "a"}, plugins_base_dir=plugins_dir),
            runtime.execute(tenant_id=tenant_b, plugin=manifest,
                            input_data={"t": "b"}, plugins_base_dir=plugins_dir),
        )

        assert results[0]["result"]["input"]["t"] == "a"
        assert results[1]["result"]["input"]["t"] == "b"

        # Verify separate semaphores exist for each (tenant, plugin) pair
        key_a = (str(tenant_a), "echo_plugin")
        key_b = (str(tenant_b), "echo_plugin")
        assert key_a in runtime._semaphores
        assert key_b in runtime._semaphores
        assert runtime._semaphores[key_a] is not runtime._semaphores[key_b]


# ──────────────────────────────────────────────────────────────────────────────
# JSON protocol contract tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_input_sent_as_json_on_stdin():
    """Plugin receives input data correctly via stdin JSON protocol."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        # Plugin reads stdin and asserts specific fields exist
        check_script = """\
import sys, json
payload = json.loads(sys.stdin.read())
assert "tenant_id" in payload, "tenant_id missing from payload"
assert "input" in payload, "input missing from payload"
print(json.dumps({"result": {"ok": True}, "error": None}))
"""
        manifest = _make_plugin(plugins_dir, "check_plugin", check_script)
        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        result = await runtime.execute(
            tenant_id=tenant_id,
            plugin=manifest,
            input_data={"foo": "bar"},
            plugins_base_dir=plugins_dir,
        )
        assert result["result"]["ok"] is True


@pytest.mark.asyncio
async def test_tenant_id_in_payload():
    """tenant_id field in JSON payload matches the UUID passed to execute()."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        manifest = _make_plugin(plugins_dir, "tenant_check", _TENANT_ECHO_SCRIPT)
        runtime = PluginRuntime()
        tenant_id = uuid.uuid4()

        result = await runtime.execute(
            tenant_id=tenant_id,
            plugin=manifest,
            input_data={},
            plugins_base_dir=plugins_dir,
        )
        assert result["result"]["tenant_id"] == str(tenant_id)


# ──────────────────────────────────────────────────────────────────────────────
# Exception hierarchy
# ──────────────────────────────────────────────────────────────────────────────


def test_exception_hierarchy():
    """All custom exceptions are subclasses of PluginRuntimeError."""
    from app.plugins.runtime import PluginRuntimeError
    assert issubclass(PluginTimeoutError, PluginRuntimeError)
    assert issubclass(PluginExecutionError, PluginRuntimeError)
    assert issubclass(PluginProtocolError, PluginRuntimeError)
    assert issubclass(PluginNotFoundError, PluginRuntimeError)


# ──────────────────────────────────────────────────────────────────────────────
# Import of os (needed in test_execute_runs_in_subprocess)
# ──────────────────────────────────────────────────────────────────────────────

import os  # noqa: E402  — needed by test_execute_runs_in_subprocess
