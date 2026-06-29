"""Example demonstrating WebPulse plugin loading and subprocess sandboxing.

Part of Sprint 3 & 4 manual verification.
"""

import asyncio
import shutil
import tempfile
from pathlib import Path

import yaml

from webpulse.core.sandbox import SubprocessSandboxWorker


async def main() -> None:
    # 1. Create a temporary plugin directory
    temp_dir = Path(tempfile.mkdtemp())
    plugin_name = "webpulse-demo-plugin"
    plugin_dir = temp_dir / plugin_name
    plugin_dir.mkdir()

    # 2. Write manifest.yaml
    manifest_data = {
        "name": plugin_name,
        "version": "1.0.0",
        "description": "A demo plugin showing sandbox execution.",
        "category": "security",
        "entry_point": "plugin:DemoPlugin",
        "permissions": {
            "network_access": True,
            "subprocess_exec": False,
        },
    }
    with open(plugin_dir / "manifest.yaml", "w", encoding="utf-8") as f:
        yaml.dump(manifest_data, f)

    # 3. Write plugin.py code
    plugin_code = """from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Finding, Target, Severity
from webpulse.utils.network import AsyncNetworkClient

class DemoPlugin(BasePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="webpulse-demo-plugin", category="security", version="1.0.0")

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        return [
            Finding(
                plugin_name=self.metadata.name,
                category=self.metadata.category,
                target_url=target.url,
                title="SSL Certificate Expiring",
                severity=Severity.HIGH,
                description="Demo finding: Certificate expires in 2 days.",
                remediation="Renew TLS certificate."
            )
        ]
"""
    with open(plugin_dir / "plugin.py", "w", encoding="utf-8") as f:
        f.write(plugin_code)

    print(f"Temporary mock plugin created under: {plugin_dir}")

    # 4. Spawns sandbox worker and execute the plugin
    print("Spawning subprocess sandbox worker...")
    worker = SubprocessSandboxWorker(plugin_dir)
    await worker.start()

    try:
        print("Executing plugin inside sandbox...")
        findings = await worker.execute_plugin("https://example.com", {"option": "val"})

        print("\n=== Scan Findings Received ===")
        for f in findings:
            print(f"ID:          {f.id}")
            print(f"Plugin:      {f.plugin_name}")
            print(f"Title:       {f.title}")
            print(f"Severity:    {f.severity}")
            print(f"Description: {f.description}")
            print(f"Remediation: {f.remediation}")
        print("==============================\n")

    finally:
        # 5. Stop worker and clean up files
        await worker.stop()
        shutil.rmtree(temp_dir)
        print("Sandbox worker stopped and temporary files cleaned.")


if __name__ == "__main__":
    asyncio.run(main())
