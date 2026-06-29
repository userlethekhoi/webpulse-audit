# 02_PRODUCT_REQUIREMENTS.md — WebPulse Product Requirements Specification (v2.0)

## 1. Purpose
This document provides the Software Requirements Specification (SRS) for the WebPulse framework. It details the functional and non-functional requirements, platform support, constraints, assumptions, and acceptance criteria required for Version 2.0.0. It establishes the baseline for all validation and testing activities.

---

## 2. Overview
WebPulse is a cross-platform, command-line interface (CLI) application developed in Python. It executes auditing scans on target domains or IPs using modular analyzer plugins. The engine acts as a coordinator, managing task scheduling, connection pools, plugin lifecycle, configuration overrides, scoring rules, and report writers.

---

## 3. Supported Configurations & Environments

### 3.1 Supported Operating Systems
* **Linux:** Ubuntu 22.04 LTS or higher, Alpine Linux 3.18 or higher (for containerized environments), Debian 12, RHEL/Rocky Linux 9.
* **macOS:** Ventura (13) and Sonoma (14) (Apple Silicon and Intel architectures).
* **Windows:** Windows 10 and 11 (WSL2 recommended, native PowerShell supported).

### 3.2 Supported Python Versions
* **Target Version:** Python 3.11.x and Python 3.12.x.
* **Why:** WebPulse leverages `asyncio.TaskGroup` (introduced in Python 3.11) to simplify async task lifecycle management and exception handling, along with structural pattern matching and improved generic type syntax.

### 3.3 Target Dependency Footprint
* **Core Dependencies:** Minimal. The core framework must only depend on:
  * `httpx` (async HTTP client)
  * `pyyaml` (configuration parser)
  * `pydantic` v2 (data modeling and validation)
  * `cryptography` (for SSL/TLS certificate decoding)
* **Optional / Plugin-Specific Dependencies:**
  * `playwright` (for headless browser execution in performance/accessibility engines). Installs dynamically or operates as an optional extra (`pip install webpulse[browser]`).

---

## 4. Functional Requirements

### 4.1 Scan Execution Engine (FR-01)
* **FR-01.1:** The engine must accept a target URI (HTTP or HTTPS) or IP address as CLI input, converting it into a unified `Target` model.
* **FR-01.2:** The engine must run checks concurrently using an async loop, complying with a configurable rate limit (requests per second).
* **FR-01.3:** The engine must support multi-target batch execution via a text list or JSON input file.
* **FR-01.4:** Scans must be cancelable gracefully (handling SIGINT/SIGTERM) by saving the current state and generating a partial report.
* **FR-01.5 (BFS Crawler):** The engine must include an async breadth-first search (BFS) crawling module (`webpulse.core.crawler`) capable of extracting internal links, managing a parsing queue, and limiting crawls via `max_depth` and `max_pages` configuration parameters.
* **FR-01.6 (Session Authenticator):** The engine must provide a session coordination module (`webpulse.core.auth`) to manage session cookies, authentication headers, or form-based logins, passing authenticated client contexts to plugins.

### 4.2 Module Audits (FR-02)
WebPulse must execute audits across these 8 core vectors:
1. **Security Scanner:** Check HTTP security headers (HSTS, CSP, X-Frame-Options, etc.), cookie flags, and exposed sensitive endpoints.
2. **SEO Analyzer:** Inspect robots.txt, sitemaps, meta tags (title, description, open graph), semantic structure (headings), and link integrity.
3. **Technology Detector:** Heuristic matching of headers, cookies, and HTML structures to identify frameworks, CMSs, and library versions.
4. **WAF Detector:** Heuristic identification of active WAFs (e.g. Cloudflare, AWS WAF, Akamai) via header signatures and custom challenge page analysis.
5. **Performance Analyzer:** Capture TTFB, connection times, transfer sizes, and (if browser mode is enabled) Core Web Vitals (LCP, FID, CLS).
6. **Accessibility Analyzer:** Scan DOM structure against WCAG 2.2 AA rules (image alt tags, form labels, aria attributes, color contrast).
7. **HTTP Analyzer:** Audit HTTP protocol support (HTTP/1.1, HTTP/2, HTTP/3), response codes, and redirect chains.
8. **SSL/TLS Analyzer:** Validate certificate validity, expiration, cipher suites, protocol versions (TLS 1.2, 1.3), and handshake safety.

### 4.3 Plugin System (FR-03)
* **FR-03.1:** Automatically discover and load plugins from configured paths (`~/.webpulse/plugins`, `./plugins`, or site-packages).
* **FR-03.2:** Validate plugin manifests before execution to check version compatibility and category tags.
* **FR-03.3:** Prevent plugins from executing if they declare dependencies that are missing from the system.
* **FR-03.4 (Subprocess Sandbox):** Third-party plugins must run in isolated worker subprocesses by default, communicating via JSON-RPC, to prevent unauthorized system calls or memory leaks in the primary engine.

### 4.4 Reporting (FR-04)
* **FR-04.1:** Write output reports to Console (STDOUT), JSON, Markdown, and HTML.
* **FR-04.2:** Filter findings in reports based on severity levels (Critical, High, Medium, Low, Info).

---

## 5. Non-Functional Requirements

### 5.1 Performance Targets (NFR-01)
* **Concurrency:** The framework must sustain up to 150 concurrent asynchronous connections on a single scanner thread without performance degradation.
* **Execution Time:** A standard HTTP-only scan on a single target must complete in under 5 seconds (assuming network latency < 150ms).
* **Memory Limits:** Under standard operation, the core CLI must not consume more than 150MB of RSS RAM. Under headless browser operation (Playwright), RAM usage must not exceed 600MB.
* **CPU Offloading:** CPU-bound tasks (BeautifulSoup DOM parsing, technological signature matching) must execute in thread pools to keep the async event loop free.

### 5.2 Security Requirements (NFR-02)
* **Input Sanitization:** All target URLs and CLI inputs must be validated using Pydantic schemas before any socket connections are opened.
* **Credential Protection:** Scan secrets or API tokens loaded from environment variables must never be printed to stdout, logged in debug files, or embedded in JSON reports.
* **Plugin Isolation:** Plugins must run in read-only mode relative to the core system settings and cannot modify the configurations of other running plugins.
* **SSRF Safeguards (SR-02.4):** Outbound connections must block RFC 1918 (private) and RFC 6890 (loopback/local) IP addresses by default, unless `--allow-private-ips` is specified.

### 5.3 Usability & CLI Ergonomics (NFR-03)
* **Colorized Console output:** Terminal output must use ANSI color-coding representing severity levels (Red for Critical, Yellow for Warning, Green for Info) and respect the `NO_COLOR` standard.
* **Progress Feedback:** Interactive terminal modes must display a progress bar detailing active, completed, and queued audit tasks.

---

## 6. System Constraints & Assumptions

### 6.1 Constraints
* **Python Interpreter Dependency:** WebPulse requires a pre-installed Python interpreter on the host system. It is not compiled into a native binary in v1.
* **Network Access:** Scans require raw network outbound access on ports 80 and 443. Firewall restrictions on the host OS may block operation.
* **Browser Driver Installation:** Executing performance/accessibility checks requires downloading browser binaries (Chromium/Firefox) via Playwright.

### 6.2 Assumptions
* **Target Cooperation:** It is assumed that targeted web servers will return standard HTTP/1.x or HTTP/2 responses. Non-standard HTTP protocols may cause connection timeouts.
* **Valid DNS Resolution:** The host running WebPulse must have access to a working DNS resolver to perform audits on domain names.

---

## 7. Definition of Done (DoD)
A feature, module, or plugin is considered **Done** and ready to merge into `main` only when it meets the following checklist:

- [ ] **Implementation:** 100% written in Python 3.11+, fully type-hinted, and compliant with `CODING_STANDARDS.md`.
- [ ] **Testing:** Unit test coverage is $\ge$ 90%. All integration tests pass successfully on Linux, macOS, and Windows.
- [ ] **Linting:** Zero warnings from `ruff`, `mypy` (strict mode), and `black`.
- [ ] **Documentation:** The module's public APIs and configuration properties are documented in the code (docstrings) and included in the developer specs.
- [ ] **Error Handling:** All network exceptions are caught, logged, and converted into structured findings. No unhandled tracebacks are exposed to the CLI user.
- [ ] **SSRF Check:** Verified that all network calls go through the validated async client containing SSRF private IP filters.
- [ ] **Sandbox Validation:** Confirm third-party plugins operate successfully inside the process-isolated sandbox worker pool.

---

## 8. Design Decisions

### 8.1 Choice of Async Library: AsyncIO vs. Trio
* **Decision:** We select native `asyncio`.
* **Rationale:** While Trio offers structured concurrency natively, `asyncio` is the standard library and, since Python 3.11, provides `TaskGroup` which handles structured concurrency patterns elegantly without adding an external runtime dependency.

### 8.2 Heuristic Detection Engine strategy
* **Decision:** We use static signature catalogs for Technology and WAF detection, loaded from JSON files.
* **Rationale:** Avoids hardcoding signatures in Python code, making it easy to update rules without releasing new code versions.

---

## 9. References
* CVSS (Common Vulnerability Scoring System) v3.1 Specification: https://www.first.org/cvss/specification-document
* Google Lighthouse Scoring Methodology: https://developer.chrome.com/docs/lighthouse/performance/performance-scoring/
* RFC 1918 Address Allocation for Private Internets: https://datatracker.ietf.org/doc/html/rfc1918

---

## 10. Validation Rules
* Any requirement added to this document must be assigned a unique requirement ID (e.g., `FR-XX` or `NFR-XX`).
* Prior to releasing minor or major versions, all functional requirements listed here must have a corresponding integration test case in `tests/integration/`.

---

## 11. Engineering Notes
* Ensure all async network operations specify an explicit connection timeout (defaulting to 10 seconds). Never perform blocking IO operations in the async loop.

---

## 12. AI Notes
* When generating code for WebPulse, always consult this document first to verify you are not violating constraints (such as Python 3.11 features or dependency limitations).
* Never bypass the validation steps defined in Section 5.2.
