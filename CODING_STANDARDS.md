# CODING_STANDARDS.md — Enterprise Python Engineering Standard

> **Classification:** Engineering Standard  
> **Version:** 1.0  
> **Language:** Python 3.10+  
> **Applicability:** All source code, AI-generated and human-written  
> **Companion Documents:**  
> - [AI_CODING_SYSTEM_PROMPT.md](./AI_CODING_SYSTEM_PROMPT.md) — Agent behavioral rules  
> - [REVIEW_CHECKLIST.md](./REVIEW_CHECKLIST.md) — Pull request review checklist

---

## How to Use This Document

Every rule in this document follows a consistent format:

- **Rule ID** — Unique identifier for traceability
- **Why** — The engineering rationale behind the rule
- **Bad Example** — What to avoid (❌)
- **Good Example** — What to write (✅)
- **Preferred Alternative** — The recommended approach when multiple valid options exist

**For AI agents:** These rules are constraints. Apply them to every line of code you produce. If a rule conflicts with an existing codebase convention, follow the existing convention and note the deviation.

---

## Table of Contents

1. [Naming](#1-naming)
2. [Imports](#2-imports)
3. [Folder Structure](#3-folder-structure)
4. [Module Organization](#4-module-organization)
5. [Function Size](#5-function-size)
6. [Class Design](#6-class-design)
7. [Comments](#7-comments)
8. [Docstrings](#8-docstrings)
9. [Logging](#9-logging)
10. [Exceptions](#10-exceptions)
11. [Type Hints](#11-type-hints)
12. [Dataclasses](#12-dataclasses)
13. [Enums](#13-enums)
14. [Configuration](#14-configuration)
15. [Constants](#15-constants)
16. [Magic Numbers](#16-magic-numbers)
17. [Dependency Injection](#17-dependency-injection)
18. [Composition](#18-composition)
19. [Patterns](#19-patterns)
20. [Anti-Patterns](#20-anti-patterns)
21. [Python Idioms](#21-python-idioms)
22. [Code Smells](#22-code-smells)
23. [Refactoring Rules](#23-refactoring-rules)

---

## 1. Naming

### NAM-01: Variables Must Describe Their Content

**Why:** Code is read 10× more than written. Descriptive names eliminate the need for comments and reduce cognitive load during review and debugging. A reader should understand what a variable holds without reading its assignment.

❌ **Bad Example:**
```python
d = fetch_data(u)
r = process(d)
for i in r:
    x = i.get("val")
    if x > t:
        res.append(i)
```

✅ **Good Example:**
```python
user_profiles = fetch_user_profiles(organization_id)
active_profiles = filter_active(user_profiles)
for profile in active_profiles:
    login_count = profile.get("login_count")
    if login_count > activity_threshold:
        highly_active_users.append(profile)
```

**Preferred Alternative:** If a variable's scope is a 3-line comprehension, single-letter names (`x`, `k`, `v`) are acceptable. Beyond that, always use descriptive names.

---

### NAM-02: Functions Must Describe Their Action

**Why:** A function name is a contract with the reader. `process()` tells the reader nothing. `validate_and_normalize_email()` tells the reader exactly what will happen, what input is expected, and what to assert in tests.

❌ **Bad Example:**
```python
def handle(data):
    ...

def do_stuff(items):
    ...

def run(config):
    ...
```

✅ **Good Example:**
```python
def validate_email_format(raw_email: str) -> str:
    ...

def calculate_risk_score(findings: list[Finding]) -> float:
    ...

def send_notification_email(recipient: str, subject: str, body: str) -> None:
    ...
```

**Preferred Alternative:** Use the pattern `<verb>_<noun>` for functions: `fetch_headers`, `parse_response`, `validate_url`, `calculate_score`, `generate_report`.

---

### NAM-03: Booleans Must Read as Yes/No Questions

**Why:** Boolean variables appear in `if` statements. When they read as questions, the conditional becomes natural English: `if is_valid:`, `if has_permission:`, `if should_retry:`.

❌ **Bad Example:**
```python
valid = check(url)
flag = True
status = determine_login(user)

if flag:
    ...
if status:
    ...
```

✅ **Good Example:**
```python
is_valid_url = validate_url_format(url)
has_exceeded_rate_limit = True
should_send_notification = determine_notification_eligibility(user)

if has_exceeded_rate_limit:
    ...
if should_send_notification:
    ...
```

**Preferred Alternative:** Prefix booleans with `is_`, `has_`, `should_`, `can_`, `was_`, `will_`, or `needs_`.

---

### NAM-04: Classes Must Be PascalCase Nouns

**Why:** PEP 8 convention. Classes are things (nouns), functions are actions (verbs). This distinction makes code instantly scannable and matches Python ecosystem conventions.

❌ **Bad Example:**
```python
class scan_target:
    ...

class RunAnalysis:
    ...

class HEADER_CHECK:
    ...
```

✅ **Good Example:**
```python
class ScanTarget:
    ...

class SecurityAnalyzer:
    ...

class HeaderCheckResult:
    ...
```

**Preferred Alternative:** If a class represents a service or action, suffix with the pattern type: `HeaderAnalyzer`, `ReportGenerator`, `UrlValidator`.

---

### NAM-05: Constants Must Be UPPER_SNAKE_CASE

**Why:** Visual distinction between mutable variables and immutable constants. When reading code, `MAX_RETRIES` is immediately recognizable as a constant, while `max_retries` looks like a variable that might change.

❌ **Bad Example:**
```python
maxRetries = 3
default_timeout = 30.0
httpOk = 200
```

✅ **Good Example:**
```python
MAX_RETRIES: Final[int] = 3
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0
HTTP_STATUS_OK: Final[int] = 200
```

**Preferred Alternative:** Use `typing.Final` to enforce immutability at the type-checker level, not just by naming convention.

---

### NAM-06: No Shadowing of Built-in Names

**Why:** Shadowing built-ins (`id`, `type`, `list`, `dict`, `input`, `hash`, `format`, `open`, `range`, `map`, `filter`, `set`) creates subtle bugs. Code that calls `id()` later in the same scope will call the local variable, not the built-in.

❌ **Bad Example:**
```python
id = user.get_id()
type = "admin"
list = get_all_items()
input = read_config()
dict = {"key": "value"}
```

✅ **Good Example:**
```python
user_id = user.get_id()
account_type = "admin"
all_items = get_all_items()
config_input = read_config()
settings_dict = {"key": "value"}
```

**Preferred Alternative:** Append a domain-specific suffix: `_id`, `_type`, `_list`, `_input`, `_map`.

---

## 2. Imports

### IMP-01: Imports Must Be Grouped and Ordered

**Why:** Consistent ordering makes imports scannable at a glance. Readers can immediately see which standard library, third-party, and local modules are in use — essential for dependency auditing and understanding external coupling.

❌ **Bad Example:**
```python
from myproject.core import models
import os
import httpx
from pathlib import Path
import json
from myproject.config import settings
import asyncio
```

✅ **Good Example:**
```python
import asyncio
import json
import os
from pathlib import Path

import httpx

from myproject.config import settings
from myproject.core import models
```

**Preferred Alternative:** Use `ruff` or `isort` to enforce ordering automatically. Configure in `pyproject.toml`:
```toml
[tool.ruff.lint.isort]
known-first-party = ["myproject"]
```

---

### IMP-02: Import Modules, Not Individual Objects (Except From Local)

**Why:** `import module` preserves namespace provenance. When reading `json.loads()`, you know exactly where `loads` comes from. With `from json import loads`, then `loads()` is ambiguous — especially with 30 imports at the top of a file.

❌ **Bad Example:**
```python
from os import path, getcwd, listdir
from json import loads, dumps
from pathlib import Path
from collections import defaultdict, Counter, deque
```

✅ **Good Example:**
```python
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
```

**Preferred Alternative:** Use `from x import y` when importing classes, specific functions from local modules, or when the module name is long and the imported name is unambiguous: `from datetime import datetime, timezone`.

---

### IMP-03: No Unused Imports

**Why:** Unused imports add noise, increase startup time, create false dependencies, and confuse readers into thinking a module is in use. They also produce linter warnings that mask real issues.

❌ **Bad Example:**
```python
import os          # Never used
import sys         # Never used
import json
from typing import Optional, Union, Any  # Only json is used
```

✅ **Good Example:**
```python
import json
```

**Preferred Alternative:** Run `ruff check --select F401` to detect unused imports automatically. Configure as a pre-commit hook.

---

### IMP-04: No Wildcard Imports

**Why:** `from module import *` imports an unknown set of names into the namespace. It makes it impossible to determine where a name came from, causes name collisions, and defeats static analysis tools like `mypy`.

❌ **Bad Example:**
```python
from os.path import *
from myproject.models import *
from myproject.utils import *
```

✅ **Good Example:**
```python
from myproject.models import Finding, ScanReport, Severity
from myproject.utils import validate_url, format_duration
```

**Preferred Alternative:** Import exactly what you need. If the list is long, it suggests the source module is doing too much — consider refactoring.

---

## 3. Folder Structure

### FS-01: Directory Structure Must Match Architectural Layers

**Why:** When the folder tree reflects the architecture, navigating the codebase is intuitive. A developer looking for "business logic" goes to `core/`. Looking for "HTTP client" goes to `infra/`. There is no guessing.

❌ **Bad Example:**
```
myproject/
├── helpers.py
├── utils.py
├── main.py
├── stuff.py
├── handlers.py
├── more_handlers.py
└── db.py
```

✅ **Good Example:**
```
myproject/
├── __init__.py
├── main.py               # Entry point only
├── core/                  # Business logic (no I/O)
│   ├── __init__.py
│   ├── models.py
│   ├── analyzers/
│   └── aggregator.py
├── infra/                 # Infrastructure (I/O, network)
│   ├── __init__.py
│   ├── http_client.py
│   └── report_writer.py
├── config/
│   ├── __init__.py
│   └── settings.py
└── exceptions.py
```

**Preferred Alternative:** Match directory depth to actual complexity. A 200-line project does not need 5 levels of nesting. Scale structure to project size.

---

### FS-02: Test Directory Must Mirror Source Directory

**Why:** Parallel structure makes it trivial to find the test file for any source file. When `myproject/core/analyzers/header_analyzer.py` is modified, the reviewer knows to check `tests/unit/core/analyzers/test_header_analyzer.py`.

❌ **Bad Example:**
```
tests/
├── test_everything.py     # One giant test file
├── test_misc.py
└── test_more.py
```

✅ **Good Example:**
```
tests/
├── conftest.py
├── unit/
│   ├── core/
│   │   ├── analyzers/
│   │   │   ├── test_header_analyzer.py
│   │   │   └── test_tls_analyzer.py
│   │   └── test_aggregator.py
│   └── infra/
│       ├── test_http_client.py
│       └── test_report_writer.py
└── integration/
    └── test_scan_pipeline.py
```

**Preferred Alternative:** The naming convention is `test_<source_module_name>.py`. Never `test_1.py` or `tests_for_stuff.py`.

---

## 4. Module Organization

### MOD-01: Each Module Has a Single Responsibility

**Why:** A module that does one thing is easy to understand, test, and replace. A module that does five things has five reasons to change, five sets of dependencies, and creates coupling between unrelated concepts.

❌ **Bad Example:**
```python
# utils.py — The dumping ground
def validate_url(url): ...
def format_date(dt): ...
def send_email(to, subject, body): ...
def calculate_checksum(data): ...
def retry_with_backoff(func): ...
def parse_csv(filepath): ...
```

✅ **Good Example:**
```python
# validators.py — Input validation only
def validate_url(url: str) -> str: ...
def validate_email(email: str) -> str: ...
def validate_ip_address(ip: str) -> str: ...
```

**Preferred Alternative:** If you're tempted to create `utils.py` or `helpers.py`, stop. Ask: what do these functions have in common? Group by responsibility, not by "leftover."

---

### MOD-02: Module Public API Defined by `__all__`

**Why:** Without `__all__`, every top-level name in a module is part of its public API. This means renaming an internal helper is a breaking change. `__all__` makes the public surface explicit and intentional.

❌ **Bad Example:**
```python
# models.py — everything is implicitly public
import re

PATTERN = re.compile(r"...")  # Internal implementation detail

class Finding: ...       # Intended public
class _Parser: ...       # Private by convention only

def _helper(): ...       # Private by convention only
def create_finding(): ...  # Intended public
```

✅ **Good Example:**
```python
# models.py
__all__ = ["Finding", "create_finding"]

import re

_PATTERN = re.compile(r"...")

class Finding: ...

class _Parser: ...

def _helper(): ...

def create_finding(): ...
```

**Preferred Alternative:** Combine `__all__` in the module with re-exports in `__init__.py` to create a clean package-level API.

---

## 5. Function Size

### FN-01: Functions Must Be ≤ 40 Lines of Logic

**Why:** Short functions are easier to name, test, review, and debug. If a function exceeds 40 lines, it is doing more than one thing. The "one screen" rule ensures a reviewer can see the entire function without scrolling.

❌ **Bad Example:**
```python
def process_scan_results(results):
    # 15 lines of validation
    # 20 lines of transformation
    # 15 lines of aggregation
    # 10 lines of formatting
    # 10 lines of output
    # Total: 70 lines — too many responsibilities
    ...
```

✅ **Good Example:**
```python
def process_scan_results(results: list[RawResult]) -> ScanReport:
    validated = validate_results(results)
    findings = extract_findings(validated)
    aggregated = aggregate_by_severity(findings)
    return format_report(aggregated)
```

**Preferred Alternative:** Extract until each function does exactly one thing. The orchestrating function becomes a readable recipe: validate → extract → aggregate → format.

---

### FN-02: Functions Must Have ≤ 5 Parameters

**Why:** Functions with many parameters are hard to call correctly, hard to test (combinatorial explosion), and usually indicate the function is doing too much. More than 5 parameters suggests the need for a configuration object.

❌ **Bad Example:**
```python
def scan_target(url, timeout, retries, proxy, verify_ssl,
                follow_redirects, max_redirects, user_agent,
                headers, cookies, auth_token):
    ...
```

✅ **Good Example:**
```python
@dataclass(frozen=True)
class ScanConfig:
    timeout: float = 30.0
    retries: int = 3
    proxy: str | None = None
    verify_ssl: bool = True
    follow_redirects: bool = True
    max_redirects: int = 5
    user_agent: str = "Scanner/1.0"

async def scan_target(url: str, config: ScanConfig = ScanConfig()) -> ScanReport:
    ...
```

**Preferred Alternative:** Group related parameters into a `dataclass` or `pydantic.BaseModel`. The function becomes `scan_target(url, config)`.

---

### FN-03: Nesting Depth Must Be ≤ 3 Levels

**Why:** Each nesting level multiplies the number of mental states the reader must track. At 5 levels deep, the reader has lost track of which `if` they're inside. Early returns (guard clauses) flatten logic dramatically.

❌ **Bad Example:**
```python
def process(items):
    if items:
        for item in items:
            if item.is_valid():
                if item.has_data():
                    for field in item.fields:
                        if field.name in REQUIRED:
                            result = transform(field)
                            if result:
                                yield result
```

✅ **Good Example:**
```python
def process(items: list[Item]) -> Iterator[Result]:
    if not items:
        return

    for item in items:
        if not item.is_valid() or not item.has_data():
            continue

        yield from _process_fields(item.fields)

def _process_fields(fields: list[Field]) -> Iterator[Result]:
    for field in fields:
        if field.name not in REQUIRED:
            continue
        result = transform(field)
        if result:
            yield result
```

**Preferred Alternative:** Use early returns, `continue`, and extracted helper functions to keep nesting shallow.

---

## 6. Class Design

### CLS-01: Prefer Composition Over Inheritance

**Why:** Inheritance creates tight coupling — the subclass is bound to the superclass's implementation. Composition creates loose coupling — the container can swap components without changing its interface. Inheritance is the strongest relationship in OOP; use it sparingly.

❌ **Bad Example:**
```python
class SecurityScanner(HTTPClient):
    """Scanner IS-A HTTPClient? No — it HAS-A client."""
    def scan(self, url: str) -> Report:
        response = self.get(url)  # Inherited from HTTPClient
        return self.analyze(response)
```

✅ **Good Example:**
```python
class SecurityScanner:
    """Scanner HAS-A client. Client is injectable and replaceable."""
    def __init__(self, client: HTTPClient) -> None:
        self._client = client

    async def scan(self, url: str) -> Report:
        response = await self._client.get(url)
        return self._analyze(response)
```

**Preferred Alternative:** Use inheritance only for interface contracts (`ABC`, `Protocol`) and truly is-a relationships. For everything else, compose.

---

### CLS-02: Classes Must Be Small and Focused

**Why:** A class with 20 methods and 15 attributes is doing too much. It's hard to test, hard to modify, and accumulates responsibility over time. Small classes are cheap to understand and safe to change.

❌ **Bad Example:**
```python
class WebAuditor:
    def scan_headers(self): ...
    def scan_tls(self): ...
    def scan_cookies(self): ...
    def generate_json_report(self): ...
    def generate_html_report(self): ...
    def send_email_notification(self): ...
    def save_to_database(self): ...
    def validate_url(self): ...
    def configure_proxy(self): ...
    # 15 more methods...
```

✅ **Good Example:**
```python
class HeaderAnalyzer:
    """Analyzes HTTP response headers."""
    def analyze(self, headers: dict[str, str]) -> list[Finding]: ...

class TLSAnalyzer:
    """Analyzes TLS/SSL configuration."""
    def analyze(self, cert_info: CertInfo) -> list[Finding]: ...

class ReportWriter:
    """Formats findings into output reports."""
    def write_json(self, findings: list[Finding]) -> str: ...
    def write_text(self, findings: list[Finding]) -> str: ...
```

**Preferred Alternative:** Apply the Single Responsibility Principle. If describing the class requires "and" ("scans AND reports AND notifies"), split it.

---

### CLS-03: Use `Protocol` for Structural Typing

**Why:** `Protocol` enables duck typing with type safety. A function that accepts any object with a `.read()` method should declare `Readable`, not require a specific class hierarchy. This maximizes flexibility and testability.

❌ **Bad Example:**
```python
from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, data: dict) -> list[Finding]: ...

# Forces every analyzer to inherit from BaseAnalyzer
class HeaderAnalyzer(BaseAnalyzer):
    def analyze(self, data: dict) -> list[Finding]: ...
```

✅ **Good Example:**
```python
from typing import Protocol

class Analyzer(Protocol):
    def analyze(self, data: dict[str, str]) -> list[Finding]: ...

# No inheritance needed — just implement the method
class HeaderAnalyzer:
    def analyze(self, data: dict[str, str]) -> list[Finding]: ...

def run_analysis(analyzer: Analyzer, data: dict[str, str]) -> list[Finding]:
    return analyzer.analyze(data)
```

**Preferred Alternative:** Use `Protocol` for duck typing, `ABC` only when you need shared implementation (methods, properties) in the base.

---

## 7. Comments

### CMT-01: Comments Explain WHY, Not WHAT

**Why:** The code already says WHAT it does. A comment restating the code adds noise without value. A comment explaining WHY — the business reason, the non-obvious constraint, the workaround — adds context that the code cannot express.

❌ **Bad Example:**
```python
# Increment the counter
counter += 1

# Check if the list is empty
if not items:
    return

# Set timeout to 30
timeout = 30
```

✅ **Good Example:**
```python
# Compensate for off-by-one in the upstream pagination API
counter += 1

# The aggregator expects at least one item; empty input
# means the scan produced no results (not an error)
if not items:
    return

# The vendor SLA guarantees response within 25s;
# 30s gives a 5s buffer before we time out
timeout = 30
```

**Preferred Alternative:** If you feel the need to comment WHAT code does, the code is too complex. Refactor for clarity instead of adding explanatory comments.

---

### CMT-02: No Commented-Out Code

**Why:** Version control exists to preserve history. Commented-out code creates uncertainty: Is this intentionally disabled? Is it a TODO? Is it dead code? It also biases future developers toward uncommenting rather than redesigning.

❌ **Bad Example:**
```python
def scan(url: str) -> Report:
    # response = old_client.fetch(url)
    # findings = legacy_analyze(response)
    response = new_client.fetch(url)
    findings = analyze(response)
    # if settings.ENABLE_DEEP_SCAN:
    #     findings += deep_analyze(response)
    return Report(findings=findings)
```

✅ **Good Example:**
```python
def scan(url: str) -> Report:
    response = new_client.fetch(url)
    findings = analyze(response)
    return Report(findings=findings)
```

**Preferred Alternative:** Delete commented-out code. Use `git log` to find old implementations. If something needs to be re-enabled, create a tracked issue.

---

## 8. Docstrings

### DOC-01: All Public Functions Must Have Docstrings

**Why:** Docstrings are the contract between the function and its callers. They enable IDE tooltips, auto-generated API documentation, and faster onboarding. A function without a docstring is a function that requires reading its implementation to understand.

❌ **Bad Example:**
```python
def analyze_headers(headers, url):
    results = []
    for name, value in headers.items():
        # 30 lines of logic...
    return results
```

✅ **Good Example:**
```python
def analyze_headers(
    headers: dict[str, str],
    url: str,
) -> list[Finding]:
    """Analyze HTTP response headers against security best practices.

    Checks for missing security headers (CSP, HSTS, X-Frame-Options),
    misconfigured values, and deprecated headers.

    Args:
        headers: HTTP response headers as key-value pairs.
        url: The target URL (used for context in findings).

    Returns:
        List of Finding objects, one per detected issue.
        Returns empty list if no issues found.

    Raises:
        ValueError: If headers dict is None.
    """
```

**Preferred Alternative:** Use Google-style docstrings (as shown). If the project uses NumPy or reST style, follow the project convention. Consistency matters more than format choice.

---

### DOC-02: Docstrings Must Match Actual Behavior

**Why:** A stale docstring is worse than no docstring. It actively misleads readers. When you change a function's parameters, return type, or exception behavior, the docstring must be updated in the same commit.

❌ **Bad Example:**
```python
def fetch_url(url: str, timeout: float = 30.0) -> Response:
    """Fetch a URL and return the response.

    Args:
        url: Target URL.
        verify: Whether to verify SSL.    # <-- parameter was removed!

    Returns:
        Response text as string.           # <-- actually returns Response object!
    """
```

✅ **Good Example:**
```python
def fetch_url(url: str, timeout: float = 30.0) -> Response:
    """Fetch a URL using async HTTP GET and return the full response.

    Args:
        url: Target URL. Must be a valid HTTP/HTTPS URL.
        timeout: Request timeout in seconds. Defaults to 30.0.

    Returns:
        httpx.Response with status code, headers, and body.

    Raises:
        httpx.TimeoutException: If request exceeds timeout.
        httpx.ConnectError: If connection cannot be established.
    """
```

**Preferred Alternative:** Treat docstring updates as part of the function change. If you change the function, update the docstring in the same edit.

---

## 9. Logging

### LOG-01: Use `logging`, Never `print()`

**Why:** `print()` writes to stdout, is not filterable by level, cannot be redirected, has no timestamps, and mixes diagnostic output with application output. `logging` provides levels, formatters, handlers, and is the Python standard.

❌ **Bad Example:**
```python
def scan(url: str) -> Report:
    print(f"Starting scan of {url}")
    print(f"DEBUG: headers = {headers}")
    print("ERROR: connection failed!")
    print(f"Scan complete in {duration}s")
```

✅ **Good Example:**
```python
logger = logging.getLogger(__name__)

async def scan(url: str) -> Report:
    logger.info("Starting scan of %s", url)
    logger.debug("Response headers: %s", headers)
    logger.error("Connection failed for %s: %s", url, error)
    logger.info("Scan completed in %.2fs", duration)
```

**Preferred Alternative:** `logger = logging.getLogger(__name__)` at the module level. Configure logging once in the entry point.

---

### LOG-02: Use Lazy Formatting in Log Calls

**Why:** f-strings are evaluated immediately, even if the log level is disabled. `logger.debug(f"Data: {expensive_serialize(obj)}")` calls `expensive_serialize()` even when DEBUG is off. Lazy formatting (`%s`) defers evaluation.

❌ **Bad Example:**
```python
logger.debug(f"Processing {len(items)} items: {items}")
logger.info(f"User {user.name} logged in at {datetime.now()}")
logger.error(f"Failed with error: {traceback.format_exc()}")
```

✅ **Good Example:**
```python
logger.debug("Processing %d items: %s", len(items), items)
logger.info("User %s logged in at %s", user.name, datetime.now())
logger.error("Failed with error: %s", traceback.format_exc())
```

**Preferred Alternative:** If using `structlog`, follow its conventions for key-value logging: `logger.info("user_login", user=user.name)`.

---

### LOG-03: Never Log Secrets

**Why:** Logs are stored, aggregated, and often accessible to broad teams. A password, token, or API key in logs is a credential leak. Even DEBUG-level logs may be collected in production incidents.

❌ **Bad Example:**
```python
logger.debug("Authenticating with token: %s", api_token)
logger.info("Connecting to %s with password %s", host, password)
logger.error("Request failed. Headers: %s", dict(response.headers))
```

✅ **Good Example:**
```python
logger.debug("Authenticating with token: %s", "***REDACTED***")
logger.info("Connecting to %s with credentials", host)
logger.error("Request failed. Status: %d", response.status_code)
```

**Preferred Alternative:** Build a redaction utility that masks known secret fields before logging. Apply it to all structured log output.

---

## 10. Exceptions

### EXC-01: Never Use Bare `except:`

**Why:** Bare `except:` catches `KeyboardInterrupt`, `SystemExit`, `GeneratorExit`, and `MemoryError` — all of which should propagate. It makes debugging impossible because you can't tell what went wrong.

❌ **Bad Example:**
```python
try:
    result = perform_scan(url)
except:
    return None
```

✅ **Good Example:**
```python
try:
    result = perform_scan(url)
except httpx.TimeoutException:
    logger.warning("Scan timed out for %s", url)
    return ScanResult.timeout(url)
except httpx.ConnectError as exc:
    logger.error("Connection failed for %s: %s", url, exc)
    raise ScanError(f"Cannot connect to {url}") from exc
```

**Preferred Alternative:** Catch the most specific exception possible. List multiple types if needed: `except (TimeoutException, ConnectError) as exc:`.

---

### EXC-02: Never Swallow Exceptions Silently

**Why:** `except SomeError: pass` hides bugs. The failure happened, but no one knows. Debugging becomes a hunt for "why does this return None sometimes?" Always log, re-raise, or return a meaningful error.

❌ **Bad Example:**
```python
try:
    config = load_config(path)
except FileNotFoundError:
    pass  # Silently ignore missing config

try:
    data = parse(raw)
except ValueError:
    pass  # ??? What happens now?
```

✅ **Good Example:**
```python
try:
    config = load_config(path)
except FileNotFoundError:
    logger.info("Config file not found at %s, using defaults", path)
    config = DefaultConfig()

try:
    data = parse(raw)
except ValueError as exc:
    logger.warning("Failed to parse input: %s", exc)
    raise ValidationError(f"Invalid input format: {exc}") from exc
```

**Preferred Alternative:** Every `except` block must do at least one of: log, re-raise, return a meaningful fallback, or raise a domain exception.

---

### EXC-03: Use Exception Chaining with `from`

**Why:** When catching one exception and raising another, `raise New() from original` preserves the full stack trace. Without `from`, debugging requires guessing what the original error was.

❌ **Bad Example:**
```python
try:
    response = await client.get(url)
except httpx.ConnectError:
    raise ScanError("Connection failed")  # Original traceback lost
```

✅ **Good Example:**
```python
try:
    response = await client.get(url)
except httpx.ConnectError as exc:
    raise ScanError(f"Connection failed for {url}") from exc
```

**Preferred Alternative:** Always use `from exc` when wrapping exceptions. Use `from None` only when you intentionally want to suppress the chain.

---

### EXC-04: Define a Project Exception Hierarchy

**Why:** Domain exceptions communicate intent. `raise ScanTimeoutError(url)` is instantly understood. `raise RuntimeError("timeout")` requires reading the message to understand what happened. A hierarchy enables granular catching.

❌ **Bad Example:**
```python
raise ValueError("URL is invalid")
raise RuntimeError("scan failed")
raise Exception("timeout")
```

✅ **Good Example:**
```python
class WebPulseError(Exception):
    """Base exception for all WebPulse errors."""

class ValidationError(WebPulseError):
    """Invalid input provided by the user."""

class NetworkError(WebPulseError):
    """Base class for all network-related errors."""

class ScanTimeoutError(NetworkError):
    """Scan exceeded the configured timeout."""

class ConnectionRefusedError(NetworkError):
    """Target refused the connection."""
```

**Preferred Alternative:** Define the hierarchy in a single `exceptions.py` file. All modules import from there.

---

## 11. Type Hints

### TYP-01: All Function Signatures Must Be Fully Annotated

**Why:** Type hints enable `mypy` to catch bugs before runtime. They serve as machine-verified documentation. A function with type hints tells the reader what it accepts and returns without reading the implementation.

❌ **Bad Example:**
```python
def analyze(headers, url):
    results = []
    for name, value in headers.items():
        if check(name, value):
            results.append(make_finding(name, value, url))
    return results
```

✅ **Good Example:**
```python
def analyze(
    headers: dict[str, str],
    url: str,
) -> list[Finding]:
    results: list[Finding] = []
    for name, value in headers.items():
        if is_insecure_header(name, value):
            results.append(Finding.from_header(name, value, url))
    return results
```

**Preferred Alternative:** Use `mypy --strict` to enforce complete type annotations project-wide.

---

### TYP-02: Use Modern Union Syntax (3.10+)

**Why:** `str | None` is shorter, more readable, and matches natural language ("string or None") better than `Optional[str]`. It was introduced as standard syntax in Python 3.10.

❌ **Bad Example:**
```python
from typing import Optional, Union, List, Dict

def fetch(url: Optional[str] = None) -> Union[Dict[str, str], None]:
    items: List[str] = []
```

✅ **Good Example:**
```python
def fetch(url: str | None = None) -> dict[str, str] | None:
    items: list[str] = []
```

**Preferred Alternative:** For Python 3.9, use `from __future__ import annotations` to enable `str | None` syntax.

---

## 12. Dataclasses

### DC-01: Use Dataclasses for Structured Data

**Why:** Dataclasses generate `__init__`, `__repr__`, `__eq__` automatically. They enforce type annotations, reduce boilerplate, and are a clear signal: "this is a data container, not a behavior object." Plain dicts provide none of these guarantees.

❌ **Bad Example:**
```python
def create_finding(title, severity, description, url):
    return {
        "title": title,
        "severity": severity,
        "description": description,
        "url": url,
    }

finding = create_finding("Missing CSP", "HIGH", "...", "https://...")
print(finding["sevrity"])  # Typo — KeyError at runtime!
```

✅ **Good Example:**
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Finding:
    title: str
    severity: Severity
    description: str
    url: str

finding = Finding(title="Missing CSP", severity=Severity.HIGH, ...)
print(finding.sevrity)  # Typo — caught by mypy at type-check time!
```

**Preferred Alternative:** Use `frozen=True` for value objects that should not be mutated after creation. Use `pydantic.BaseModel` when you need validation, serialization, or parsing from external data.

---

## 13. Enums

### ENUM-01: Use Enums for Fixed Value Sets

**Why:** String literals for states, statuses, and categories are error-prone. `"high"`, `"HIGH"`, `"High"` are three different strings. An `Enum` guarantees a closed set of values, enables IDE autocompletion, and catches typos at import time.

❌ **Bad Example:**
```python
finding["severity"] = "high"
if severity == "CRITICAL":    # Was it "critical" or "CRITICAL"?
    alert()
if status == "complte":       # Typo — silently wrong
    finish()
```

✅ **Good Example:**
```python
from enum import Enum

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

if finding.severity == Severity.CRITICAL:  # Type-safe, IDE-supported
    alert()
```

**Preferred Alternative:** For string enums that need serialization, use `class Severity(str, Enum)` so they serialize to their string values automatically.

---

## 14. Configuration

### CFG-01: Use Pydantic Settings for Configuration

**Why:** Pydantic settings provides type validation, environment variable parsing, default values, and documentation in a single class. Raw `os.getenv()` returns untyped strings with no validation.

❌ **Bad Example:**
```python
timeout = int(os.getenv("TIMEOUT", "30"))       # Crashes on "abc"
debug = os.getenv("DEBUG", "false") == "true"    # "True" won't work
proxy = os.getenv("PROXY")                       # No validation
```

✅ **Good Example:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WEBPULSE_")

    timeout: float = 30.0
    debug: bool = False
    proxy: str | None = None
    concurrency: int = Field(default=10, ge=1, le=100)
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

settings = Settings()  # Auto-reads WEBPULSE_TIMEOUT, etc.
```

**Preferred Alternative:** Validate all configuration at startup. If validation fails, crash immediately with a clear error — not silently 10 minutes into execution.

---

## 15. Constants

### CONST-01: Constants Must Be Module-Level and Typed

**Why:** Constants defined at the module level are easy to find, easy to override for testing, and clearly visible in code reviews. Constants buried inside functions are invisible and duplicated.

❌ **Bad Example:**
```python
def retry_request(url):
    for i in range(3):              # Magic number
        try:
            return fetch(url)
        except TimeoutError:
            time.sleep(2 ** i)      # Magic number
    raise RetriesExhausted(url)
```

✅ **Good Example:**
```python
from typing import Final

MAX_RETRIES: Final[int] = 3
BACKOFF_BASE_SECONDS: Final[float] = 1.0

def retry_request(url: str) -> Response:
    for attempt in range(MAX_RETRIES):
        try:
            return fetch(url)
        except TimeoutError:
            sleep_seconds = BACKOFF_BASE_SECONDS * (2 ** attempt)
            time.sleep(sleep_seconds)
    raise RetriesExhausted(url, max_retries=MAX_RETRIES)
```

**Preferred Alternative:** Group related constants in a dedicated `constants.py` module or a frozen dataclass for namespacing.

---

## 16. Magic Numbers

### MAGIC-01: Replace All Magic Numbers and Strings with Named Constants

**Why:** `if status == 200` means nothing to a new reader. `if status == HTTP_STATUS_OK` is self-documenting. Named constants also create a single source of truth — changing `HTTP_STATUS_OK` updates every usage.

❌ **Bad Example:**
```python
if response.status_code == 200:
    ...
elif response.status_code == 429:
    time.sleep(60)
elif response.status_code == 503:
    time.sleep(5)

if len(results) > 100:
    paginate(results)

timeout = 30
```

✅ **Good Example:**
```python
HTTP_OK: Final[int] = 200
HTTP_TOO_MANY_REQUESTS: Final[int] = 429
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503
RATE_LIMIT_WAIT_SECONDS: Final[float] = 60.0
SERVICE_RETRY_SECONDS: Final[float] = 5.0
PAGINATION_THRESHOLD: Final[int] = 100
DEFAULT_TIMEOUT_SECONDS: Final[float] = 30.0

if response.status_code == HTTP_OK:
    ...
elif response.status_code == HTTP_TOO_MANY_REQUESTS:
    time.sleep(RATE_LIMIT_WAIT_SECONDS)
elif response.status_code == HTTP_SERVICE_UNAVAILABLE:
    time.sleep(SERVICE_RETRY_SECONDS)
```

**Preferred Alternative:** For HTTP status codes specifically, use `http.HTTPStatus.OK` from the standard library.

---

## 17. Dependency Injection

### DI-01: Inject Dependencies Through Constructors

**Why:** Constructor injection makes dependencies explicit. A class that receives its HTTP client, database connection, and logger through `__init__` declares its requirements in its signature. This enables testing with fakes and prevents hidden coupling.

❌ **Bad Example:**
```python
class SecurityScanner:
    def __init__(self):
        self.client = httpx.AsyncClient()   # Hidden dependency
        self.db = Database.connect()         # Hidden dependency
        self.cache = RedisCache()            # Hidden dependency

    async def scan(self, url: str) -> Report:
        response = await self.client.get(url)
        ...
```

✅ **Good Example:**
```python
class SecurityScanner:
    def __init__(
        self,
        client: httpx.AsyncClient,
        repository: ScanRepository,
    ) -> None:
        self._client = client
        self._repository = repository

    async def scan(self, url: str) -> Report:
        response = await self._client.get(url)
        ...

# In production:
async with httpx.AsyncClient() as client:
    scanner = SecurityScanner(client=client, repository=PostgresRepository())

# In tests:
scanner = SecurityScanner(client=mock_client, repository=InMemoryRepository())
```

**Preferred Alternative:** For simple projects, constructor injection is sufficient. No framework needed. For complex projects, consider a lightweight DI container.

---

## 18. Composition

### COMP-01: Build Complex Behavior from Simple Components

**Why:** Composition assembles behavior from independent, testable pieces. Each piece can be developed, tested, and replaced independently. This is the antidote to monolithic classes that grow indefinitely.

❌ **Bad Example:**
```python
class MegaScanner:
    """Does everything: HTTP, analysis, reporting, notification."""
    def fetch(self, url): ...
    def analyze_headers(self, response): ...
    def analyze_tls(self, response): ...
    def analyze_cookies(self, response): ...
    def generate_json(self, findings): ...
    def generate_html(self, findings): ...
    def send_email(self, report): ...
    def save_to_db(self, report): ...
```

✅ **Good Example:**
```python
class ScanPipeline:
    """Orchestrates scanning by composing independent components."""
    def __init__(
        self,
        client: HTTPClient,
        analyzers: list[Analyzer],
        reporter: Reporter,
    ) -> None:
        self._client = client
        self._analyzers = analyzers
        self._reporter = reporter

    async def execute(self, url: str) -> Report:
        response = await self._client.fetch(url)
        findings = []
        for analyzer in self._analyzers:
            findings.extend(analyzer.analyze(response))
        return self._reporter.generate(findings)
```

**Preferred Alternative:** The pipeline pattern — compose a sequence of independent steps that each transform data. Each step is testable in isolation.

---

## 19. Patterns

### PAT-01: Strategy Pattern — Swap Algorithms at Runtime

**Why:** When multiple algorithms exist for the same operation (e.g., different report formats), the Strategy pattern encapsulates each algorithm and makes them interchangeable without modifying the caller.

❌ **Bad Example:**
```python
def generate_report(findings, format_type):
    if format_type == "json":
        return json.dumps([f.to_dict() for f in findings])
    elif format_type == "html":
        return "<html>..."
    elif format_type == "csv":
        return "title,severity\n..."
    elif format_type == "xml":
        return "<findings>..."
    # Every new format modifies this function
```

✅ **Good Example:**
```python
class ReportFormatter(Protocol):
    def format(self, findings: list[Finding]) -> str: ...

class JsonFormatter:
    def format(self, findings: list[Finding]) -> str:
        return json.dumps([f.to_dict() for f in findings], indent=2)

class HtmlFormatter:
    def format(self, findings: list[Finding]) -> str:
        ...

FORMATTERS: dict[str, ReportFormatter] = {
    "json": JsonFormatter(),
    "html": HtmlFormatter(),
}

def generate_report(findings: list[Finding], format_name: str) -> str:
    formatter = FORMATTERS[format_name]
    return formatter.format(findings)
```

**Preferred Alternative:** Use a `Protocol` for the strategy interface. Register implementations in a dict for O(1) lookup.

---

### PAT-02: Factory Pattern — Encapsulate Object Creation

**Why:** When object creation involves logic (choosing which class, configuring options, validating inputs), a factory centralizes that logic. Callers don't need to know which concrete class to instantiate.

❌ **Bad Example:**
```python
# Scattered across the codebase
if output_type == "json":
    writer = JsonWriter(indent=2, sort_keys=True)
elif output_type == "text":
    writer = TextWriter(width=80, color=True)
elif output_type == "html":
    writer = HtmlWriter(template="default", minify=False)
```

✅ **Good Example:**
```python
def create_writer(output_type: str, **kwargs: Any) -> ReportWriter:
    """Factory for report writers."""
    writers = {
        "json": lambda: JsonWriter(indent=kwargs.get("indent", 2)),
        "text": lambda: TextWriter(width=kwargs.get("width", 80)),
        "html": lambda: HtmlWriter(template=kwargs.get("template", "default")),
    }
    if output_type not in writers:
        raise ValueError(f"Unknown output type: {output_type!r}")
    return writers[output_type]()
```

**Preferred Alternative:** For simple cases, a dict mapping names to classes is sufficient. For complex creation, use a dedicated factory function.

---

## 20. Anti-Patterns

### ANTI-01: No God Objects

**Why:** A class that knows about everything and does everything becomes the bottleneck for all changes. Every modification risks breaking unrelated functionality. God objects are untestable, unmaintainable, and unkillable.

❌ **Bad Example:**
```python
class Application:
    def __init__(self):
        self.db = Database()
        self.cache = Cache()
        self.mailer = Mailer()
        self.scanner = Scanner()
        self.reporter = Reporter()
        self.scheduler = Scheduler()

    def scan(self): ...
    def report(self): ...
    def notify(self): ...
    def schedule(self): ...
    def clear_cache(self): ...
    def migrate_db(self): ...
```

✅ **Good Example:** Decompose into focused classes connected by dependency injection (see §17, §18).

**Preferred Alternative:** If a class has more than 5 dependencies or 10 public methods, it is likely a God object. Split it.

---

### ANTI-02: No Premature Abstraction (YAGNI)

**Why:** Abstractions added "in case we need them later" are wrong 80% of the time. They add complexity, indirection, and maintenance burden for a future that may never arrive. Abstraction should emerge from concrete usage, not precede it.

❌ **Bad Example:**
```python
class AbstractScannerFactory(ABC):
    """We might need different scanner factories someday."""
    @abstractmethod
    def create_scanner(self) -> AbstractScanner: ...

class AbstractScanner(ABC):
    """We might need different scanners someday."""
    @abstractmethod
    def scan(self) -> AbstractResult: ...

class AbstractResult(ABC):
    """We might need different result types someday."""
    ...

# One concrete implementation. The abstractions serve nothing.
class ConcreteScanner(AbstractScanner): ...
```

✅ **Good Example:**
```python
class SecurityScanner:
    """One scanner. Concrete. Testable. Done."""
    async def scan(self, url: str) -> ScanReport: ...
```

**Preferred Alternative:** Write concrete code first. Extract abstractions when you have 2+ concrete implementations that share a pattern.

---

### ANTI-03: No `utils.py` / `helpers.py` Dumping Grounds

**Why:** `utils.py` is where code goes to hide. It grows indefinitely because "where should I put this?" defaults to "utils." It violates SRP by containing unrelated functions and creates a hidden dependency magnet.

❌ **Bad Example:**
```python
# utils.py — 800 lines of unrelated functions
def validate_url(url): ...
def format_bytes(n): ...
def send_email(to, subject, body): ...
def calculate_hash(data): ...
def retry(func, max_retries=3): ...
def parse_date(date_str): ...
def sanitize_html(html): ...
```

✅ **Good Example:**
```python
# validators.py
def validate_url(url: str) -> str: ...
def validate_email(email: str) -> str: ...

# formatters.py
def format_bytes(n: int) -> str: ...
def format_duration(seconds: float) -> str: ...

# retry.py
def retry(func: Callable, max_retries: int = 3): ...
```

**Preferred Alternative:** Name files by responsibility. If you can't name it better than "utils," the functions probably belong in different modules.

---

## 21. Python Idioms

### IDOM-01: Use Context Managers for Resource Lifecycle

**Why:** Context managers guarantee cleanup even when exceptions occur. `with open(path) as f:` ensures the file is closed whether the block succeeds or raises. Manual `try/finally` is verbose and error-prone.

❌ **Bad Example:**
```python
f = open("report.json", "w")
f.write(json.dumps(data))
f.close()  # Never reached if write() raises

client = httpx.AsyncClient()
response = await client.get(url)
# client.aclose() — forgotten, connection leaks
```

✅ **Good Example:**
```python
with open("report.json", "w") as f:
    f.write(json.dumps(data))

async with httpx.AsyncClient() as client:
    response = await client.get(url)
```

**Preferred Alternative:** For custom resources, implement `__enter__`/`__exit__` or use `@contextmanager`.

---

### IDOM-02: Use Comprehensions for Simple Transformations

**Why:** List/dict/set comprehensions are more concise, often faster (optimized at C level in CPython), and signal "this is a transformation" rather than "this is imperative logic." But only for simple, single-level operations.

❌ **Bad Example:**
```python
result = []
for item in items:
    if item.is_active:
        result.append(item.name.upper())
```

✅ **Good Example:**
```python
active_names = [item.name.upper() for item in items if item.is_active]
```

**Preferred Alternative:** If the comprehension exceeds one line or has nested logic, use an explicit loop or extract a function. Readability beats brevity.

---

### IDOM-03: Use `enumerate()` Instead of Manual Index Tracking

**Why:** Manual index tracking (`i = 0; i += 1`) is error-prone and adds noise. `enumerate()` is the Pythonic way to get both index and value, and clearly signals intent.

❌ **Bad Example:**
```python
i = 0
for item in items:
    print(f"{i}: {item}")
    i += 1
```

✅ **Good Example:**
```python
for index, item in enumerate(items):
    print(f"{index}: {item}")
```

**Preferred Alternative:** Use `enumerate(items, start=1)` when 1-based indexing is needed.

---

### IDOM-04: Use `zip()` for Parallel Iteration

**Why:** `zip()` pairs elements from multiple iterables cleanly. Manual indexing (`items_a[i]`, `items_b[i]`) is fragile and IndexError-prone.

❌ **Bad Example:**
```python
for i in range(len(names)):
    print(f"{names[i]}: {scores[i]}")
```

✅ **Good Example:**
```python
for name, score in zip(names, scores, strict=True):
    print(f"{name}: {score}")
```

**Preferred Alternative:** Use `strict=True` (Python 3.10+) to catch length mismatches. Use `itertools.zip_longest()` when lengths may differ intentionally.

---

### IDOM-05: Use Unpacking for Readable Assignments

**Why:** Tuple unpacking is a core Python idiom. It makes multi-value returns readable and avoids index-based access.

❌ **Bad Example:**
```python
result = get_scan_summary()
total = result[0]
passed = result[1]
failed = result[2]
```

✅ **Good Example:**
```python
total, passed, failed = get_scan_summary()
```

**Preferred Alternative:** For functions returning more than 3 values, return a `dataclass` or `NamedTuple` instead of a plain tuple.

---

## 22. Code Smells

### SMELL-01: Feature Envy — Method Uses Another Object's Data More Than Its Own

**Why:** If a method primarily accesses another object's attributes, the logic probably belongs in that other object. Feature envy creates coupling and violates encapsulation.

❌ **Bad Example:**
```python
class ReportGenerator:
    def calculate_risk(self, scan: ScanResult) -> float:
        critical = len([f for f in scan.findings if f.severity == "critical"])
        high = len([f for f in scan.findings if f.severity == "high"])
        return (critical * 10 + high * 5) / scan.total_checks
```

✅ **Good Example:**
```python
class ScanResult:
    def calculate_risk_score(self) -> float:
        critical = sum(1 for f in self.findings if f.severity == Severity.CRITICAL)
        high = sum(1 for f in self.findings if f.severity == Severity.HIGH)
        return (critical * 10 + high * 5) / self.total_checks
```

**Preferred Alternative:** Move the method to the class whose data it primarily uses.

---

### SMELL-02: Long Parameter Lists

**Why:** More than 5 parameters make a function hard to call, hard to remember, and hard to test. Long parameter lists indicate the function does too much or needs a parameter object.

❌ **Bad Example:**
```python
def create_report(title, author, date, findings, format, template,
                  include_summary, include_charts, output_path, compress):
    ...
```

✅ **Good Example:**
```python
@dataclass(frozen=True)
class ReportOptions:
    format: str = "json"
    template: str = "default"
    include_summary: bool = True
    include_charts: bool = False
    compress: bool = False

def create_report(
    title: str,
    findings: list[Finding],
    options: ReportOptions = ReportOptions(),
) -> Report:
    ...
```

**Preferred Alternative:** Group related parameters into a dataclass or Pydantic model.

---

### SMELL-03: Shotgun Surgery — One Change Requires Edits in Many Files

**Why:** If adding a new severity level requires changes in 8 files (model, analyzer, reporter, formatter, CLI, tests, docs, config), the responsibility is scattered. Changes should be localized.

❌ **Bad Example:**
```
Adding "INFORMATIONAL" severity requires changes in:
  models.py       — add to list
  analyzer.py     — add case
  reporter.py     — add color
  cli.py          — add filter
  formatter.py    — add template
  constants.py    — add weight
  tests/          — update 6 test files
```

✅ **Good Example:**
```python
class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    # Adding a new member here is the ONLY change needed.
    # All display, filtering, and sorting derive from the Enum.

    @property
    def weight(self) -> int:
        weights = {self.CRITICAL: 10, self.HIGH: 5, self.MEDIUM: 3, self.LOW: 1, self.INFO: 0}
        return weights[self]

    @property
    def color(self) -> str:
        colors = {self.CRITICAL: "red", self.HIGH: "orange", ...}
        return colors[self]
```

**Preferred Alternative:** Co-locate related data and behavior. If adding a value requires changing multiple files, refactor to centralize.

---

### SMELL-04: Primitive Obsession — Using Strings Where Domain Types Belong

**Why:** Passing `url: str` means any string is accepted — `"hello"`, `""`, `"not-a-url"`. A `Url` type with validation catches errors at construction time, not deep inside business logic.

❌ **Bad Example:**
```python
def scan(url: str, severity: str, format: str) -> dict:
    ...

scan("not-a-url", "HIGHH", "jsson")  # Three bugs, zero type errors
```

✅ **Good Example:**
```python
def scan(target: ValidatedUrl, min_severity: Severity, output_format: OutputFormat) -> ScanReport:
    ...

scan(ValidatedUrl("not-a-url"), ...)  # ValidationError at construction!
```

**Preferred Alternative:** Create thin wrapper types (`ValidatedUrl`, `EmailAddress`) for strings that represent domain concepts with validation rules.

---

## 23. Refactoring Rules

### REF-01: Extract When You Repeat

**Why:** Duplicated code means duplicated bugs. When the same logic appears twice, extract it into a function. The function name documents the intent, and future fixes apply once.

❌ **Bad Example:**
```python
# In scanner.py
if not url.startswith("http://") and not url.startswith("https://"):
    raise ValueError(f"Invalid URL scheme: {url}")

# In batch_scanner.py (copy-pasted)
if not url.startswith("http://") and not url.startswith("https://"):
    raise ValueError(f"Invalid URL scheme: {url}")
```

✅ **Good Example:**
```python
# In validators.py
def validate_url_scheme(url: str) -> None:
    """Ensure URL uses HTTP or HTTPS scheme."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError(f"Unsupported URL scheme: {parsed.scheme!r}")
```

**Preferred Alternative:** The Rule of Three — if you see the same logic three times, it's time to extract. Twice is a judgment call.

---

### REF-02: Flatten Deeply Nested Code with Guard Clauses

**Why:** Every nesting level doubles the cognitive load. Guard clauses (early returns) eliminate nesting by handling special cases first, leaving the main logic at the top indentation level.

❌ **Bad Example:**
```python
def process_finding(finding):
    if finding is not None:
        if finding.severity != Severity.INFO:
            if finding.is_confirmed:
                if finding.url not in excluded_urls:
                    report.add(finding)
                    return True
    return False
```

✅ **Good Example:**
```python
def process_finding(finding: Finding | None) -> bool:
    if finding is None:
        return False
    if finding.severity == Severity.INFO:
        return False
    if not finding.is_confirmed:
        return False
    if finding.url in excluded_urls:
        return False

    report.add(finding)
    return True
```

**Preferred Alternative:** Each guard clause is a documented reason to skip processing. The reader understands the preconditions from top to bottom.

---

### REF-03: Replace Conditional Chains with Dispatch Tables

**Why:** Long `if/elif/elif` chains are hard to extend, easy to get wrong, and violate the Open/Closed Principle. A dispatch table (dict mapping) is O(1), extensible, and self-documenting.

❌ **Bad Example:**
```python
def get_analyzer(check_type: str) -> Analyzer:
    if check_type == "headers":
        return HeaderAnalyzer()
    elif check_type == "tls":
        return TLSAnalyzer()
    elif check_type == "cookies":
        return CookieAnalyzer()
    elif check_type == "dns":
        return DNSAnalyzer()
    else:
        raise ValueError(f"Unknown check type: {check_type}")
```

✅ **Good Example:**
```python
ANALYZERS: dict[str, type[Analyzer]] = {
    "headers": HeaderAnalyzer,
    "tls": TLSAnalyzer,
    "cookies": CookieAnalyzer,
    "dns": DNSAnalyzer,
}

def get_analyzer(check_type: str) -> Analyzer:
    analyzer_class = ANALYZERS.get(check_type)
    if analyzer_class is None:
        raise ValueError(f"Unknown check type: {check_type!r}. Available: {', '.join(ANALYZERS)}")
    return analyzer_class()
```

**Preferred Alternative:** Adding a new analyzer is now one line: `"cors": CORSAnalyzer,`. No structural change needed.

---

### REF-04: Replace Mutable Default Arguments

**Why:** Mutable default arguments (`list`, `dict`, `set`) are shared across all calls. Appending to a default list in one call mutates it for all future calls. This is one of Python's most notorious gotchas.

❌ **Bad Example:**
```python
def add_finding(findings: list[Finding] = []) -> list[Finding]:
    findings.append(new_finding)
    return findings

# First call returns [finding1]
# Second call returns [finding1, finding2] — default was mutated!
```

✅ **Good Example:**
```python
def add_finding(findings: list[Finding] | None = None) -> list[Finding]:
    if findings is None:
        findings = []
    findings.append(new_finding)
    return findings
```

**Preferred Alternative:** The `None` sentinel pattern is canonical Python. Apply it to every `list`, `dict`, and `set` default parameter.

---

### REF-05: Replace Nested Dictionary Access with Data Classes

**Why:** Nested dict access (`data["user"]["address"]["city"]`) is fragile, untyped, and produces `KeyError` at runtime. A dataclass tree provides autocompletion, type checking, and attribute access.

❌ **Bad Example:**
```python
config = {
    "scan": {
        "timeout": 30,
        "retries": 3,
        "headers": {
            "user_agent": "Scanner/1.0"
        }
    }
}

timeout = config["scan"]["timeout"]
ua = config["scan"]["headers"]["user_agent"]  # KeyError if typo
```

✅ **Good Example:**
```python
@dataclass(frozen=True)
class HeaderConfig:
    user_agent: str = "Scanner/1.0"

@dataclass(frozen=True)
class ScanConfig:
    timeout: float = 30.0
    retries: int = 3
    headers: HeaderConfig = field(default_factory=HeaderConfig)

config = ScanConfig()
timeout = config.timeout                # Typed, IDE-supported
ua = config.headers.user_agent          # No KeyError possible
```

**Preferred Alternative:** Use `pydantic.BaseModel` when parsing from external sources (JSON, YAML, env vars). Use `dataclass` for internal structured data.

---

### REF-06: Extract Complex Boolean Expressions

**Why:** Complex boolean expressions are hard to read, harder to debug, and impossible to name. Extracting them into named variables turns opaque logic into readable documentation.

❌ **Bad Example:**
```python
if (response.status_code == 200 and
    "text/html" in response.headers.get("content-type", "") and
    len(response.content) > 0 and
    not response.is_redirect and
    response.elapsed.total_seconds() < timeout):
    process(response)
```

✅ **Good Example:**
```python
is_successful = response.status_code == 200
is_html = "text/html" in response.headers.get("content-type", "")
has_content = len(response.content) > 0
is_direct = not response.is_redirect
is_within_timeout = response.elapsed.total_seconds() < timeout

if is_successful and is_html and has_content and is_direct and is_within_timeout:
    process(response)
```

**Preferred Alternative:** Each boolean variable serves as inline documentation. When one condition fails, the debugger shows exactly which one.

---

### REF-07: Replace Comments with Descriptive Code

**Why:** If code needs a comment to explain what it does, the code is too complex. Refactoring the code to be self-explanatory is better than leaving a comment that may become stale.

❌ **Bad Example:**
```python
# Check if user can access the resource
if user.role in ("admin", "editor") and not user.is_suspended and resource.is_published:
    allow_access()
```

✅ **Good Example:**
```python
def has_edit_permission(user: User) -> bool:
    return user.role in (Role.ADMIN, Role.EDITOR) and not user.is_suspended

def is_accessible(resource: Resource) -> bool:
    return resource.is_published

if has_edit_permission(user) and is_accessible(resource):
    allow_access()
```

**Preferred Alternative:** Extract logic into well-named functions. The function name replaces the comment and is guaranteed to stay in sync with the logic.

---

## Appendix A — Quick Reference Card

| Category | Key Rule | Shorthand |
|---|---|---|
| **Naming** | Variables describe content | `user_count` not `x` |
| **Imports** | Group: stdlib → third-party → local | `ruff` enforces |
| **Folders** | Mirror architecture layers | `core/` `infra/` `config/` |
| **Modules** | One responsibility per module | No `utils.py` |
| **Functions** | ≤ 40 lines, ≤ 5 params, ≤ 3 nesting | Extract early |
| **Classes** | Small, focused, composed | Inject dependencies |
| **Comments** | Explain WHY, not WHAT | Or refactor instead |
| **Docstrings** | All public functions, Google style | Keep accurate |
| **Logging** | `logging.getLogger(__name__)` | Never `print()` |
| **Exceptions** | Specific types, never bare `except:` | Chain with `from` |
| **Types** | Full annotations, `mypy --strict` | `str \| None` syntax |
| **Dataclasses** | `@dataclass(frozen=True)` for value objects | Not plain dicts |
| **Enums** | `class Severity(str, Enum)` | Not string literals |
| **Config** | `pydantic-settings`, validate at startup | Not raw `os.getenv` |
| **Constants** | `UPPER_SNAKE_CASE`, `Final` typed | Not magic numbers |
| **DI** | Constructor injection | No hidden `__init__` deps |
| **Composition** | Assemble from small components | Not God objects |
| **Patterns** | Strategy, Factory when warranted | Not premature |
| **Anti-patterns** | No God objects, no `utils.py`, no YAGNI | Split and name |
| **Idioms** | `with`, comprehensions, `enumerate` | Pythonic = readable |
| **Smells** | Feature envy, long params, shotgun surgery | Refactor signals |
| **Refactoring** | Guard clauses, dispatch tables, extract | Flatten and name |

---

*End of document. These standards apply to all code — human-written and AI-generated — without exception.*
