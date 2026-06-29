# 04_MODULE_SPECIFICATIONS.md — WebPulse Module Specifications (v2.0)

## 1. Purpose
This document specifies the internal interface contracts, responsibilities, input/output schemas, configuration parameters, and execution flows for all modules within the WebPulse framework. It defines how each component behaves and interfaces with the rest of the system.

---

## 2. Overview
WebPulse's code separation separates the system into **Core Orchestration Modules** and **Audit Analyzer Modules**. All Audit Analyzers subclass the abstract base class `BasePlugin` and return data matching Pydantic-validated result models.

---

## 3. Core Orchestration Modules

### 3.1 CLI Module (`webpulse.cli`)
* **Responsibilities:** Parse user input, setup logging, load profiles, trigger DI injection, and launch scan sessions.
* **Public Interface:**
  ```python
  class CLIEntry:
      def run(self, argv: list[str]) -> int: ...
  ```
* **Inputs:** CLI Arguments string list.
* **Outputs:** Integer exit code (0 = success, 1 = failure, 2 = threshold warning, 3 = critical security).
* **Error Handling:** Catch all runtime exceptions, print standard error formatting to stderr, prevent traceback dumps unless `--debug` is toggled.

### 3.2 Configuration Module (`webpulse.core.config`)
* **Responsibilities:** Load, parse, merge, and validate YAML/JSON/TOML settings.
* **Public Interface:**
  ```python
  class ConfigManager:
      def load_config(self, filepath: Path | None) -> AppConfig: ...
      def get_module_config(self, module_name: str) -> dict[str, Any]: ...
  ```
* **Dependencies:** `pydantic`, `pyyaml`.

### 3.3 Plugin Loader Module (`webpulse.core.plugin_loader`)
* **Responsibilities:** Find, validate, manifest-verify, and load module plugins dynamically.
* **Public Interface:**
  ```python
  class PluginLoader:
      def discover_plugins(self, search_paths: list[Path]) -> list[Type[BasePlugin]]: ...
      def validate_manifest(self, plugin_cls: Type[BasePlugin]) -> bool: ...
  ```

### 3.4 Scheduler Module (`webpulse.core.scheduler`)
* **Responsibilities:** Manage async request queues, connection rates, timeouts, task concurrency, and backoff states.
* **Public Interface:**
  ```python
  class AsyncScheduler:
      def __init__(self, rate_limit: int, max_connections: int): ...
      async def run_scan(self, targets: list[Target], plugins: list[BasePlugin]) -> list[Finding]: ...
  ```

### 3.5 Crawler Module (`webpulse.core.crawler`)
* **Responsibilities:** Implement a breadth-first search (BFS) page crawler to traverse site links, compile a unique queue, and enforce depth boundaries.
* **Public Interface:**
  ```python
  class BFSWebCrawler:
      def __init__(self, max_depth: int, max_pages: int, allowed_domains: list[str]): ...
      async def crawl(self, root_target: Target, client: AsyncNetworkClient) -> list[Target]: ...
  ```
* **Inputs:** Root `Target` URL model, network client.
* **Outputs:** List of discovered subpage `Target` URLs.

### 3.6 Authentication Coordinator (`webpulse.core.auth`)
* **Responsibilities:** Execute authentication routines (cookie injections, bearer tokens, form logins) and maintain session state contexts.
* **Public Interface:**
  ```python
  class AuthCoordinator:
      def __init__(self, auth_config: dict[str, Any]): ...
      async def establish_session(self, client: AsyncNetworkClient) -> bool: ...
      def inject_headers(self, headers: dict[str, str]) -> dict[str, str]: ...
  ```

### 3.7 Sandbox Engine (`webpulse.core.sandbox`)
* **Responsibilities:** Manage subprocess pools to run unverified third-party plugins, communicating via JSON-RPC over stdin/stdout.
* **Public Interface:**
  ```python
  class SubprocessSandboxWorker:
      def __init__(self, plugin_path: Path): ...
      async def launch_and_execute(self, target: Target, config: dict[str, Any]) -> list[Finding]: ...
  ```

### 3.8 Utilities Module (`webpulse.utils`)
* **Responsibilities:** Abstract logging setup, BeautifulSoup parsing (offloaded to threads), and SSRF-safe connection pooling.
* **Public Interface:**
  ```python
  class AsyncNetworkClient:
      def __init__(self, allow_private_ips: bool = False): ...
      async def request(self, method: str, url: str, **kwargs) -> Response: ...
      async def check_ssl(self, host: str, port: int) -> dict[str, Any]: ...

  class AsyncHTMLParser:
      @staticmethod
      async def parse_dom(html_content: str) -> BeautifulSoup: ... # Executes offloaded to thread executor
  ```

---

## 4. Audit Analyzer Modules (Built-in Plugins)

All analyzers implement the following abstract interface:
```python
class BasePlugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata: ...
    
    async def on_load(self, config: dict[str, Any]) -> None:
        """Executed during plugin initialization."""
        self.config = config

    @abstractmethod
    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        """Runs the primary audit logic on the Target."""
        ...

    async def on_unload(self) -> None:
        """Executed when destroying the plugin context."""
        pass
```

### 4.1 Security Scanner (`webpulse.modules.security`)
* **Responsibilities:** Analyze headers (CSP, HSTS, CORS, Cookie flags) and look for sensitive endpoint leaks (e.g. `.git/`, `env`).
* **Inputs:** Target metadata, standard HTTP client.
* **Outputs:** List of `Finding` objects representing header misconfigurations.

### 4.2 SEO Analyzer (`webpulse.modules.seo`)
* **Responsibilities:** Crawl page DOM to analyze title, description length, image alt tags, structural headings, canonical tags, and page indexability.
* **Inputs:** Target DOM and response object.
* **Outputs:** Structured report of SEO compliance violations.

### 4.3 Technology Detector (`webpulse.modules.technology`)
* **Responsibilities:** Match HTTP headers, body content, script patterns, and cookie names against database fingerprints to detect tech stacks.
* **Inputs:** HTTP response object and raw source.
* **Outputs:** Confirmed tech stack tags with a calculated confidence percentage (0-100%).

### 4.4 WAF Detector (`webpulse.modules.waf`)
* **Responsibilities:** Identify firewalls (e.g., Cloudflare, AWS WAF, ModSecurity) by sending intentional payloads to trigger responses and matching returned headers/pages.
* **Inputs:** Target URI, custom injection headers.
* **Outputs:** Identified WAF signature and confidence score.

### 4.5 Performance Analyzer (`webpulse.modules.performance`)
* **Responsibilities:** Track response timings, page weights, script sizes, and Core Web Vitals (when Playwright is enabled).
* **Inputs:** Network logs, Playwright page context.
* **Outputs:** Metrics mapping TTFB, Page Load Time, DOM Content Loaded, LCP, CLS.

### 4.6 Accessibility Analyzer (`webpulse.modules.accessibility`)
* **Responsibilities:** Validate document nodes against WCAG 2.2 criteria.
* **Inputs:** Playwright browser DOM or static HTML structure.
* **Outputs:** List of accessibility barriers found, categorized by level (A, AA).

### 4.7 HTTP Analyzer (`webpulse.modules.http`)
* **Responsibilities:** Audit redirect path limits, status codes, compression availability (Gzip/Brotli), and HTTP version support.
* **Inputs:** Target domain address.
* **Outputs:** Connection stats, compression factors, redirect hop trace list.

### 4.8 SSL Analyzer (`webpulse.modules.ssl`)
* **Responsibilities:** Connect to target socket to decode certificate properties, expiration, weak cipher configurations, and support for TLS versions.
* **Inputs:** Target hostname and port.
* **Outputs:** Certificate validity dates, cipher lists, TLS version compliance list.

### 4.9 Stress Testing Module (`webpulse.modules.stress_test`)
* **Responsibilities:** Perform authorized load testing by scaling concurrency to check site threshold limit parameters.
* **Inputs:** Targeted URL, user rate load limits, connection targets.
* **Outputs:** Request response curves, error percentage levels under load.
* **Security Control:** Requires explicit CLI flag `--yes-i-have-authorization` to execute.

---

## 5. Reporter Module (`webpulse.reports.reporter`)
* **Responsibilities:** Orchestrate findings aggregation, run scoring matrices, generate visual charts, and write output files.
* **Public Interface:**
  ```python
  class Reporter:
      def __init__(self, output_formats: list[str], output_path: Path): ...
      def generate_report(self, target: Target, findings: list[Finding]) -> ScanReport: ...
  ```

---

## 6. Design Decisions
* **Decision:** Built-in analyzer modules are packaged under `webpulse/modules/` but operate under the exact same plugin interfaces as third-party packages.
* **Rationale:** Enforces code symmetry. If a core developer needs to write a new scanning check, they write it as a plugin, keeping the codebase modular.

---

## 7. Future Considerations
* Core utility components will support asynchronous DNS lookup (using `aiodns`) to enable quick subdomain resolution checks in future minor versions.

---

## 8. Validation Rules
* Every module must expose an entry point configuration parameter mapped under its respective section in the root YAML schema.
* No module executing audits may write directly to file files or console stdout; they must only return list objects of `Finding` models.

---

## 9. Engineering Notes
* Always use standard logging loggers (`logging.getLogger("webpulse.modules.<name>")`) inside each module to allow users to toggle verbosity per module.

---

## 10. AI Notes
* When adding a check, locate the appropriate module package folder. Ensure any shared utilities are placed in `webpulse/utils/` rather than repeated across analyzers.
