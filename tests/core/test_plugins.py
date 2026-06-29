"""Unit tests for the WebPulse Plugin Loader and Sandbox systems."""

from pathlib import Path

import pytest
import yaml

from webpulse.core.exceptions import SecurityException
from webpulse.core.plugin_loader import PluginLoader
from webpulse.core.sandbox import SubprocessSandboxWorker
from webpulse.modules.base import BasePlugin


@pytest.fixture
def create_mock_plugin(tmp_path: Path):
    """Factory fixture to create temporary mock plugin files."""

    def _create(manifest_data: dict, code_content: str) -> Path:
        plugin_dir = tmp_path / manifest_data["name"]
        plugin_dir.mkdir()

        with open(plugin_dir / "manifest.yaml", "w", encoding="utf-8") as f:
            yaml.dump(manifest_data, f)

        # Parse entry point module
        module_name = manifest_data["entry_point"].split(":")[0]
        with open(plugin_dir / f"{module_name}.py", "w", encoding="utf-8") as f:
            f.write(code_content)

        return plugin_dir

    return _create


def test_plugin_load_success(create_mock_plugin) -> None:
    """Verify a valid plugin class imports and validates successfully."""
    manifest = {
        "name": "webpulse-test-plugin",
        "version": "1.0.0",
        "category": "security",
        "entry_point": "my_plugin:MyPlugin",
        "permissions": {"network_access": True, "subprocess_exec": False},
    }
    code = """from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Finding, Target
from webpulse.utils.network import AsyncNetworkClient

class MyPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="webpulse-test-plugin", category="security", version="1.0.0")

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        return []
"""
    plugin_dir = create_mock_plugin(manifest, code)
    loader = PluginLoader()
    plugin_cls = loader.load_plugin(plugin_dir, plugin_dir / "manifest.yaml")

    assert issubclass(plugin_cls, BasePlugin)
    instance = plugin_cls()
    assert instance.metadata.name == "webpulse-test-plugin"


def test_ast_forbidden_subprocess_import(create_mock_plugin) -> None:
    """Verify AST block checks catch unauthorized subprocess imports."""
    manifest = {
        "name": "webpulse-blocked-plugin",
        "version": "1.0.0",
        "category": "security",
        "entry_point": "bad_plugin:BadPlugin",
        "permissions": {"subprocess_exec": False},  # Subprocess disabled
    }
    code = """import subprocess
from webpulse.modules.base import BasePlugin

class BadPlugin(BasePlugin):
    pass
"""
    plugin_dir = create_mock_plugin(manifest, code)
    loader = PluginLoader()

    with pytest.raises(SecurityException) as exc_info:
        loader.load_plugin(plugin_dir, plugin_dir / "manifest.yaml")

    assert "subprocess_exec permissions" in str(exc_info.value)


def test_ast_forbidden_os_system_call(create_mock_plugin) -> None:
    """Verify AST block checks catch unauthorized os.system usage."""
    manifest = {
        "name": "webpulse-blocked-os-plugin",
        "version": "1.0.0",
        "category": "security",
        "entry_point": "bad_plugin:BadPlugin",
        "permissions": {"subprocess_exec": False},
    }
    code = """import os
from webpulse.modules.base import BasePlugin

class BadPlugin(BasePlugin):
    def run_bad(self):
        os.system("whoami")
"""
    plugin_dir = create_mock_plugin(manifest, code)
    loader = PluginLoader()

    with pytest.raises(SecurityException) as exc_info:
        loader.load_plugin(plugin_dir, plugin_dir / "manifest.yaml")

    assert "subprocess_exec permissions" in str(exc_info.value)


def test_ast_forbidden_network_import(create_mock_plugin) -> None:
    """Verify AST block checks catch unauthorized socket imports."""
    manifest = {
        "name": "webpulse-no-net-plugin",
        "version": "1.0.0",
        "category": "seo",
        "entry_point": "net_plugin:NetPlugin",
        "permissions": {"network_access": False},  # Network disabled
    }
    code = """import socket
from webpulse.modules.base import BasePlugin

class NetPlugin(BasePlugin):
    pass
"""
    plugin_dir = create_mock_plugin(manifest, code)
    loader = PluginLoader()

    with pytest.raises(SecurityException) as exc_info:
        loader.load_plugin(plugin_dir, plugin_dir / "manifest.yaml")

    assert "network_access permissions" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sandbox_worker_execution(create_mock_plugin) -> None:
    """Verify that SubprocessSandboxWorker executes a mock plugin correctly over JSON-RPC."""
    manifest = {
        "name": "webpulse-sandbox-plugin",
        "version": "1.0.0",
        "category": "security",
        "entry_point": "plugin:SandboxPlugin",
        "permissions": {"network_access": True, "subprocess_exec": False},
    }
    code = """from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Finding, Target, Severity
from webpulse.utils.network import AsyncNetworkClient

class SandboxPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="webpulse-sandbox-plugin", category="security", version="1.0.0")

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        return [
            Finding(
                plugin_name=self.metadata.name,
                category=self.metadata.category,
                target_url=target.url,
                title="Mock Vulnerability",
                severity=Severity.HIGH,
                description="Found a vulnerability.",
                remediation="Apply remediation steps."
            )
        ]
"""
    plugin_dir = create_mock_plugin(manifest, code)
    worker = SubprocessSandboxWorker(plugin_dir)

    await worker.start()
    try:
        findings = await worker.execute_plugin("https://example.com", {"option": "val"})
        assert len(findings) == 1
        assert findings[0].title == "Mock Vulnerability"
        assert findings[0].severity == "HIGH"
        assert findings[0].target_url == "https://example.com"
    finally:
        await worker.stop()
