# 12_DEVELOPER_GUIDE.md — Developer Contribution Guide (v2.0)

## 1. Purpose
This document specifies the development practices, coding standards, Git workflow, testing requirements, and release processes for contributors to the WebPulse framework. It serves as the onboarding guide for both human engineers and AI coding agents.

---

## 2. Overview
WebPulse is maintained as a clean, highly structured codebase. All contributions must adhere to rigorous quality gates, including strict linting, automated async testing, and architectural boundary checks.

---

## 3. Git Workflow & Branching Strategy

WebPulse utilizes a simplified Git Flow branching strategy:

```
main       ──────────────────────────[Release v2.0.0]
               ▲
develop    ────┼───────[Merge PR]────────[Candidate]
               │           ▲
feature/*  ────┴───────────┴─[Work]
```

* **`main`:** Production-stable branch. Direct commits are blocked. Releases are tagged from this branch.
* **`develop`:** Integration branch for new features and bug fixes.
* **Feature Branches (`feature/feature-name`):** Branched from `develop`. Merged back via Pull Request.
* **Bugfix Branches (`bugfix/bug-name`):** For resolving specific GitHub issues.

### 3.1 Pull Request Requirements
* Every PR must resolve a single logical change.
* A minimum of one engineering approval is required.
* All CI checks (linting, tests across Linux/Windows/macOS) must pass.
* PR description must link to the corresponding GitHub issue.

---

## 4. Linting, Formatting, and Type Checking

We enforce code quality standards via pre-commit hooks and CI pipelines:

* **Formatter:** `black` (line length 100).
* **Linter:** `ruff` (enforcing PEP8, import ordering, and warning flags).
* **Static Type Checker:** `mypy` in strict mode.

### 4.1 Running validation locally:
```bash
# Run format checks
ruff check .
black --check .

# Run static type checks
mypy webpulse/
```

---

## 5. Testing Guidelines

WebPulse uses `pytest` and `pytest-asyncio` for unit and integration testing.

* **Async Test Rules:** All async test cases must be marked with `@pytest.mark.asyncio` and execute within the event loop context.
* **Network Mocking:** Live internet requests are forbidden during unit tests. You must mock all outgoing HTTP calls using `pytest-mock` or `respx`.
* **SSRF Filtering Mock:** Make sure tests cover IP resolution pathways to assert that RFC 1918 addresses are blocked by default.

### 5.2 Running the test suite:
```bash
# Run all tests with coverage reports
pytest --cov=webpulse --cov-report=term-missing tests/
```

---

## 6. Creating a Custom Plugin (Directory Blueprint)

To build a plugin:
1. Create a subdirectory under `plugins/` matching your plugin name (e.g. `plugins/my_custom_check/`).
2. Add a `manifest.yaml` (following the schema in `05_PLUGIN_SYSTEM.md`).
3. Implement your scanner code subclassing `BasePlugin` inside `plugin.py`, utilizing constructor configurations and lifecycle hooks.

```
plugins/my_custom_check/
 ├── manifest.yaml
 ├── plugin.py
 └── test_plugin.py
```

### 6.1 Testing Sandbox Subprocess Isolation
When testing a third-party plugin, verify it executes correctly within the JSON-RPC sandbox worker:
```bash
pytest tests/core/test_sandbox.py --plugin-dir=plugins/my_custom_check/
```

---

## 7. Versioning and Releases
WebPulse adheres to Semantic Versioning (SemVer) 2.0.0.
* **MAJOR:** Incompatible API changes (e.g. rewriting BasePlugin interfaces).
* **MINOR:** Backwards-compatible functionality (e.g. adding a new analyzer module).
* **PATCH:** Backwards-compatible bug fixes (e.g. fixing a typo in WAF signatures).

---

## 8. Design Decisions
* **Decision:** We use `ruff` instead of combining `flake8`, `isort`, and `autoflake`.
* **Rationale:** `ruff` runs 10x to 100x faster than legacy Python tools, reducing pre-commit hook overhead and accelerating developer feedback loops.

---

## 9. References
* pytest-asyncio documentation: https://pytest-asyncio.readthedocs.io/
* Ruff Linter Documentation: https://beta.ruff.rs/docs/

---

## 10. Validation Rules
* PRs that lower the overall test coverage percentage below 90% will be blocked by the CI check.
* Any public class or method added must include type hints and a Google-style docstring.

---

## 11. Engineering Notes
* When writing mock tests, verify your assertions cover error cases (e.g. connection timeout, dns failures) rather than just validating the happy path.

---

## 12. AI Notes
* Do not introduce code containing print statements. Always use the configured logger (`logger.info`, `logger.debug`).
* Never run tests without mocking outbound network requests.
