# Handoff: US-010 — Plugin Manager

**Completed by:** Backend Dev
**Date:** 2026-03-27
**Status:** ✅ Done (35/35 tests passing)

## What Was Built

US-010 delivered a **plugin loader abstraction pattern** that decouples plugin discovery from plugin management. The implementation separates concerns into three layers:

1. **PluginManifest** — Pydantic model validating manifest schema (id, version, capabilities, entrypoint, description)
2. **Plugin Loaders** — Protocol-based abstraction for plugin discovery:
   - `FSPluginLoader` — filesystem-based discovery (scans `plugins_dir/*/manifest.yaml`)
   - `PackagePluginLoader` — stub for future package-based discovery via `importlib.metadata`
3. **PluginManager** — orchestrates loaders, manages tenant plugin state, ensures cross-tenant isolation

**Key architectural decision:** Loaders are merged with last-wins precedence (later loaders override earlier ones on plugin ID conflict). This mirrors Buildout's "sources" pattern and enables filesystem plugins to override package plugins.

Backward compatibility maintained: existing code using `PluginManager().load_manifests(plugins_dir)` works unchanged.

## Integration Points for US-011

### What US-011 (Security Engineer) needs to know

1. **PluginManager API surface:**
   - `manager.get_active_plugins(tenant_id, db)` → `list[PluginManifest]` for enabled plugins only
   - `manager.enable_plugin(tenant_id, plugin_name, db)` → updates DB, immediate effect
   - `manager.disable_plugin(tenant_id, plugin_name, db)` → updates DB, immediate effect
   - `manager._manifests` — internal dict containing all loaded manifests keyed by `plugin_id`

2. **Plugin entrypoint contract:**
   - Each manifest includes an `entrypoint: str` field (e.g., `"plugin.py"`)
   - This is the file path relative to the plugin directory that US-011 must execute
   - Example: `plugins/plone_integration/plugin.py`

3. **Tenant isolation boundary:**
   - `get_active_plugins()` queries `tenant_plugins` table with `WHERE tenant_id=X AND enabled=True`
   - DB query enforces isolation; PluginManager does not load plugin code
   - US-011 must ensure plugin execution (in subprocess via MCP) does not leak tenant context to sibling plugins

4. **Manifest validation:**
   - Manifests are validated at load time via Pydantic (strict mode, extra fields forbidden)
   - Malformed manifests raise `ValueError` immediately; not silently skipped
   - This is safe-by-default: missing manifest on disk = plugin silently skipped in `get_active_plugins()`

### Files US-011 will touch

- `backend/app/plugins/manager.py` — read the entrypoint field and tenant isolation pattern
- `backend/app/plugins/loaders.py` — understand how manifests are loaded
- `backend/app/plugins/__init__.py` — import PluginManager and PluginManifest
- `backend/app/api/v1/plugins.py` — stub endpoint (not yet implemented; US-021 will add REST API)

## File Ownership

| File | Owner | Notes |
|------|-------|-------|
| `backend/app/plugins/manager.py` | Backend Dev | Core PluginManager orchestration; read-only for US-011 |
| `backend/app/plugins/loaders.py` | Backend Dev | Plugin discovery abstraction; read-only for US-011 |
| `backend/app/plugins/__init__.py` | Backend Dev | Exports; read-only for downstream agents |
| `backend/app/db/models.py` | Backend Dev | TenantPlugin model (already existed); read-only for all |
| `backend/tests/test_plugin_manager.py` | QA Engineer | Extends with runtime/isolation tests after US-011 |

## Residual Risks / Known Gaps

### MEDIUM: PackagePluginLoader is MVP stub

**Status:** Intentional
**Impact:** Plugin distribution via PyPI not yet supported. Filesystem plugins only.
**Mitigation:** Clearly documented as TODO. Can be implemented incrementally post-MVP. `load()` returns empty dict, so no silent failures.
**For US-011:** No impact. Treat PackagePluginLoader as not available.

### MEDIUM: TenantPlugin.config (JSONB) not validated

**Status:** Deferred
**Impact:** Plugin configuration stored in DB but not validated against manifest schema.
**Mitigation:** Documented as "Deferred to plugin layer". Validation can be added in US-011 (plugin runtime).
**For US-011:** When executing a plugin, validate its `config` before passing to entrypoint.

### LOW: Manifest on-disk mismatch

**Status:** Intentional safe-by-default
**Impact:** If `manifest.yaml` is deleted but DB row remains, `get_active_plugins()` silently filters it out.
**Mitigation:** This is safe. DB orphans are harmless; they just won't be activated.
**For US-011:** If a plugin is expected but not returned by `get_active_plugins()`, check if manifest file exists on disk.

## How to Verify This Works

### Run the test suite

```bash
# In project root
make up                    # Start Docker environment
make test                  # Full suite (35/35 passing)

# Or just plugin tests
docker exec ai-platform-api python -m pytest tests/test_plugin_manager.py -v

# With coverage
docker exec ai-platform-api python -m pytest tests/test_plugin_manager.py \
  --cov=app.plugins --cov-report=term-missing
```

### Manual verification

```python
# Filesystem loader
from pathlib import Path
from app.plugins import PluginManager, FSPluginLoader

loader = FSPluginLoader(Path("./plugins"))
manager = PluginManager(loaders=[loader])
manifests = manager.load_manifests()
print(f"Loaded {len(manifests)} plugins: {list(manifests.keys())}")
# Expected: ['plone_integration', 'docs_rag', 'block_builder', 'doc_ingestion']

# Multiple loaders (Package + Filesystem with precedence)
from app.plugins import PackagePluginLoader
manager = PluginManager(loaders=[
    PackagePluginLoader(),
    FSPluginLoader(Path("./plugins")),
])
manifests = manager.load_manifests()
# Filesystem plugins override packages on conflict
```

### Verify tenant isolation at API level

This requires a running API. Tests confirm it, but for manual check:

```bash
# Start the API
make up

# Query active plugins for tenant 1 (should be empty or all plugins depending on config)
curl -X GET http://localhost:8000/api/v1/tenants/me/plugins \
  -H "Authorization: Bearer <tenant1_token>"

# Query for tenant 2 (should NOT see tenant 1's enabled plugins)
curl -X GET http://localhost:8000/api/v1/tenants/me/plugins \
  -H "Authorization: Bearer <tenant2_token>"
```

## Test Inventory

**Total: 35/35 passing (100%)**

### Original tests (26 — all backward compatible)
- PluginManifest validation (7)
- load_manifests function (9)
- get_active_plugins (4)
- enable_plugin (2)
- disable_plugin (2)
- Cross-tenant isolation (2)

### New loader pattern tests (9)
- FSPluginLoader single/multiple/empty/nonexistent (4)
- PackagePluginLoader stub (1)
- PluginManager + Loaders integration (4):
  - Manager with FSPluginLoader
  - Merge multiple loaders
  - Loader precedence (later overrides earlier)
  - Backward compatibility with `plugins_dir` argument

## Dependencies & External Calls

**No new external dependencies added.** Uses existing:
- `pyyaml>=6.0.0` — manifest YAML parsing
- `pytest`, `pytest-asyncio` — tests
- `typing.Protocol` — standard library (Python 3.8+)

PluginManager makes NO external API calls. All DB operations passed in from caller (clean dependency injection).

## Next Phase: US-011 (Security Engineer)

US-011 will implement `PluginRuntime` — the layer that executes plugins in isolated subprocess using the manifests loaded by PluginManager.

**Contract between US-010 and US-011:**

```python
# US-010 provides
active_plugins = await manager.get_active_plugins(tenant_id, db)
for plugin in active_plugins:
    entrypoint = plugin.entrypoint      # e.g., "plugin.py"
    capabilities = plugin.capabilities  # e.g., ["generate", "query"]
    version = plugin.version            # e.g., "1.0.0"

# US-011 executes
# subprocess.run([python, f"plugins/{plugin.id}/{entrypoint}"], ...)
# with tenant context passed as environment or stdin
# with resource limits and timeout
# with audit logging
```

**US-011 must ensure:**
1. Subprocess environment isolated per-tenant (no shared state leak)
2. Timeout enforcement (no hung plugins)
3. Audit logging of plugin invocations
4. Error handling: malformed entrypoint, missing file, non-zero exit codes

---

**Status for handoff:** Ready. All acceptance criteria met. 35/35 tests passing. Backward compatible. Extensible for future loaders.
