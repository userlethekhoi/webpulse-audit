# WebPulse Sprint 5 Summary

## Completed Features
* **BFS Web Crawler (`src/webpulse/core/crawler.py`)**: Traverses internal site links up to configured `max_depth` and `max_pages` limits. Respects domain restrictions, normalizes query string sorting, and matches path regex parameters to avoid crawling restricted routes (e.g., `/logout`).
* **Session Authentication Coordinator (`src/webpulse/core/auth.py`)**: Executes credentials-based authentication (supporting `post_json` and `post_form` methods) and extracts cookies or header session tokens, automatically injecting them into subsequent client requests.
* **Scoring & Reporting Engine (`src/webpulse/reports/reporter.py`)**:
  * Implements CVSS-inspired category scoring deductions using severity weights (Critical=10.0, High=6.0, Medium=3.0, Low=1.0) and multipliers (Security=1.5, Performance=1.2, Accessibility=1.0, SEO=0.8).
  * Applies root-to-subpage aggregate weights (Root: 50%, Subpages average: 50%).
  * Implements `-15` Security score penalty on session authentication failures.
  * Formulates Overall Health Score and Risk Score (0-10 scale).
  * Generates reports in Console (ANSI colorized with try-except Windows encoding protection), JSON (validated against the schema), Markdown (collapsible details), and HTML (premium responsive dark-mode dashboard with inline SVG circular gauges).
* **CLI Entrypoint Subcommands (`src/webpulse/cli/main.py`)**: Implements `scan`, `plugins`, and `config` entrypoints, tying the engine parts into a unified command executable.

## Files Created or Modified
* **[crawler.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/src/webpulse/core/crawler.py)**: Async BFS web crawler.
* **[auth.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/src/webpulse/core/auth.py)**: Credentials authentication coordinator.
* **[reporter.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/src/webpulse/reports/reporter.py)**: Scoring engine and multi-format reports exporter.
* **[main.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/src/webpulse/cli/main.py)**: Unified CLI subcommand executable.
* **[pyproject.toml](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/pyproject.toml)**: Register console scripts and CLI lint ignores.
* **[test_crawler.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/tests/core/test_crawler.py)**: Tests BFS limits and page traversal.
* **[test_auth.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/tests/core/test_auth.py)**: Tests credentials flow and header injections.
* **[test_reporter.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/tests/reports/test_reporter.py)**: Asserts mathematical scoring deductions and aggregates.
* **[test_cli.py](file:///c:/Users/Le%20The%20Khoi/Downloads/Tester-Website/tests/cli/test_cli.py)**: Asserts CLI subcommands, arguments, and options.

## Architecture Decisions
* **Dynamic Sandbox Subprocesses**: Executed third-party plugins in dynamic isolation processes (`SubprocessSandboxWorker`) communicating via JSON-RPC 2.0. Standardized the subprocess lifecycle by introducing synchronous pipeline `start()`, `execute_plugin()`, and `stop()` steps to prevent zombie workers and memory leaks.
* **Unicode/ANSI Codec Handlers**: Wrapped terminal report output streams in automatic try-except blocks. When writing to default Windows terminals using custom codecs (like `cp1252`), characters fallback to safe replacement encodings, preventing system crashes.
* **Aggregated Scoring Hierarchy**: Pre-calculates category scores per single page, aggregates subpages using a unified arithmetic mean, and applies a weighted calculation across category dimensions.

## Testing Status
* **Test Suites run**: 37 unit/integration tests passed successfully (`100%` pass rate).
* **Coverage**: Verified coverage across core BFS crawling queue bounds, authentication handlers, score weight deductions, and argparse parameters.

## Known Limitations
* **Dynamic Single Page Applications**: The BFS crawler is currently limited to traditional HTML source parsing (anchor links matching) and does not execute client-side JavaScript routers for deep link discovery.

## Technical Debt & Future Work
* **Playwright Crawling**: Future sprints will introduce optional browser-based crawling to resolve JavaScript dynamic routes.
* **WAF/DDoS Simulation Modulators**: Preparing Sprint 6 load-testing simulators.

## Merge Checklist
- [x] All 37 pytest checks passed.
- [x] Ruff check and linting has zero errors.
- [x] Strict Mypy type-checking reports zero issues.
- [x] Verified CLI run parameters (`webpulse scan --help`, `webpulse plugins list`, `webpulse config show`).
