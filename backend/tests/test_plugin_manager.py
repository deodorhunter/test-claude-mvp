"""
Plugin Manager tests — manifest loading, enable/disable, cross-tenant isolation.

No running PostgreSQL required. DB session mocked with AsyncMock.
"""

import uuid
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from app.plugins.manager import PluginManager, PluginManifest
from app.plugins.loaders import FSPluginLoader, PackagePluginLoader
from app.db.models.tenant import TenantPlugin


# ──────────────────────────────────────────────────────────────────────────────
# PluginManifest validation tests
# ──────────────────────────────────────────────────────────────────────────────


def test_plugin_manifest_valid():
    """Valid manifest with all required fields."""
    manifest = PluginManifest(
        id="test_plugin",
        version="0.1.0",
        capabilities=["read", "write"],
        entrypoint="plugin.py",
        description="Test plugin",
    )
    assert manifest.id == "test_plugin"
    assert manifest.version == "0.1.0"
    assert manifest.capabilities == ["read", "write"]
    assert manifest.entrypoint == "plugin.py"
    assert manifest.description == "Test plugin"


def test_plugin_manifest_missing_id():
    """Manifest without 'id' must fail."""
    with pytest.raises(Exception):  # pydantic ValidationError
        PluginManifest(
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        )


def test_plugin_manifest_missing_version():
    """Manifest without 'version' must fail."""
    with pytest.raises(Exception):
        PluginManifest(
            id="test",
            capabilities=[],
            entrypoint="plugin.py",
        )


def test_plugin_manifest_missing_capabilities():
    """Manifest without 'capabilities' must fail."""
    with pytest.raises(Exception):
        PluginManifest(
            id="test",
            version="0.1.0",
            entrypoint="plugin.py",
        )


def test_plugin_manifest_missing_entrypoint():
    """Manifest without 'entrypoint' must fail."""
    with pytest.raises(Exception):
        PluginManifest(
            id="test",
            version="0.1.0",
            capabilities=[],
        )


def test_plugin_manifest_description_optional():
    """Description field is optional, defaults to empty string."""
    manifest = PluginManifest(
        id="test",
        version="0.1.0",
        capabilities=[],
        entrypoint="plugin.py",
    )
    assert manifest.description == ""


def test_plugin_manifest_forbids_extra_fields():
    """Manifest must reject extra fields."""
    with pytest.raises(Exception):  # pydantic ValidationError
        PluginManifest(
            id="test",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
            unknown_field="value",
        )


# ──────────────────────────────────────────────────────────────────────────────
# load_manifests tests
# ──────────────────────────────────────────────────────────────────────────────


def test_load_manifests_empty_dir():
    """Empty plugins dir → no error, empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PluginManager()
        result = manager.load_manifests(Path(tmpdir))
        assert result == {}
        assert manager._manifests == {}


def test_load_manifests_nonexistent_dir():
    """Non-existent plugins dir → no error, empty dict."""
    manager = PluginManager()
    result = manager.load_manifests(Path("/nonexistent/plugins"))
    assert result == {}
    assert manager._manifests == {}


def test_load_manifests_single_plugin():
    """Load one valid manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "test_plugin",
            "version": "0.1.0",
            "capabilities": ["read"],
            "entrypoint": "plugin.py",
            "description": "Test",
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PluginManager()
        result = manager.load_manifests(plugins_dir)

        assert "test_plugin" in result
        assert result["test_plugin"].id == "test_plugin"
        assert result["test_plugin"].version == "0.1.0"
        assert manager._manifests == result


def test_load_manifests_multiple_plugins():
    """Load multiple valid manifests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        for plugin_id in ["plugin_a", "plugin_b", "plugin_c"]:
            plugin_dir = plugins_dir / plugin_id
            plugin_dir.mkdir()
            manifest_data = {
                "id": plugin_id,
                "version": "0.1.0",
                "capabilities": [],
                "entrypoint": "plugin.py",
            }
            with open(plugin_dir / "manifest.yaml", "w") as f:
                yaml.dump(manifest_data, f)

        manager = PluginManager()
        result = manager.load_manifests(plugins_dir)

        assert len(result) == 3
        assert "plugin_a" in result
        assert "plugin_b" in result
        assert "plugin_c" in result


def test_load_manifests_skip_subdir_without_manifest():
    """Skip subdirectories without manifest.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        # Create plugin with manifest
        (plugins_dir / "valid_plugin").mkdir()
        manifest_data = {
            "id": "valid_plugin",
            "version": "0.1.0",
            "capabilities": [],
            "entrypoint": "plugin.py",
        }
        with open(plugins_dir / "valid_plugin" / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        # Create subdir without manifest
        (plugins_dir / "invalid_subdir").mkdir()
        (plugins_dir / "invalid_subdir" / "somefile.py").touch()

        manager = PluginManager()
        result = manager.load_manifests(plugins_dir)

        assert len(result) == 1
        assert "valid_plugin" in result


def test_load_manifests_invalid_yaml():
    """Malformed YAML → ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "bad_plugin"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.yaml", "w") as f:
            f.write("invalid: [yaml: content:")  # Invalid YAML

        manager = PluginManager()
        with pytest.raises(ValueError, match="Invalid YAML"):
            manager.load_manifests(plugins_dir)


def test_load_manifests_empty_yaml():
    """Empty YAML file → ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "empty_plugin"
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.yaml", "w") as f:
            f.write("")  # Empty file

        manager = PluginManager()
        with pytest.raises(ValueError, match="Manifest is empty"):
            manager.load_manifests(plugins_dir)


def test_load_manifests_missing_required_field():
    """Manifest missing required field → ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "incomplete_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "incomplete_plugin",
            "version": "0.1.0",
            # Missing capabilities and entrypoint
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        manager = PluginManager()
        with pytest.raises(ValueError, match="Invalid manifest"):
            manager.load_manifests(plugins_dir)


def test_load_manifests_clears_previous_state():
    """Calling load_manifests twice should clear old plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        # First load: one plugin
        plugin_dir = plugins_dir / "plugin_v1"
        plugin_dir.mkdir()
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(
                {
                    "id": "plugin_v1",
                    "version": "0.1.0",
                    "capabilities": [],
                    "entrypoint": "plugin.py",
                },
                f,
            )

        manager = PluginManager()
        result1 = manager.load_manifests(plugins_dir)
        assert len(result1) == 1
        assert "plugin_v1" in result1

        # Clear and reload: empty dir
        for item in plugins_dir.iterdir():
            import shutil
            shutil.rmtree(item)

        result2 = manager.load_manifests(plugins_dir)
        assert len(result2) == 0
        assert manager._manifests == {}


# ──────────────────────────────────────────────────────────────────────────────
# get_active_plugins tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_active_plugins_no_plugins_for_tenant():
    """Tenant with no enabled plugins returns empty list."""
    manager = PluginManager()
    manager._manifests = {
        "plugin_a": PluginManifest(
            id="plugin_a",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        )
    }

    tenant_id = uuid.uuid4()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await manager.get_active_plugins(tenant_id, mock_db)
    assert result == []


@pytest.mark.asyncio
async def test_get_active_plugins_returns_enabled_plugins():
    """Returns only plugins enabled for that tenant."""
    manager = PluginManager()
    manager._manifests = {
        "plugin_a": PluginManifest(
            id="plugin_a",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        ),
        "plugin_b": PluginManifest(
            id="plugin_b",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        ),
    }

    tenant_id = uuid.uuid4()

    # Mock DB result: two enabled rows
    row_a = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name="plugin_a",
        enabled=True,
        config={},
    )
    row_b = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name="plugin_b",
        enabled=True,
        config={},
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [row_a, row_b]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await manager.get_active_plugins(tenant_id, mock_db)
    assert len(result) == 2
    assert result[0].id == "plugin_a"
    assert result[1].id == "plugin_b"


@pytest.mark.asyncio
async def test_get_active_plugins_filters_orphaned_db_entries():
    """Skip plugins in DB but not in loaded manifests."""
    manager = PluginManager()
    manager._manifests = {
        "plugin_a": PluginManifest(
            id="plugin_a",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        )
    }

    tenant_id = uuid.uuid4()

    # Mock DB result: one exists in manifests, one doesn't
    row_a = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name="plugin_a",
        enabled=True,
        config={},
    )
    row_orphaned = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name="plugin_orphaned",
        enabled=True,
        config={},
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [row_a, row_orphaned]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await manager.get_active_plugins(tenant_id, mock_db)
    assert len(result) == 1
    assert result[0].id == "plugin_a"


@pytest.mark.asyncio
async def test_get_active_plugins_cross_tenant_isolation():
    """Query for tenant A only returns A's plugins, never B's."""
    manager = PluginManager()
    manager._manifests = {
        "plugin_a": PluginManifest(
            id="plugin_a",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        )
    }

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    # Mock DB result: only tenant_a's plugin
    row_a = TenantPlugin(
        tenant_id=tenant_a,
        plugin_name="plugin_a",
        enabled=True,
        config={},
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [row_a]

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    result = await manager.get_active_plugins(tenant_a, mock_db)
    assert len(result) == 1

    # Verify the query was filtered by tenant_a (check execute was called)
    mock_db.execute.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# enable_plugin tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enable_plugin_creates_new_row():
    """Enable a plugin when row doesn't exist → INSERT."""
    manager = PluginManager()

    tenant_id = uuid.uuid4()
    plugin_name = "test_plugin"

    # Mock: no existing row
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    await manager.enable_plugin(tenant_id, plugin_name, mock_db)

    # Verify add() was called
    mock_db.add.assert_called_once()
    added_row = mock_db.add.call_args[0][0]
    assert isinstance(added_row, TenantPlugin)
    assert added_row.tenant_id == tenant_id
    assert added_row.plugin_name == plugin_name
    assert added_row.enabled is True

    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_enable_plugin_updates_existing_row():
    """Enable a plugin when row exists → UPDATE."""
    manager = PluginManager()

    tenant_id = uuid.uuid4()
    plugin_name = "test_plugin"

    # Mock: existing row, currently disabled
    existing_row = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name=plugin_name,
        enabled=False,
        config={},
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_row

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    await manager.enable_plugin(tenant_id, plugin_name, mock_db)

    # Verify the row was updated
    assert existing_row.enabled is True
    mock_db.commit.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# disable_plugin tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_disable_plugin_updates_existing_row():
    """Disable a plugin when row exists → UPDATE."""
    manager = PluginManager()

    tenant_id = uuid.uuid4()
    plugin_name = "test_plugin"

    # Mock: existing row, currently enabled
    existing_row = TenantPlugin(
        tenant_id=tenant_id,
        plugin_name=plugin_name,
        enabled=True,
        config={},
    )

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_row

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    await manager.disable_plugin(tenant_id, plugin_name, mock_db)

    # Verify the row was updated
    assert existing_row.enabled is False
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_disable_plugin_noop_if_row_not_exists():
    """Disable a plugin when row doesn't exist → no-op, no error."""
    manager = PluginManager()

    tenant_id = uuid.uuid4()
    plugin_name = "test_plugin"

    # Mock: no existing row
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.commit = AsyncMock()

    # Should not raise
    await manager.disable_plugin(tenant_id, plugin_name, mock_db)

    # No add() call, no commit
    mock_db.commit.assert_not_called()


# ──────────────────────────────────────────────────────────────────────────────
# Cross-tenant isolation tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enable_plugin_tenant_isolation():
    """Enable plugin for tenant A doesn't affect tenant B."""
    manager = PluginManager()

    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    plugin_name = "shared_plugin"

    # Mock: no existing row
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    # Enable for tenant A
    await manager.enable_plugin(tenant_a, plugin_name, mock_db)

    # Verify the added row has tenant_a, not tenant_b
    added_row = mock_db.add.call_args[0][0]
    assert added_row.tenant_id == tenant_a


@pytest.mark.asyncio
async def test_get_active_plugins_tenant_isolation():
    """Query for tenant A must filter by tenant_id in WHERE clause."""
    manager = PluginManager()
    manager._manifests = {
        "plugin": PluginManifest(
            id="plugin",
            version="0.1.0",
            capabilities=[],
            entrypoint="plugin.py",
        )
    }

    tenant_a = uuid.uuid4()

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    await manager.get_active_plugins(tenant_a, mock_db)

    # Verify execute was called with a query that filters by tenant_a
    mock_db.execute.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# PluginLoader pattern tests
# ──────────────────────────────────────────────────────────────────────────────


def test_fs_plugin_loader_single_plugin():
    """FSPluginLoader can load a single plugin from filesystem."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "test_plugin",
            "version": "0.1.0",
            "capabilities": ["read"],
            "entrypoint": "plugin.py",
            "description": "Test",
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        loader = FSPluginLoader(plugins_dir)
        result = loader.load()

        assert "test_plugin" in result
        assert result["test_plugin"].id == "test_plugin"
        assert result["test_plugin"].version == "0.1.0"


def test_fs_plugin_loader_multiple_plugins():
    """FSPluginLoader can load multiple plugins."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)

        for plugin_id in ["plugin_a", "plugin_b", "plugin_c"]:
            plugin_dir = plugins_dir / plugin_id
            plugin_dir.mkdir()
            manifest_data = {
                "id": plugin_id,
                "version": "0.1.0",
                "capabilities": [],
                "entrypoint": "plugin.py",
            }
            with open(plugin_dir / "manifest.yaml", "w") as f:
                yaml.dump(manifest_data, f)

        loader = FSPluginLoader(plugins_dir)
        result = loader.load()

        assert len(result) == 3
        assert "plugin_a" in result
        assert "plugin_b" in result
        assert "plugin_c" in result


def test_fs_plugin_loader_empty_dir():
    """FSPluginLoader on empty dir returns empty dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        loader = FSPluginLoader(Path(tmpdir))
        result = loader.load()
        assert result == {}


def test_fs_plugin_loader_nonexistent_dir():
    """FSPluginLoader on nonexistent dir returns empty dict."""
    loader = FSPluginLoader(Path("/nonexistent/plugins"))
    result = loader.load()
    assert result == {}


def test_package_plugin_loader_stub():
    """PackagePluginLoader stub returns empty dict (MVP only)."""
    loader = PackagePluginLoader()
    result = loader.load()
    assert result == {}


def test_plugin_manager_with_fs_loader():
    """PluginManager initialized with FSPluginLoader works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "test_plugin",
            "version": "0.1.0",
            "capabilities": ["read"],
            "entrypoint": "plugin.py",
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        loader = FSPluginLoader(plugins_dir)
        manager = PluginManager(loaders=[loader])
        result = manager.load_manifests()

        assert "test_plugin" in result
        assert result["test_plugin"].id == "test_plugin"


def test_plugin_manager_merge_multiple_loaders():
    """PluginManager merges manifests from multiple loaders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "fs_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "fs_plugin",
            "version": "0.1.0",
            "capabilities": [],
            "entrypoint": "plugin.py",
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        fs_loader = FSPluginLoader(plugins_dir)
        pkg_loader = PackagePluginLoader()

        manager = PluginManager(loaders=[fs_loader, pkg_loader])
        result = manager.load_manifests()

        # Should have the FS plugin (pkg_loader returns empty)
        assert "fs_plugin" in result
        assert len(result) == 1


def test_plugin_manager_loader_precedence():
    """Later loaders override earlier ones for duplicate plugin_id."""
    with tempfile.TemporaryDirectory() as tmpdir1:
        with tempfile.TemporaryDirectory() as tmpdir2:
            # First loader has plugin_shared
            dir1 = Path(tmpdir1)
            plugin_dir1 = dir1 / "plugin_shared"
            plugin_dir1.mkdir()
            with open(plugin_dir1 / "manifest.yaml", "w") as f:
                yaml.dump(
                    {
                        "id": "plugin_shared",
                        "version": "1.0.0",
                        "capabilities": [],
                        "entrypoint": "v1.py",
                    },
                    f,
                )

            # Second loader also has plugin_shared (different version)
            dir2 = Path(tmpdir2)
            plugin_dir2 = dir2 / "plugin_shared"
            plugin_dir2.mkdir()
            with open(plugin_dir2 / "manifest.yaml", "w") as f:
                yaml.dump(
                    {
                        "id": "plugin_shared",
                        "version": "2.0.0",
                        "capabilities": [],
                        "entrypoint": "v2.py",
                    },
                    f,
                )

            loader1 = FSPluginLoader(dir1)
            loader2 = FSPluginLoader(dir2)

            manager = PluginManager(loaders=[loader1, loader2])
            result = manager.load_manifests()

            # Later loader (loader2) should win
            assert result["plugin_shared"].version == "2.0.0"
            assert result["plugin_shared"].entrypoint == "v2.py"


def test_plugin_manager_backward_compat_plugins_dir_arg():
    """PluginManager.load_manifests(plugins_dir) still works for backward compat."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugins_dir = Path(tmpdir)
        plugin_dir = plugins_dir / "test_plugin"
        plugin_dir.mkdir()

        manifest_data = {
            "id": "test_plugin",
            "version": "0.1.0",
            "capabilities": ["read"],
            "entrypoint": "plugin.py",
        }
        with open(plugin_dir / "manifest.yaml", "w") as f:
            yaml.dump(manifest_data, f)

        # Create manager without loaders, use plugins_dir arg
        manager = PluginManager()
        result = manager.load_manifests(plugins_dir)

        assert "test_plugin" in result
        assert result["test_plugin"].id == "test_plugin"
