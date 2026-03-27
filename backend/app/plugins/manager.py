"""
Plugin Manager — load manifest YAML, manage tenant plugin state, ensure isolation.

No external calls, no DB session creation. All DB operations passed in from caller.
"""

import uuid
from pathlib import Path
from pydantic import BaseModel, ConfigDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.plugins.loaders import PluginLoader


class PluginManifest(BaseModel):
    """Plugin metadata from manifest.yaml"""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    capabilities: list[str]
    entrypoint: str
    description: str = ""


class PluginManager:
    """
    Manages plugin lifecycle at runtime.

    State: _manifests dict loaded once at init. Get active plugins per tenant from DB.
    Can be initialized with a list of PluginLoaders to search multiple sources.
    """

    def __init__(self, loaders: list["PluginLoader"] | None = None):
        """
        Initialize PluginManager with optional loaders.

        Args:
            loaders: Optional list of PluginLoader instances. If None, no loaders
                     are registered. Call load_manifests() without arguments to use
                     registered loaders, or pass a single FSPluginLoader for
                     backward compatibility.
        """
        self._loaders = loaders or []
        self._manifests: dict[str, PluginManifest] = {}

    def load_manifests(
        self, plugins_dir: Path | None = None
    ) -> dict[str, PluginManifest]:
        """
        Load manifests from registered loaders or filesystem.

        Args:
            plugins_dir: Optional Path for backward compatibility. If provided,
                         creates a temporary FSPluginLoader for this directory.
                         If None, uses loaders registered in __init__.

        Precedence on duplicate plugin_id: loaders are processed in order,
        later loaders override earlier ones. For filesystem precedence over packages,
        register FSPluginLoader last.

        Returns:
            dict[plugin_id -> PluginManifest]
        """
        self._manifests.clear()

        # Handle backward compatibility: plugins_dir argument
        loaders_to_use = self._loaders
        if plugins_dir is not None:
            from app.plugins.loaders import FSPluginLoader

            loaders_to_use = [FSPluginLoader(plugins_dir)]

        # Load from all loaders and merge
        for loader in loaders_to_use:
            loader_manifests = loader.load()
            self._manifests.update(loader_manifests)

        return self._manifests

    async def get_active_plugins(
        self, tenant_id: uuid.UUID, db
    ) -> list[PluginManifest]:
        """
        Query DB for active plugins of this tenant.

        Filters tenant_plugins where tenant_id=X and enabled=True.
        Only returns manifests that were loaded on disk (skip orphaned DB records).

        Returns:
            List of PluginManifest for enabled plugins
        """
        from sqlalchemy import select
        from app.db.models.tenant import TenantPlugin

        stmt = select(TenantPlugin).where(
            TenantPlugin.tenant_id == tenant_id,
            TenantPlugin.enabled == True,
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()

        # Only return plugins that exist in loaded manifests
        manifests = []
        for row in rows:
            if row.plugin_name in self._manifests:
                manifests.append(self._manifests[row.plugin_name])

        return manifests

    async def enable_plugin(
        self, tenant_id: uuid.UUID, plugin_name: str, db
    ) -> None:
        """
        Enable a plugin for a tenant.

        If row exists → UPDATE enabled=True
        If row doesn't exist → INSERT enabled=True

        Does not validate that plugin_name exists in manifests.
        """
        from sqlalchemy import select
        from app.db.models.tenant import TenantPlugin

        stmt = select(TenantPlugin).where(
            TenantPlugin.tenant_id == tenant_id,
            TenantPlugin.plugin_name == plugin_name,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.enabled = True
        else:
            row = TenantPlugin(
                tenant_id=tenant_id,
                plugin_name=plugin_name,
                enabled=True,
                config={},
            )
            db.add(row)

        await db.commit()

    async def disable_plugin(
        self, tenant_id: uuid.UUID, plugin_name: str, db
    ) -> None:
        """
        Disable a plugin for a tenant.

        If row exists → UPDATE enabled=False
        If row doesn't exist → no-op (not an error)
        """
        from sqlalchemy import select
        from app.db.models.tenant import TenantPlugin

        stmt = select(TenantPlugin).where(
            TenantPlugin.tenant_id == tenant_id,
            TenantPlugin.plugin_name == plugin_name,
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()

        if row:
            row.enabled = False
            await db.commit()
