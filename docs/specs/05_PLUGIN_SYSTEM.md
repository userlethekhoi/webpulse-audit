# 05_PLUGIN_SYSTEM.md — WebPulse Plugin System Specification (v2.0)

## 1. Purpose
This document defines the architecture, manifest schemas, security models, execution lifecycles, and compatibility rules for the WebPulse Plugin Framework. It provides developers and AI agents with the exact specifications required to write, load, and run third-party plugins safely.

---

## 2. Overview
WebPulse is built on a plugin-first philosophy. All audit modules (built-in and external) are managed by a centralized `PluginLoader` that discovers, verifies, and schedules execution. To ensure security and environment stability, the framework supports subprocess sandboxing, AST import inspection, and isolated virtualenv execution contexts.

---

## 3. Plugin Lifecycle

A plugin traverses the following states during a WebPulse scan session:

```
[Discovery] ──► [Validation] ──► [Resolution] ──► [Instantiation] ──► [Execution] ──► [Teardown]
```

1. **Discovery:** The loader scans configured directories for Python modules containing a `manifest.yaml` file.
2. **Validation:** Manifest formats, schema declarations, and signature hashes are verified. Static AST parsing checks declared imports.
3. **Resolution:** Plugin-to-plugin and system package dependencies are verified. Plugins with conflicting dependencies are allocated to isolated Python virtualenv worker contexts.
4. **Instantiation:** The scheduler initializes the plugin, calling `on_load(config)`. If sandboxed, the loader spawns a subprocess worker and transmits the configuration.
5. **Execution:** The async `execute()` method is scheduled inside the event loop (or run via JSON-RPC inside the sandbox worker).
6. **Teardown:** System resources are freed by executing the `on_unload()` hook.

---

## 4. Manifest Schema (`manifest.yaml`)

Every plugin must supply a `manifest.yaml` in its root folder.

```yaml
name: "webpulse-http2-downgrade-check"
version: "1.2.0"
description: "Checks if the server allows unsafe downgrades from HTTP/2 to HTTP/1.1."
author: "Security Team <secops@example.com>"
license: "MIT"
category: "security"
priority: 50             # Execution priority (1 = highest, 100 = lowest)
entry_point: "plugin:Http2DowngradePlugin"

compatibility:
  webpulse_version: ">=2.0.0, <3.0.0"
  python_version: ">=3.11"

dependencies:
  system_packages: []
  pip_packages:
    - "h2>=4.1.0"
  required_plugins:
    - "webpulse-http-analyzer"

permissions:
  network_access: true
  filesystem_read: false
  filesystem_write: false
  subprocess_exec: false
```

---

## 5. Plugin Security & Sandbox Model

WebPulse enforces a permission-based verification system during the loading phase.

### 5.1 Static AST Import Verification
Prior to running `importlib.import_module()`, the `PluginLoader` reads the imports inside the plugin's code files using Python's static abstract syntax tree (`ast`) parsing.
* If a plugin does not declare `subprocess_exec: true` in its manifest, but contains imports of `subprocess`, `os.system`, `os.popen`, or `shutil`, the loader rejects the plugin and raises a `SecurityException`.
* If `network_access: false` is set in the manifest, but socket imports are detected, the plugin loading fails.

### 5.2 Subprocess Sandboxing & JSON-RPC Protocol
By default, all third-party plugins are loaded into an isolated subprocess sandbox.
* The main engine spawns a worker process using a minimal Python wrapper: `python -m webpulse.core.sandbox_worker <plugin_path>`.
* Communication occurs over standard input/output (`stdin`/`stdout`) using a standard JSON-RPC 2.0 protocol:

#### 5.2.1 Initialization Request:
```json
{
  "jsonrpc": "2.0",
  "method": "on_load",
  "params": {
    "config": { "custom_option": "value" }
  },
  "id": 1
}
```

#### 5.2.2 Execution Request:
```json
{
  "jsonrpc": "2.0",
  "method": "execute",
  "params": {
    "target": { "url": "https://example.com", "ip_address": "93.184.216.34" }
  },
  "id": 2
}
```

#### 5.2.3 Response Output:
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "id": "abc-123",
      "plugin_name": "webpulse-http2-downgrade-check",
      "category": "security",
      "title": "Insecure HTTP/2 Downgrade Allowed",
      "severity": "MEDIUM",
      "confidence": 1.0,
      "description": "Server permits protocol downgrades.",
      "remediation": "Enforce HTTP/2 constraints.",
      "evidence": []
    }
  ],
  "id": 2
}
```

---

## 6. Dependency Conflict Isolation (Virtualenv Mode)
If two plugins specify conflicting package dependencies:
1. The `PluginLoader` compiles a hash of the required packages in the manifest.
2. If conflicts are resolved, a local virtual environment is created under `~/.webpulse/envs/<plugin_hash>/`.
3. The sandbox worker is spawned using the virtual environment's python binary (`~/.webpulse/envs/<plugin_hash>/bin/python`), preserving isolation.

---

## 7. Plugin Development Guide

Below is the standard interface template class all plugin writers must implement:

```python
# plugin.py
from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient

class Http2DowngradePlugin(BasePlugin):
    async def on_load(self, config: dict):
        """Plugin configuration and validation initialization."""
        self.config = config

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-http2-downgrade-check",
            category="security",
            version="2.0.0"
        )

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        findings = []
        # Custom check logic goes here
        return findings

    async def on_unload(self):
        """Cleanup sockets and context objects."""
        pass
```

---

## 8. Design Decisions
* **Decision:** We use standard YAML manifests rather than custom python decorators for configuration parameters and permissions.
* **Rationale:** A manifest file can be parsed statically without executing any Python code, allowing the framework to audit plugin security safety profiles before loading them into memory.

---

## 9. References
* Python `importlib` documentation: https://docs.python.org/3/library/importlib.html
* Python `ast` module reference: https://docs.python.org/3/library/ast.html
* JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification

---

## 10. Validation Rules
* Every manifest must supply `name`, `version`, `entry_point`, and `compatibility`.
* Major versions of WebPulse will reject plugins compiled for older major releases unless matching compatibility is declared.

---

## 11. Engineering Notes
* If a plugin execution fails, the scheduler must catch the exception, log the traceback in debug level, format a warning finding inside the report, and release execution resources.

---

## 12. AI Notes
* Do not import modules outside the standard library or specified in the manifest dependencies.
* Never use deprecated class methods inside plugins.
