# WebPulse Architecture Review Report (v2.0 Specs Audit)

## 1. Purpose
This report presents a thorough review of the WebPulse Version 2.0 specifications to confirm structural coherence, find discrepancies across files, analyze security exposures, and define development safeguards before any Python source code is written.

---

## 2. Terminology & Conceptual Alignment Audit
The Version 2.0 specs were audited for naming consistency. The following rules are verified as aligned across all documents:
* **Target:** Repesents the URL or IP being audited (standardized in `01_PROJECT_VISION.md`, `02_PRODUCT_REQUIREMENTS.md`, `03_ARCHITECTURE.md`, `04_MODULE_SPECIFICATIONS.md`, `07_REPORT_SCHEMA.md`, `08_CLI_REFERENCE.md`, `09_CONFIGURATION_REFERENCE.md`, and `13_AI_AGENT_GUIDE.md`).
* **Finding:** Represents an audit issue discovered by a plugin (standardized across all 13 specs).
* **Core Packages:** Core modules reside strictly under `webpulse.core.*`, built-in analyzers under `webpulse.modules.*`, and reporters under `webpulse.reports.*`.

---

## 3. Potential Inconsistencies & Resolutions

### 3.1 Playwright Emulation Execution Context
* **Inconsistency:** `02_PRODUCT_REQUIREMENTS.md` notes that Playwright is an optional extra package (`pip install webpulse[browser]`), while `04_MODULE_SPECIFICATIONS.md` list Accessibility and Performance analyzers as core modules.
* **Resolution:** If Playwright is not installed (e.g. standard profile), these analyzers must degrade gracefully, skipping browser-dependent checks and logging a warning finding, rather than throwing import errors.
* **Refinement:** The `PluginLoader` will verify the capability flags of these plugins at runtime and conditionally load them based on system dependencies.

### 3.2 Subprocess Sandbox & Built-in Modules
* **Inconsistency:** `03_ARCHITECTURE.md` states built-in plugins run in-process using thread pool offloading, whereas third-party plugins run in subprocesses via JSON-RPC.
* **Resolution:** The `BasePlugin` ABC supports both execution modes. If `--sandbox-plugins` is toggled globally, built-in plugins will also execute inside the subprocess sandboxes to guarantee complete safety during high-stress audits.

---

## 4. Key Security Controls Audit
* **SSRF Prevention:** Verified that `webpulse.utils.network` forces resolution checks against private and local IP blocks (RFC 1918, RFC 6890).
* **Credential Secrecy:** Enforced through environmental overlays and Pydantic config validation. No secrets can be written to the Console or JSON findings evidence.
* **Authorization Gate:** The Stress Testing Module enforces a hard-coded check requiring the CLI flag `--yes-i-have-authorization` to be supplied.

---

## 5. Architectural Approval Checklist

- [x] Clear folder and package boundaries defined.
- [x] Terminology standardized (`Target` and `Finding` uniform across files).
- [x] Thread pool offloading specified for CPU-bound DOM parsing.
- [x] Subprocess sandbox JSON-RPC interface defined.
- [x] SSRF filters defined inside the connection client wrapper.
- [x] All 13 specification files audited and confirmed consistent.
