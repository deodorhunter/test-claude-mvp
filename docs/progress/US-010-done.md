# US-010: PluginLoader Abstraction Refactoring — Completed

**Status:** ✅ Done
**Test Results:** 35/35 passing (original 26 + 9 new loader pattern tests)
**Date:** 2026-03-27

## Summary

Successfully refactored `PluginManager` to support a **plugin loader abstraction pattern**. The implementation separates plugin discovery from plugin management, enabling multiple plugin sources (filesystem, packages, custom) without coupling `PluginManager` to any specific discovery mechanism.

## Phase 1: Original Implementation (Existing)

### PluginManager (`backend/app/plugins/manager.py`)

**PluginManifest (Pydantic model)**
- Fields: `id: str`, `version: str`, `capabilities: list[str]`, `entrypoint: str`, `description: str = ""`
- Extra fields are forbidden (strict validation)
- All required fields enforce non-null, non-empty constraints

**PluginManager core methods (unchanged behavior)**

1. **`get_active_plugins(tenant_id: UUID, db: AsyncSession) -> list[PluginManifest]`**
   - Queries `tenant_plugins` table: `WHERE tenant_id=X AND enabled=True`
   - Returns only manifests that exist in loaded plugin set (filters orphaned DB records)
   - Ensures cross-tenant isolation at DB query level

2. **`enable_plugin(tenant_id: UUID, plugin_name: str, db: AsyncSession) -> None`**
   - If row exists → UPDATE `enabled=True`
   - If row doesn't exist → INSERT with `enabled=True`

3. **`disable_plugin(tenant_id: UUID, plugin_name: str, db: AsyncSession) -> None`**
   - If row exists → UPDATE `enabled=False`
   - If row doesn't exist → no-op (no error)

## Phase 2: Loader Abstraction Refactoring (New)

### New Module: `backend/app/plugins/loaders.py`

Implemented three components:

#### 1. `PluginLoader` (Protocol)
- Defines the interface for plugin discovery
- Single method: `load() -> dict[str, PluginManifest]`
- Enables any loader implementation to conform without inheritance

#### 2. `FSPluginLoader` (Filesystem implementation)
- Extracted manifest loading logic from original `PluginManager.load_manifests()`
- Loads plugins from `plugins_dir/*/manifest.yaml`
- Supports:
  - Recursive directory scanning
  - YAML parsing and validation
  - Pydantic validation of manifest structure
  - Graceful handling of missing/nonexistent directories

#### 3. `PackagePluginLoader` (Package discovery stub)
- Future implementation for `importlib.metadata.entry_points()`
- Currently returns empty dict (MVP only)
- Defines the interface for future package-based plugin discovery

### Refactored: `backend/app/plugins/manager.py`

#### Constructor changes
```python
def __init__(self, loaders: list[PluginLoader] | None = None):
    self._loaders = loaders or []
    self._manifests: dict[str, PluginManifest] = {}
```

#### `load_manifests()` signature update
```python
def load_manifests(self, plugins_dir: Path | None = None) -> dict[str, PluginManifest]
```

**Three usage patterns:**

1. **New pattern with loaders (preferred):**
   ```python
   manager = PluginManager(loaders=[FSPluginLoader(Path("./plugins"))])
   manifest = manager.load_manifests()
   ```

2. **Multiple loaders with precedence:**
   ```python
   manager = PluginManager(loaders=[
       PackagePluginLoader(),  # Check packages first
       FSPluginLoader(Path("./plugins")),  # Filesystem overrides
   ])
   manifest = manager.load_manifests()
   ```

3. **Backward compatible (existing code works unchanged):**
   ```python
   manager = PluginManager()
   manifest = manager.load_manifests(Path("./plugins"))
   ```

**Loader merging and precedence:**
- Results from all loaders are merged via `dict.update()`
- Later loaders override earlier ones on duplicate `plugin_id`
- FSPluginLoader should be last in list if filesystem plugins should take precedence

### Updated: `backend/app/plugins/__init__.py`

Added exports:
- `FSPluginLoader`
- `PackagePluginLoader`
- `PluginLoader`

## Testing

### Test Results
```
35/35 tests passing (100%)

Original tests (26):  ✅ All passing
New loader tests (9): ✅ All passing
No regressions
```

### Test Coverage

**Original tests (26 tests — all passing, backward compatible):**
- PluginManifest validation (7 tests)
- load_manifests function (9 tests)
- get_active_plugins (4 tests)
- enable_plugin (2 tests)
- disable_plugin (2 tests)
- Cross-tenant isolation (2 tests)

**New loader pattern tests (9 tests):**

**FSPluginLoader tests (4):**
- `test_fs_plugin_loader_single_plugin()` — loads one manifest
- `test_fs_plugin_loader_multiple_plugins()` — loads multiple manifests
- `test_fs_plugin_loader_empty_dir()` — empty dir returns empty dict
- `test_fs_plugin_loader_nonexistent_dir()` — nonexistent dir returns empty dict

**PackagePluginLoader tests (1):**
- `test_package_plugin_loader_stub()` — returns empty dict (MVP)

**PluginManager + Loaders integration tests (4):**
- `test_plugin_manager_with_fs_loader()` — manager initialized with FSPluginLoader
- `test_plugin_manager_merge_multiple_loaders()` — merges results from multiple loaders
- `test_plugin_manager_loader_precedence()` — later loaders override earlier ones
- `test_plugin_manager_backward_compat_plugins_dir_arg()` — backward compatibility with `plugins_dir` arg

## Design Rationale

### 1. Protocol-based design
- Used `typing.Protocol` instead of ABC to avoid inheritance complexity
- Loaders only need to implement `load()` method
- Enables duck-typing for future custom loaders

### 2. Backward compatibility
- Existing code requires zero changes
- `PluginManager()` + `load_manifests(plugins_dir)` continues to work
- New code can adopt loaders incrementally

### 3. Loader precedence
- Later loaders in the list override earlier ones (via `dict.update()`)
- Mirrors Buildout's "sources" development pattern
- FSPluginLoader should be last if filesystem plugins should take precedence over packages

### 4. Future-proof extensibility
- New loader types can be added without modifying `PluginManager`
- Examples for future implementation:
  - `HTTPPluginLoader` — fetch manifests from remote registry
  - `DatabasePluginLoader` — load from DB
  - `ZipPluginLoader` — load from zip archive

## Acceptance Criteria ✅

- [x] `PluginLoader` protocol defined with `load()` method
- [x] `FSPluginLoader` extracts manifest loading logic from `PluginManager`
- [x] `PackagePluginLoader` stub returns empty dict
- [x] `PluginManager.__init__()` accepts optional loaders list
- [x] `PluginManager.load_manifests()` supports loaders and backward-compatible arg
- [x] Loader precedence: later loaders override earlier ones
- [x] All 26 original tests pass without modification
- [x] 9 new loader pattern tests added and passing
- [x] Exports in `__init__.py` include all loaders
- [x] No external dependencies added
- [x] Docker smoke test: 35/35 tests passing

## Residual Risks

1. **Plugin manifest on disk mismatch**: If `manifest.yaml` is deleted but DB row remains, `get_active_plugins()` silently skips it. Intentional (safe-by-default).

2. **No plugin lifecycle hooks**: PluginManager doesn't call plugin init/cleanup code. By design. Plugin invocation handled by MCP layer (US-015).

3. **Config field unused**: `TenantPlugin.config` (JSONB) loaded but not validated. Deferred to plugin layer.

## Running Tests

```bash
# In Docker container
docker exec ai-platform-api python -m pytest tests/test_plugin_manager.py -v

# Or via make
make test  # runs full test suite including plugin tests

# Coverage
docker exec ai-platform-api python -m pytest tests/test_plugin_manager.py --cov=app.plugins --cov-report=term-missing
```

## Files Modified/Created

**New:**
- `backend/app/plugins/loaders.py` — FSPluginLoader, PackagePluginLoader, PluginLoader protocol

**Modified:**
- `backend/app/plugins/manager.py` — refactored to support loaders
- `backend/app/plugins/__init__.py` — added loader exports
- `backend/tests/test_plugin_manager.py` — added 9 new loader tests

## Dependencies

No new external dependencies added. Uses existing:
- `pyyaml>=6.0.0` — manifest YAML parsing
- `pytest`, `pytest-asyncio` — already in dev dependencies
- `typing.Protocol` — standard library (Python 3.8+)

## Developer Notes

### For local development

```python
from pathlib import Path
from app.plugins import PluginManager, FSPluginLoader

# Clone plugins locally
plugins_dir = Path("./plugins")
loader = FSPluginLoader(plugins_dir)
manager = PluginManager(loaders=[loader])
manager.load_manifests()
```

### For production with future package plugins

```python
from app.plugins import PluginManager, FSPluginLoader, PackagePluginLoader

# Check installed packages, then local filesystem (filesystem wins on conflict)
manager = PluginManager(loaders=[
    PackagePluginLoader(),
    FSPluginLoader(Path("./plugins")),
])
manager.load_manifests()
```

## Integration Points (unchanged)

### Startup (as before)
```python
from app.plugins.manager import PluginManager

plugins_manager = PluginManager()
plugins_manager.load_manifests(Path("./plugins"))
```

### API endpoints (US-021 — unchanged)
```python
async def get_plugins(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    plugins_manager: PluginManager = Depends(),
):
    active = await plugins_manager.get_active_plugins(current_user.tenant_id, db)
    return [{"id": p.id, "version": p.version} for p in active]
```

## Ready for Next Phase

US-010 refactoring complete. Ready for:
- Phase 2b: Model Layer (MCP integration uses PluginManager)
- Phase 2c: RAG + MCP (plugin output handling)
- Incremental adoption of loader pattern in new code
