# WebPulse Implementation Roadmap & Sprint Plan

## 1. Purpose
This document outlines the phased development roadmap for the WebPulse framework, dividing the implementation process into manageable, reviewable Sprints. Each Sprint defines goals, files, dependencies, and acceptance criteria.

---

## 2. Overview of Sprints

```
[Sprint 1: Core Foundation] ──► [Sprint 2: SSRF Network Client] ──► [Sprint 3: BFS Crawler & Auth]
                                                                               │
[Sprint 6: Core Analyzers]   ◄── [Sprint 5: Subprocess Sandbox]  ◄── [Sprint 4: Plugin Loader ABCs]
         │
[Sprint 7: Scoring & Reporting] ──► [Sprint 8: CLI Integration] ──► [v1.0.0 Stable Release]
```

---

## 3. Detailed Sprint Specifications

### Sprint 1: Core Foundation & Configuration Engine
* **Goal:** Set up the package structure, baseline configurations, exceptions, and logging controls.
* **Files:**
  - `src/webpulse/__init__.py`
  - `src/webpulse/core/__init__.py`
  - `src/webpulse/core/exceptions.py`
  - `src/webpulse/core/config.py` (Pydantic-based settings)
  - `src/webpulse/core/di.py` (Dependency injection container)
  - `src/webpulse/utils/__init__.py`
  - `src/webpulse/utils/logging.py`
* **Dependencies:** `pydantic` v2, `pyyaml`.
* **Acceptance Criteria:**
  - Able to load configurations from YAML/JSON/TOML.
  - Successfully merges environment variables.
  - Core DI container initializes config singletons.
* **Complexity:** Low.

### Sprint 2: Async Network Client & SSRF Filters
* **Goal:** Implement the async network request client with integrated SSRF IP filters.
* **Files:**
  - `src/webpulse/utils/network.py`
* **Dependencies:** `httpx`, `cryptography` (for TLS handshake parameters).
* **Acceptance Criteria:**
  - outbound requests to loopback or private ranges (RFC 1918 / 6890) fail by default.
  - `--allow-private-ips` bypasses SSRF filters.
  - DNS resolution occurs asynchronously.
* **Complexity:** Medium.

### Sprint 3: BFS Crawler & Auth Coordinator
* **Goal:** Build the async crawler queue and session manager.
* **Files:**
  - `src/webpulse/core/crawler.py`
  - `src/webpulse/core/auth.py`
* **Dependencies:** `beautifulsoup4`, `httpx`.
* **Acceptance Criteria:**
  - BFS crawler visits internal links up to `max_depth` and `max_pages`.
  - Auth coordinator executes cookie/header injection upon login check.
* **Complexity:** High.

### Sprint 4: Plugin Loader & Base Interfaces
* **Goal:** Implement the plugin loader and ABC interfaces.
* **Files:**
  - `src/webpulse/modules/__init__.py`
  - `src/webpulse/modules/base.py`
  - `src/webpulse/core/plugin_loader.py`
* **Dependencies:** Python's `importlib`, standard library.
* **Acceptance Criteria:**
  - Automatically loads and registers modules containing `manifest.yaml`.
  - Validates manifests against schema.
* **Complexity:** Medium.

### Sprint 5: Subprocess Sandbox Engine
* **Goal:** Build subprocess-based execution wrapper for third-party plugins.
* **Files:**
  - `src/webpulse/core/sandbox.py`
  - `src/webpulse/core/sandbox_worker.py`
* **Dependencies:** `multiprocessing` (built-in).
* **Acceptance Criteria:**
  - Third-party plugins execute in subprocess workers.
  - Communicate successfully via JSON-RPC 2.0.
  - Static AST audit blocks forbidden imports (e.g. `subprocess` without permission).
* **Complexity:** High.

### Sprint 6: Core Analyzer Plugins
* **Goal:** Implement the 8 built-in check modules.
* **Files:**
  - `src/webpulse/modules/security/`
  - `src/webpulse/modules/seo/`
  - `src/webpulse/modules/technology/`
  - `src/webpulse/modules/waf/`
  - `src/webpulse/modules/performance/`
  - `src/webpulse/modules/accessibility/`
  - `src/webpulse/modules/http/`
  - `src/webpulse/modules/ssl/`
* **Dependencies:** BeautifulSoup4, Playwright (optional).
* **Acceptance Criteria:**
  - Built-in checks execute asynchronously.
  - CPU-bound blocks (parsing/tech regex matching) are offloaded to background threads.
* **Complexity:** High.

### Sprint 7: Scoring & Reporting Engine
* **Goal:** Calculate scores and output reports.
* **Files:**
  - `src/webpulse/reports/`
  - `src/webpulse/reports/reporter.py`
  - `src/webpulse/reports/writers/`
* **Dependencies:** JSON Schema, Python standard libraries.
* **Acceptance Criteria:**
  - Deductions applied correctly based on findings.
  - Overall Health Score matches mathematical formulas.
  - Reports generated in JSON, Markdown, HTML, and Console.
* **Complexity:** Medium.

### Sprint 8: CLI Integration & System Delivery
* **Goal:** Implement CLI subcommands and release v1.0.0 stable.
* **Files:**
  - `src/webpulse/cli.py`
* **Dependencies:** `argparse` (built-in).
* **Acceptance Criteria:**
  - Commands (`scan`, `plugins`, `config`) parse correctly.
  - Exits with correct pipelines codes (0, 1, 2, 3).
* **Complexity:** Low.
