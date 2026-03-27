"""
Plugin Loaders — abstraction for discovering plugins from different sources.

Supports multiple loader implementations (filesystem, packages, etc.).
PluginManager can be initialized with a list of loaders to search for plugins.
"""

from pathlib import Path
from typing import Protocol
import yaml

from app.plugins.manager import PluginManifest


class PluginLoader(Protocol):
    """Protocol for plugin loaders. Implementations discover and load plugin manifests."""

    def load(self) -> dict[str, PluginManifest]:
        """
        Load and return plugin manifests from this source.

        Returns:
            dict[plugin_id -> PluginManifest]
        """
        ...


class FSPluginLoader:
    """
    Load plugins from filesystem.

    Scans plugins_dir/*/manifest.yaml and loads each manifest into a PluginManifest.
    Raises ValueError on malformed manifests.

    Usage:
        loader = FSPluginLoader(Path("./plugins"))
        manifests = loader.load()
    """

    def __init__(self, plugins_dir: Path):
        """
        Initialize loader with a plugins directory.

        Args:
            plugins_dir: Path to the plugins directory containing plugin subdirectories.
        """
        self.plugins_dir = plugins_dir

    def load(self) -> dict[str, PluginManifest]:
        """
        Scan plugins_dir/*/manifest.yaml and load into memory.

        Each manifest must have: id, version, capabilities (list), entrypoint.
        Raises ValueError on malformed manifest.

        Returns:
            dict[plugin_id -> PluginManifest]
        """
        manifests: dict[str, PluginManifest] = {}

        if not self.plugins_dir.exists():
            # If plugins dir doesn't exist, return empty. No error.
            return {}

        for plugin_subdir in self.plugins_dir.iterdir():
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
                manifests[manifest.id] = manifest

            except yaml.YAMLError as e:
                raise ValueError(
                    f"Invalid YAML in {manifest_path}: {e}"
                ) from e
            except ValueError as e:
                raise ValueError(
                    f"Invalid manifest in {manifest_path}: {e}"
                ) from e

        return manifests


class PackagePluginLoader:
    """
    Load plugins from installed Python packages.

    Future implementation: discovers plugins via importlib.metadata.entry_points()
    with group="ai_platform.plugins".

    Not implemented in MVP. Returns empty dict to maintain protocol compliance.

    Usage (future):
        loader = PackagePluginLoader()
        manifests = loader.load()  # Currently returns {}
    """

    def load(self) -> dict[str, PluginManifest]:
        """
        Load plugins from installed packages.

        MVP: stub only. Always returns empty dict.

        Returns:
            dict[plugin_id -> PluginManifest]
        """
        # TODO: Future implementation via importlib.metadata.entry_points()
        return {}
