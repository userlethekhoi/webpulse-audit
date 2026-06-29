# 08_CLI_REFERENCE.md — WebPulse CLI Reference (v2.0)

## 1. Purpose
This document provides the reference specification for the WebPulse command-line interface (CLI). It details command names, parameters, execution modes, exit codes, and output controls, serving as the interface contract for developers, scripts, and CI/CD wrappers.

---

## 2. Overview
WebPulse is controlled via a unified console executable (`webpulse`). The CLI is designed to support direct ad-hoc scanning by developers, batch execution via configuration files, and seamless automation in headless pipeline environments.

---

## 3. Command Hierarchy

```
webpulse
 ├── scan <target_url> [options]
 ├── plugins
 │    ├── list
 │    ├── info <plugin_name>
 │    └── validate <plugin_path>
 └── config
      ├── show
      ├── set <key> <value>
      └── validate
```

---

## 4. Commands & Arguments Reference

### 4.1 Global Options
These flags are applicable across all subcommands:
* `-h, --help`: Show detailed usage information and exit.
* `-v, --verbose`: Increase output logging verbosity (can be specified multiple times: `-v` for info, `-vv` for debug).
* `--debug`: Enable full traceback prints and turn off error interception.
* `--no-color`: Disable all ANSI colors in console output (matches the `NO_COLOR` spec).

### 4.2 The `scan` Subcommand
Audits a target URL or host.
* **Usage:** `webpulse scan <target_url> [options]`
* **Arguments:**
  * `<target_url>` (Required): The target domain or URL to audit.

* **Scan Options:**
  * `-o, --output <path>`: Write the audit report to the specified file path.
  * `-f, --format <format>`: Report format type. Options: `console`, `json`, `html`, `markdown`. Multiple formats can be comma-separated (e.g. `-f json,html`). Default: `console`.
  * `-p, --profile <profile_name>`: Load a predefined scan profile (e.g. `fast`, `default`, `full`).
  * `-r, --rate-limit <rps>`: Limit maximum requests per second. Default: `10`.
  * `-c, --concurrency <limit>`: Limit maximum concurrent connections. Default: `25`.
  * `--timeout <seconds>`: Global connection timeout. Default: `10`.
  * `--use-browser`: Launch headless browser (Playwright) to audit performance and accessibility vectors.
  * `--yes-i-have-authorization`: Explicit confirmation required to run the Stress Testing Module.

* **Crawler & Authentication Options (v2.0):**
  * `--crawl`: Enable BFS crawling to scan discovered internal page URLs.
  * `--max-depth <depth>`: Maximum crawler BFS recursion depth. Default: `2`.
  * `--max-pages <limit>`: Maximum count of page targets visited. Default: `10`.
  * `--auth-config <path>`: Path to a YAML/JSON file containing session credentials or login form targets.
  * `--allow-private-ips`: Bypass default SSRF blocking rules. Allows scans to run on internal hosts (RFC 1918 / 6890).
  * `--sandbox-plugins <bool>`: Toggle sandbox subprocess execution for third-party plugins. Default: `true` (Enabled).

### 4.3 The `plugins` Subcommand
* **`plugins list`**: List all discovered plugins and their active states.
* **`plugins info <plugin_name>`**: Display detailed manifest properties for a plugin.
* **`plugins validate <plugin_path>`**: Run manifest and AST checks on a local plugin package directory.

### 4.4 The `config` Subcommand
* **`config show`**: Print current merged configuration parameters.
* **`config set <key> <value>`**: Update a user global configuration parameter in `~/.webpulse/config.yaml`.
* **`config validate`**: Run schema validations on the current active configuration file.

---

## 5. Exit Codes

WebPulse uses standardized exit codes to allow integration in automation pipelines:

| Exit Code | Classification | Condition |
|---|---|---|
| **0** | SUCCESS | Scan completed successfully; no warning thresholds were exceeded. |
| **1** | SYSTEM_ERROR | General execution error (e.g., config error, missing dependencies, DNS lookup failed). |
| **2** | THRESHOLD_EXCEEDED | Scan completed, but the overall health score fell below the configured warning threshold (e.g. `--fail-on-health 80`). |
| **3** | SECURITY_CRITICAL | Scan completed, and at least one Critical severity security finding was discovered (with `--fail-on-critical`). |
| **130** | CANCELED | Execution terminated by user interrupt (SIGINT / Ctrl+C). |

---

## 6. CLI Execution Modes

### 6.1 Batch Mode (Headless CI/CD)
Designed for runners. Suppresses interactive progress bars and outputs clean, machine-parsable logs:
```bash
webpulse scan https://example.com -f json -o dist/report.json -vv --no-color --crawl --auth-config config/auth.json
```

### 6.2 Interactive Mode
For local terminal audits. Employs a dynamic progress bar showcasing active tasks, request rate counters, and live severity findings counters.

---

## 7. Design Decisions
* **Decision:** CLI implementation uses `argparse` from the Python standard library instead of external frameworks like `Click` or `Typer`.
* **Rationale:** Reduces core package dependency chains and guarantees compatibility with minimal environments.

---

## 8. Future REST API Compatibility
The CLI arguments map 1-to-1 with a future REST API request payload (e.g. `/api/v1/scan` POST requests). This ensures WebPulse can be converted into a microservice worker easily in the future.

---

## 9. References
* POSIX CLI conventions: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html
* NO_COLOR standard reference: https://no-color.org/

---

## 10. Validation Rules
* Any new flag added to the CLI must be declared inside the `webpulse.cli.cli_args` parsing definition.
* Subcommands must return one of the integers defined in Section 5.

---

## 11. Engineering Notes
* When rendering terminal colors, check if `stdout.isatty()` is True and verify `--no-color` has not been set before outputting ANSI sequences.

---

## 12. AI Notes
* Do not import third-party click modules in CLI scripts. Use the custom CLIEntry wrapping mechanism built on argparse.
