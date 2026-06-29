"""Plugin discovery and dynamic loading system for WebPulse.

Inspects plugin directories, parses manifests, performs AST safety checks,
and imports plugin classes.
"""

import ast
import importlib.util
import logging
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from webpulse.core.exceptions import PluginException, SecurityException
from webpulse.modules.base import BasePlugin

logger = logging.getLogger("webpulse.core.plugin_loader")


class CompatibilityConfig(BaseModel):
    """Compatibility settings for plugins."""

    webpulse_version: str = Field(default=">=2.0.0, <3.0.0")
    python_version: str | None = Field(default=None)


class DependencyConfig(BaseModel):
    """Dependency listings for plugins."""

    system_packages: list[str] = Field(default_factory=list)
    pip_packages: list[str] = Field(default_factory=list)
    required_plugins: list[str] = Field(default_factory=list)


class PermissionConfig(BaseModel):
    """Permission declarations in plugin manifests."""

    network_access: bool = Field(default=True)
    filesystem_read: bool = Field(default=False)
    filesystem_write: bool = Field(default=False)
    subprocess_exec: bool = Field(default=False)


class PluginManifest(BaseModel):
    """Validated schema for a plugin's manifest.yaml."""

    name: str = Field(..., description="Plugin unique ID name.")
    version: str = Field(..., description="Semantic version string.")
    description: str = Field(default="")
    author: str = Field(default="")
    license: str = Field(default="")
    category: str = Field(..., description="E.g. security, seo, performance.")
    priority: int = Field(default=50, ge=1, le=100)
    entry_point: str = Field(..., description="Format: 'module:ClassName'")
    compatibility: CompatibilityConfig = Field(default_factory=CompatibilityConfig)
    dependencies: DependencyConfig = Field(default_factory=DependencyConfig)
    permissions: PermissionConfig = Field(default_factory=PermissionConfig)


class PluginLoader:
    """Manages the discovery, AST-verification, and loading of plugins."""

    def __init__(self) -> None:
        """Initialize the PluginLoader."""
        # Maps plugin names to loaded manifests for permission auditing
        self.manifests: dict[str, PluginManifest] = {}

    def discover_plugins(self, search_paths: list[Path]) -> list[type[BasePlugin]]:
        """Walk search paths to find directories containing valid plugins and load them.

        Args:
            search_paths: List of directories to search.

        Returns:
            List of successfully loaded BasePlugin class types.
        """
        loaded_classes: list[type[BasePlugin]] = []

        for base_path in search_paths:
            if not base_path.exists() or not base_path.is_dir():
                logger.debug(f"Search path '{base_path}' does not exist or is not a directory.")
                continue

            for plugin_dir in base_path.iterdir():
                if plugin_dir.is_dir():
                    manifest_path = plugin_dir / "manifest.yaml"
                    if not manifest_path.exists():
                        # Support .yml fallback
                        manifest_path = plugin_dir / "manifest.yml"

                    if manifest_path.exists():
                        try:
                            logger.info(f"Discovering plugin in folder: {plugin_dir}")
                            plugin_cls = self.load_plugin(plugin_dir, manifest_path)
                            loaded_classes.append(plugin_cls)
                        except Exception as e:
                            logger.error(f"Failed to load plugin from '{plugin_dir}': {e}")

        return loaded_classes

    def load_plugin(self, plugin_dir: Path, manifest_path: Path) -> type[BasePlugin]:
        """Parse manifest, execute AST verification, and load the plugin class.

        Args:
            plugin_dir: Path to the plugin directory.
            manifest_path: Path to the manifest.yaml file.

        Returns:
            The imported BasePlugin class.

        Raises:
            PluginException: For validation or import failures.
            SecurityException: For AST validation permission violations.
        """
        # 1. Parse and validate manifest
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest_dict = yaml.safe_load(f)
            manifest = PluginManifest.model_validate(manifest_dict)
        except Exception as e:
            raise PluginException(f"Invalid manifest.yaml structure: {e}") from e

        self.manifests[manifest.name] = manifest

        # 2. Extract entry point parts
        if ":" not in manifest.entry_point:
            raise PluginException(
                f"Invalid entry_point '{manifest.entry_point}' "
                "(expected format 'module:ClassName')."
            )
        module_name, class_name = manifest.entry_point.split(":", 1)
        entry_file = plugin_dir / f"{module_name}.py"
        if not entry_file.exists():
            raise PluginException(f"Entry point file not found: '{entry_file}'")

        # 3. Perform static AST security audits on all .py files in plugin_dir
        for py_file in plugin_dir.glob("**/*.py"):
            self._verify_ast_imports(py_file, manifest.permissions)

        # 4. Import the module dynamically
        try:
            # Use unique namespace to avoid collisions
            unique_module_name = f"webpulse.plugins._dynamic.{manifest.name}"
            spec = importlib.util.spec_from_file_location(unique_module_name, entry_file)
            if not spec or not spec.loader:
                raise PluginException(f"Failed to create module spec for '{entry_file}'")

            module = importlib.util.module_from_spec(spec)
            sys.modules[unique_module_name] = module
            spec.loader.exec_module(module)
        except SecurityException:
            raise
        except Exception as e:
            raise PluginException(f"Failed to import plugin module '{entry_file}': {e}") from e

        # 5. Extract and validate plugin class
        if not hasattr(module, class_name):
            raise PluginException(f"Class '{class_name}' not found inside module '{module_name}'")

        plugin_cls = getattr(module, class_name)
        if not isinstance(plugin_cls, type) or not issubclass(plugin_cls, BasePlugin):
            raise PluginException(f"Class '{class_name}' must subclass BasePlugin.")

        logger.info(f"Loaded plugin '{manifest.name}' successfully.")
        return plugin_cls

    def _verify_ast_imports(self, file_path: Path, permissions: PermissionConfig) -> None:
        """Inspect all imports statically using an Abstract Syntax Tree (AST).

        Args:
            file_path: The Python script to audit.
            permissions: Allowed actions configuration.

        Raises:
            SecurityException: If forbidden imports or calls are detected.
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(file_path))
        except Exception as e:
            raise PluginException(f"Failed to parse AST for '{file_path}': {e}") from e

        for node in ast.walk(tree):
            # Check normal imports (e.g. import subprocess)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    self._check_forbidden_package(root_pkg, file_path, permissions)

            # Check from-imports (e.g. from subprocess import Popen)
            elif isinstance(node, ast.ImportFrom) and node.module:
                root_pkg = node.module.split(".")[0]
                self._check_forbidden_package(root_pkg, file_path, permissions)

            # Check direct attribute usage on aliases or modules (e.g. os.system)
            elif (
                isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == "os"
                and node.attr in ("system", "popen", "spawn")
                and not permissions.subprocess_exec
            ):
                raise SecurityException(
                    f"Plugin code '{file_path}' calls forbidden attribute 'os.{node.attr}' "
                    f"without subprocess_exec permissions."
                )

    def _check_forbidden_package(
        self, pkg_name: str, file_path: Path, permissions: PermissionConfig
    ) -> None:
        """Helper to verify if a package import is allowed under configured permissions."""
        if not permissions.subprocess_exec and pkg_name in ("subprocess", "shutil"):
            raise SecurityException(
                f"Plugin code '{file_path}' imports forbidden package '{pkg_name}' "
                f"without subprocess_exec permissions."
            )

        if not permissions.network_access and pkg_name in (
            "socket",
            "httpx",
            "http",
            "urllib",
            "requests",
        ):
            raise SecurityException(
                f"Plugin code '{file_path}' imports forbidden package '{pkg_name}' "
                f"without network_access permissions."
            )
