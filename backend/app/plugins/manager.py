"""
Plugin Manager — load manifest YAML, manage tenant plugin state, ensure isolation.

No external calls, no DB session creation. All DB operations passed in from caller.
"""

import uuid
from pathlib import Path
from pydantic import BaseModel, ConfigDict
import yaml


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
    """

    def __init__(self):
        self._manifests: dict[str, PluginManifest] = {}

    def load_manifests(self, plugins_dir: Path) -> dict[str, PluginManifest]:
        """
        Scan plugins_dir/*/manifest.yaml and load into memory.

        Each manifest must have: id, version, capabilities (list), entrypoint.
        Raises ValueError on malformed manifest.

        Returns:
            dict[plugin_id -> PluginManifest]
        """
        self._manifests.clear()

        if not plugins_dir.exists():
            # If plugins dir doesn't exist, return empty. No error.
            return {}

        for plugin_subdir in plugins_dir.iterdir():
            if not plugin_subdir.is_dir():
                continue

            manifest_path = plugin_subdir / "manifest.yaml"
            if not manifest_path.exists():
                # Skip subdirs without manifest.yaml
                continue

            try:
                with open(manifest_path, "r") as f:
                    data = yaml.safe_load(f)

                if data is None:
                    raise ValueError(f"Manifest is empty: {manifest_path}")

                # Pydantic validation will catch missing fields
                manifest = PluginManifest(**data)
                self._manifests[manifest.id] = manifest

            except yaml.YAMLError as e:
                raise ValueError(
                    f"Invalid YAML in {manifest_path}: {e}"
                ) from e
            except ValueError as e:
                raise ValueError(
                    f"Invalid manifest in {manifest_path}: {e}"
                ) from e

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
