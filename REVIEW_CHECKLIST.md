# REVIEW_CHECKLIST.md — Production Pull Request Review Standard

> **Classification:** Engineering Review Standard  
> **Version:** 1.0  
> **Applicability:** All pull requests, code reviews, and AI-generated code  
> **Total Items:** 230  
> **Categories:** 23

---

## How to Use This Checklist

### For Human Reviewers
Review each applicable category. Mark items as ✅ Pass, ❌ Fail, or ⊘ N/A. A single ❌ on a Critical item is a blocking finding. All Fail items must be resolved before merge.

### For AI Agents
Evaluate your own code against every applicable item before presenting it. Items marked ❌ must be fixed before delivery. Items marked ⊘ N/A must include a one-line justification.

### Severity Levels

| Severity | Symbol | Meaning | Merge Policy |
|---|---|---|---|
| **Critical** | 🔴 | Security vulnerability, data loss, crash | **Blocks merge.** Must fix immediately. |
| **High** | 🟠 | Bug, incorrect behavior, missing error handling | **Blocks merge.** Must fix before approval. |
| **Medium** | 🟡 | Code smell, suboptimal pattern, missing test | **Should fix.** May merge with tracked follow-up. |
| **Low** | 🟢 | Style, minor improvement, documentation gap | **Nice to fix.** Does not block merge. |

### Review Summary Template

```
## PR Review Summary

Reviewer:       [Name / Agent ID]
Date:           [YYYY-MM-DD]
PR:             [#number or description]
Verdict:        APPROVE / REQUEST CHANGES / REJECT

| Category          | Pass | Fail | N/A | Blockers |
|-------------------|------|------|-----|----------|
| Architecture      |      |      |     |          |
| Security          |      |      |     |          |
| ...               |      |      |     |          |
| TOTALS            |      |      |     |          |
```

---

## 1. Architecture (12 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| A-01 | 🟠 | Change respects the existing architectural style | New code follows the same patterns (layered, hexagonal, pipeline) as the rest of the codebase | Introduces a different architectural pattern without justification |
| A-02 | 🟠 | Dependency direction is correct | Dependencies flow inward: interface → core ← infrastructure. Core has no outward imports. | Core module imports from infrastructure or interface layer |
| A-03 | 🟠 | No circular dependencies introduced | All import chains are acyclic. No module A → B → A paths. | `import` statements create a cycle between modules |
| A-04 | 🟡 | Single Responsibility Principle followed | Each module, class, and function has one clear reason to change | A class or module handles multiple unrelated concerns |
| A-05 | 🟡 | Module boundaries are respected | Communication between modules happens through defined public interfaces | Module reaches into another module's internals (private attrs, internal functions) |
| A-06 | 🟠 | Public API surface is minimal | Only necessary functions/classes are exported. Internal helpers are private. | Implementation details are exposed as public API |
| A-07 | 🟡 | New files follow existing naming and location conventions | File is placed in the correct directory per project structure. Name follows existing patterns. | File placed in wrong directory or uses inconsistent naming |
| A-08 | 🟡 | Design patterns are used appropriately | Patterns solve a real problem. No over-engineering. | Pattern is used preemptively without a concrete need (YAGNI violation) |
| A-09 | 🟠 | Backward compatibility maintained | Existing callers, configs, and tests continue to work without modification | Public function signature, return type, or behavior changed without migration path |
| A-10 | 🟡 | Abstraction level is consistent within each layer | Functions at the same level operate at the same abstraction (all high-level or all low-level) | High-level orchestration mixed with low-level byte manipulation in same function |
| A-11 | 🟡 | No God objects or God functions | No single class handles >3 responsibilities. No function >80 lines. | Monolithic class or function that does everything |
| A-12 | 🟠 | Changes are backward-compatible or breaking changes are documented | Deprecation warnings added. Migration path documented. Version bumped. | Breaking change with no documentation, warning, or version bump |

---

## 2. Security (15 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| S-01 | 🔴 | No hardcoded secrets, tokens, passwords, or API keys | All secrets come from environment variables or secret management. No literals in source. | String literal containing a key, password, token, or connection string |
| S-02 | 🔴 | All external input is validated before processing | Input validated for type, length, range, format, encoding at the boundary | User/network/file input used without validation |
| S-03 | 🔴 | No SQL injection possible | All queries use parameterized statements or ORM methods. No string formatting in SQL. | f-string, `.format()`, `%` operator, or `+` concatenation in SQL query |
| S-04 | 🔴 | No command injection possible | `subprocess.run()` uses argument list. No `shell=True`, `os.system()`, `os.popen()`, `eval()` | User input passed to shell command or `eval`/`exec` |
| S-05 | 🔴 | No SSRF possible | Outbound URLs validated against allowlist. Private IP ranges blocked. DNS resolved before validation. | User-supplied URL used directly for outbound requests without validation |
| S-06 | 🔴 | No directory traversal possible | Paths canonicalized with `Path.resolve()`. Verified within base directory. `..` and null bytes rejected. | User input used in file path without canonicalization and boundary check |
| S-07 | 🔴 | TLS certificates are validated | `verify=True` (or default) on all HTTP clients. No `verify=False` in production code. | `verify=False` without an explicit, documented override flag |
| S-08 | 🟠 | No unsafe deserialization | No `pickle.loads()`, `shelve`, `marshal`, or `yaml.load()` on untrusted data. Uses `json` or `yaml.safe_load()`. | Deserializing untrusted data with an unsafe serializer |
| S-09 | 🟠 | Secrets are never logged | No passwords, tokens, API keys, or session IDs appear in log output at any level | Secret value passed to `logger.*()` call or `print()` |
| S-10 | 🟠 | Error messages do not leak internal details | User-facing errors are generic. No stack traces, file paths, SQL queries, or internal IPs exposed. | Exception message contains `traceback`, internal path, or query text |
| S-11 | 🟠 | Cryptographic operations use standard algorithms | Uses `cryptography`, `hashlib`, `hmac` libraries. AES-256-GCM, SHA-256+, bcrypt/Argon2 for passwords. | Custom crypto, MD5/SHA1 for passwords, ECB mode, hardcoded IVs |
| S-12 | 🟠 | Random tokens use `secrets` module | Tokens, nonces, and security-sensitive random values use `secrets.token_hex()` or equivalent | Using `random` module for security-sensitive values |
| S-13 | 🟡 | Security headers present on HTTP responses | CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy set | Missing security headers on responses |
| S-14 | 🟡 | CORS configuration is restrictive | Specific origins allowlisted. No wildcard `*` in production. | `Access-Control-Allow-Origin: *` in production configuration |
| S-15 | 🟡 | Cookies have secure attributes | `Secure`, `HttpOnly`, `SameSite` attributes set on all cookies | Cookies missing security attributes |

---

## 3. Performance (12 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| P-01 | 🟠 | No N+1 query or request patterns | Batch operations used. No loop issuing individual queries/requests for each item. | Loop that makes one network call per item in a collection |
| P-02 | 🟠 | HTTP clients are reused (connection pooling) | `httpx.AsyncClient` or `requests.Session` created once and reused | New client instance created per request |
| P-03 | 🟠 | No blocking I/O inside async functions | All I/O uses `await`. Blocking calls wrapped in `asyncio.to_thread()`. | `open()`, `time.sleep()`, sync HTTP call inside `async def` |
| P-04 | 🟡 | Algorithm complexity is appropriate for data size | O(n log n) sort, O(1) dict lookup, O(n) scan — matches the expected data volume | O(n²) or worse where O(n log n) is feasible. Nested loops on large datasets. |
| P-05 | 🟡 | Large data processed in streams or batches | Generators, iterators, or chunked reads for files >1MB or collections >10K items | Entire large file or dataset loaded into memory at once |
| P-06 | 🟡 | Timeouts set on all network operations | `timeout=` parameter explicitly set on every HTTP request, socket, and database query | Network call with no timeout (infinite wait possible) |
| P-07 | 🟡 | No redundant computation | Expensive results cached or computed once. No repeated identical calls in loops. | Same expensive function called repeatedly with same arguments |
| P-08 | 🟡 | No unnecessary object creation in hot loops | Objects created outside loops when possible. String concatenation uses `join()` for lists. | Creating objects, compiling regexes, or opening connections inside tight loops |
| P-09 | 🟡 | Appropriate data structures used | `set` for membership testing, `dict` for lookup, `deque` for FIFO, `heapq` for priority | `list` used for membership testing. Linear scan where hash lookup would work. |
| P-10 | 🟡 | File handles closed promptly | Context managers (`with`) used for all file operations | `open()` without `with` block. File handle not closed on exception path. |
| P-11 | 🟢 | Pagination used for large result sets | API responses and database queries use cursor-based or offset pagination | Unbounded query returning potentially millions of rows |
| P-12 | 🟢 | No premature optimization that reduces readability | Code is clear first, fast second. Optimization has profiling evidence. | Micro-optimized code that is hard to read without measured benefit |

---

## 4. Concurrency (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| C-01 | 🔴 | No race conditions on shared mutable state | Shared state protected by `asyncio.Lock`, `threading.Lock`, or atomic operations | Multiple coroutines/threads read-modify-write shared data without synchronization |
| C-02 | 🟠 | `asyncio.gather()` results inspected for exceptions | When `return_exceptions=True`, each result is checked for exception instances | Gathered results used without checking for embedded exceptions |
| C-03 | 🟠 | Concurrency is bounded by semaphore or pool | `asyncio.Semaphore` or `ThreadPoolExecutor(max_workers=N)` limits concurrent operations | Unbounded `asyncio.gather()` launching thousands of concurrent tasks |
| C-04 | 🟠 | `asyncio.CancelledError` handled correctly | Cancellation triggers resource cleanup, then re-raises (not swallowed) | `CancelledError` caught and suppressed, preventing proper shutdown |
| C-05 | 🟠 | Deadlocks are impossible | Lock acquisition order is consistent. No nested lock acquisition. Timeouts on lock waits. | Two locks acquired in different orders in different code paths |
| C-06 | 🟡 | Correct concurrency model selected | `asyncio` for I/O-bound. `multiprocessing` for CPU-bound. `threading` only when appropriate. | CPU-bound work in asyncio. I/O-bound work in multiprocessing. |
| C-07 | 🟡 | Task cancellation propagates correctly | Parent task cancellation cancels child tasks. Cleanup runs. | Orphaned tasks continue running after parent is cancelled |
| C-08 | 🟡 | No thread-unsafe operations in async context | No global mutable state accessed from multiple coroutines without protection | Module-level mutable dict/list modified by concurrent coroutines |
| C-09 | 🟡 | Concurrent writes are serialized | File writes, database writes, and log writes are thread/task-safe | Multiple coroutines writing to same file without locking |
| C-10 | 🟢 | Background tasks are tracked and awaited | All spawned tasks are stored and awaited or cancelled at shutdown | Fire-and-forget `asyncio.create_task()` with no reference kept |

---

## 5. Memory (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| M-01 | 🟠 | No unbounded memory growth | Collections have maximum size. Caches have TTL and eviction. Buffers are bounded. | List grows indefinitely. Cache never evicts. Buffer has no size limit. |
| M-02 | 🟠 | Large datasets use generators or iterators | Data processed lazily with `yield`, `iter()`, or streaming APIs | Entire dataset materialized into a list when only iteration is needed |
| M-03 | 🟡 | References to large objects released when no longer needed | Variables holding large objects set to `None` or go out of scope after use | Large response body or file content held in memory for the entire program lifetime |
| M-04 | 🟡 | No accidental deep copies of large structures | `copy.deepcopy()` not used on large objects. Shared references used intentionally. | Deep-copying a 100MB data structure in a loop |
| M-05 | 🟡 | String building uses efficient patterns | `str.join()` for building from lists. `io.StringIO` for incremental building. | String concatenation with `+=` in a loop (O(n²) memory allocation) |
| M-06 | 🟡 | `__slots__` considered for high-volume data classes | Hot-path objects with thousands of instances use `__slots__` to reduce memory | N/A for most code. Fail only when profiling shows dict overhead is significant. |
| M-07 | 🟢 | Streaming used for large HTTP responses | `response.stream()` or equivalent for responses >10MB | Downloading entire large response body into memory with `.read()` |
| M-08 | 🟢 | No reference cycles preventing garbage collection | Weak references or explicit cleanup for bidirectional object relationships | Object A references B references A, preventing GC without explicit cycle breaking |

---

## 6. Error Handling (12 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| E-01 | 🔴 | No bare `except:` clauses | Every `except` names a specific exception type | `except:` or `except BaseException:` without re-raise |
| E-02 | 🔴 | No exceptions silently swallowed | Every `except` block logs, re-raises, or returns a meaningful error | `except SomeError: pass` — exception caught and ignored |
| E-03 | 🟠 | Exception types are specific and narrow | Catches `httpx.TimeoutException`, not `Exception`. Catches `KeyError`, not `BaseException`. | `except Exception` used as a catch-all instead of specific types |
| E-04 | 🟠 | Error messages include sufficient context | Exception includes: what failed, what input caused it, what operation was attempted | Error message is generic: `"An error occurred"` with no context |
| E-05 | 🟠 | Custom exceptions used for domain errors | Project defines exception hierarchy. Domain errors use domain exceptions. | Using `ValueError` or `RuntimeError` for domain-specific error conditions |
| E-06 | 🟠 | Exception chaining preserves cause | `raise NewError(...) from original_exception` used to preserve stack trace | Original exception discarded: `raise NewError(...)` without `from` |
| E-07 | 🟠 | Network errors handled per error type | Timeout, DNS, connection, SSL, HTTP status errors each have specific handling | Single `except Exception` around all network operations |
| E-08 | 🟡 | Retry logic uses exponential backoff with jitter | Retries use increasing delays (1s, 2s, 4s) with random jitter | Fixed-interval retries or no backoff (retry storms under load) |
| E-09 | 🟡 | Only idempotent operations are retried | POST/create operations not retried blindly. Idempotency key used where needed. | Non-idempotent operation retried, potentially causing duplicates |
| E-10 | 🟡 | Graceful degradation on partial failure | When one component fails, system returns partial results with clear indication | Entire operation fails because one sub-component raised an exception |
| E-11 | 🟡 | `finally` blocks or context managers ensure cleanup | Resources released even when exceptions occur. No cleanup code after `try` block. | Resource cleanup code placed after try/except, skipped if unexpected exception |
| E-12 | 🟢 | Error responses use consistent format | All errors follow the same structure: code, message, details, timestamp | Different error formats in different parts of the application |

---

## 7. Logging (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| L-01 | 🟠 | No `print()` statements for diagnostics | All diagnostic output uses `logging` module | `print()` used for debugging, status, or error output |
| L-02 | 🔴 | No secrets logged at any level | Passwords, tokens, API keys, session IDs never appear in log output | Secret value passed to any `logger.*()` call, even at `DEBUG` |
| L-03 | 🟡 | Lazy formatting used in log calls | `logger.info("msg %s", val)` — not `logger.info(f"msg {val}")` | f-string or `.format()` in logging call (evaluates regardless of level) |
| L-04 | 🟡 | Appropriate log level used | DEBUG for diagnostics, INFO for events, WARNING for recoverable issues, ERROR for failures | INFO used for debug details. ERROR used for warnings. Level mismatch. |
| L-05 | 🟡 | Named loggers used per module | `logger = logging.getLogger(__name__)` in each module | Single root logger used everywhere. Logger name doesn't match module. |
| L-06 | 🟡 | Logging configured once at startup | `logging.basicConfig()` or equivalent called in entry point only | Logging configured in library modules or reconfigured in multiple places |
| L-07 | 🟡 | Log messages include correlation context | Request ID, target URL, operation name included where applicable | Log message has no identifying context: `"Request failed"` (which request?) |
| L-08 | 🟡 | Operation timing logged for performance-critical paths | `logger.info("Scan completed in %.2fs", duration)` for measurable operations | No timing information in logs for operations with performance requirements |
| L-09 | 🟢 | Log output destination is correct | Logs to stderr (not stdout). Stdout reserved for application output. | Logs mixed with application output on stdout |
| L-10 | 🟢 | Log level configurable at runtime | Log level settable via environment variable or configuration | Log level hardcoded, not changeable without code modification |

---

## 8. Testing (12 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| T-01 | 🟠 | Tests exist for all new/modified public functions | Every public function has at least one test | Public function added or modified with no corresponding test |
| T-02 | 🟠 | Happy path tested | At least one test verifies correct behavior with valid input | No test for the expected normal use case |
| T-03 | 🟠 | Error paths tested | At least one test per expected exception or error condition | Error handling code exists but is never exercised by tests |
| T-04 | 🟡 | Edge cases tested | Empty input, None, zero, negative, maximum, unicode, special characters | No tests for boundary conditions or unusual inputs |
| T-05 | 🟡 | Tests are independent and isolated | Each test can run alone. No shared mutable state. No test ordering dependency. | Test B fails if Test A doesn't run first. Tests share a mutable fixture. |
| T-06 | 🟡 | Tests are deterministic | No flaky tests. Time, randomness, and network are mocked. | Test passes intermittently. Uses `time.time()` or real network calls. |
| T-07 | 🟡 | Test names are descriptive | `test_parse_url_with_missing_scheme_raises_value_error` | `test_1`, `test_parse`, `test_it_works` |
| T-08 | 🟡 | Arrange-Act-Assert structure followed | Setup, execution, and verification are clearly separated | Test is a wall of interleaved setup, calls, and asserts |
| T-09 | 🟡 | Mocks are scoped appropriately | Mock at architectural boundaries (network, filesystem). Mock scope is narrow. | Mocking the function under test. Over-mocking internals. |
| T-10 | 🟡 | Test file structure mirrors source structure | `src/core/analyzer.py` → `tests/unit/core/test_analyzer.py` | Tests in flat directory or unrelated structure |
| T-11 | 🟢 | Fixtures are shared via conftest.py | Common fixtures in `conftest.py` with appropriate scope | Duplicated fixture code across multiple test files |
| T-12 | 🟢 | Coverage meets minimum threshold | Line coverage ≥ project-defined minimum (typically 80% for core) | Coverage below threshold without justification |

---

## 9. Naming (9 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| N-01 | 🟡 | Variables describe what they hold | `scan_results`, `target_url`, `retry_count` | `x`, `tmp`, `data`, `result`, `val`, `thing` |
| N-02 | 🟡 | Functions describe what they do | `fetch_security_headers`, `validate_url`, `calculate_risk_score` | `do_stuff`, `process`, `handle`, `run`, `execute` (without context) |
| N-03 | 🟡 | Boolean variables/parameters read as questions | `is_valid`, `has_findings`, `should_retry`, `can_connect` | `valid`, `flag`, `check`, `status` (ambiguous) |
| N-04 | 🟡 | Classes use PascalCase nouns | `SecurityScanner`, `ScanReport`, `HeaderAnalyzer` | `scanner_class`, `RunScan`, `HEADER_ANALYZER` |
| N-05 | 🟡 | Constants use UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT`, `HTTP_STATUS_OK` | `maxRetries`, `default_timeout`, `httpStatusOk` |
| N-06 | 🟡 | No abbreviations unless universally understood | `url`, `http`, `json`, `csv`, `html` are OK. `usr`, `mgr`, `cnt`, `hdr` are not. | Abbreviation that requires domain knowledge to decode |
| N-07 | 🟡 | Naming is consistent across the codebase | If one module uses `fetch_`, all modules use `fetch_` (not `get_` and `retrieve_`) | Mixed naming conventions for the same concept |
| N-08 | 🟢 | Private members have leading underscore | `_internal_method`, `_cache`, `_parse_header` | Internal method/attribute without underscore exposed as public |
| N-09 | 🟢 | No shadowing of built-in names | No variables named `id`, `type`, `list`, `dict`, `input`, `open`, `format`, `hash` | Local variable shadows a Python built-in |

---

## 10. Style (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| ST-01 | 🟡 | Consistent formatting throughout change | Code passes `ruff format` or project formatter with zero changes | Inconsistent indentation, spacing, or line breaks |
| ST-02 | 🟡 | Import organization follows convention | stdlib → third-party → local. Alphabetized within groups. No unused imports. | Random import ordering. Unused imports present. |
| ST-03 | 🟡 | Line length within project limit | All lines ≤ configured limit (79, 88, 99, or 120 chars) | Lines exceeding limit without functional necessity |
| ST-04 | 🟡 | Consistent string quoting | All strings use same quote style (single or double) per project convention | Mixed `'single'` and `"double"` quotes without pattern |
| ST-05 | 🟢 | Trailing whitespace removed | No trailing spaces or tabs on any line | Trailing whitespace present |
| ST-06 | 🟢 | File ends with single newline | Every file ends with exactly one newline character | File ends with no newline or multiple blank lines |
| ST-07 | 🟢 | No commented-out code | All lines are active code, comments, or documentation | Blocks of code commented out with `#` |
| ST-08 | 🟢 | Consistent blank line usage | Two blank lines between top-level definitions. One between methods. Per PEP 8. | Inconsistent spacing between functions and classes |

---

## 11. Readability (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| R-01 | 🟡 | Functions are ≤ 40 lines | Each function fits on one screen. Single responsibility. | Function exceeds 40 lines of logic (not counting docstring) |
| R-02 | 🟡 | Nesting depth ≤ 3 levels | Maximum 3 levels of indentation within a function | Deeply nested if/for/try blocks requiring horizontal scrolling |
| R-03 | 🟡 | Early returns used for guard clauses | Error conditions and preconditions handled at the top, then proceed to main logic | Deep nesting from `if valid: if not empty: if has_permission:` chains |
| R-04 | 🟡 | Complex conditions extracted to named variables | `is_eligible = age >= 18 and has_consent and not is_banned` | `if age >= 18 and has_consent and not is_banned and score > 50:` inline |
| R-05 | 🟡 | Magic numbers and strings are named constants | `MAX_RETRIES = 3`, `TIMEOUT_SECONDS = 30.0` | Literal `3` or `30.0` appearing without explanation |
| R-06 | 🟡 | Code reads top-to-bottom without jumping | Logic flows sequentially. No need to jump around the file to understand. | Control flow that requires reading the function backwards |
| R-07 | 🟡 | Ternary expressions are simple | `result = value if condition else default` — single level, clear | Nested ternary: `a if x else b if y else c if z else d` |
| R-08 | 🟢 | Comments explain WHY, not WHAT | `# Retry because the API occasionally returns 503 during deployments` | `# Increment counter` above `counter += 1` |
| R-09 | 🟢 | Function parameters ≤ 5 | Functions accept at most 5 parameters. Use dataclass or kwargs for more. | Function with 8+ positional parameters |
| R-10 | 🟢 | List/dict comprehensions are readable | Single-level comprehensions with clear intent. Named generator for complex ones. | Nested comprehension with filtering: `[f(x) for y in z for x in y if g(x)]` |

---

## 12. Maintainability (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| MA-01 | 🟡 | No code duplication (DRY) | Shared logic extracted to helper functions. No copy-pasted blocks. | Same logic appears in 2+ places with minor variations |
| MA-02 | 🟡 | No dead code | Every function, class, variable, and import is used. No unreachable branches. | Unused functions, unreachable `else` branches, imported but unused modules |
| MA-03 | 🟡 | Coupling between modules is minimal | Modules depend on interfaces, not implementations. Changes are local. | Changing one module requires cascading changes across many others |
| MA-04 | 🟡 | Feature flags or configuration used for togglable behavior | Runtime-configurable behavior uses config, not code branches | Feature enabled/disabled by commenting out code or changing constants |
| MA-05 | 🟡 | No technical debt markers without issue tracking | Every TODO/FIXME has a linked issue number: `# TODO(#123): migrate to v2 API` | Bare `TODO` or `FIXME` with no tracking reference |
| MA-06 | 🟡 | Change is isolated and minimal | Only files related to the requirement are modified. No drive-by refactoring. | Unrelated formatting, renaming, or restructuring bundled with functional change |
| MA-07 | 🟡 | Cyclomatic complexity ≤ 10 per function | Each function has ≤ 10 independent paths (if/elif/for/while/except branches) | Function with deeply branching logic requiring a truth table to understand |
| MA-08 | 🟢 | Code is self-documenting | Variable/function names make the code's intent clear without comments | Code requires extensive comments to explain what it does |
| MA-09 | 🟢 | Enums used instead of magic strings | `Severity.HIGH` instead of `"high"`. Enum prevents typos and enables IDE support. | String literals used for state/status values throughout the codebase |
| MA-10 | 🟢 | Consistent error propagation strategy per layer | Exceptions within module, result objects across boundaries, consistent throughout | Mixed strategies: some functions raise, others return None, others return dicts |

---

## 13. Dependencies (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| D-01 | 🟠 | No new dependency added without justification | New dependency has documented reason, alternatives considered, license checked | New package in requirements without explanation |
| D-02 | 🟠 | Dependency versions are pinned | Exact versions in lock file: `httpx==0.27.0`. No unpinned ranges in applications. | Unpinned dependency: `httpx` or `httpx>=0.27` in application requirements |
| D-03 | 🟠 | No known critical CVEs in dependencies | All dependencies checked against advisory databases. No unpatched critical CVEs. | Dependency with known critical vulnerability |
| D-04 | 🟡 | License compatibility verified | All dependency licenses compatible with project license | GPL dependency in an MIT-licensed project |
| D-05 | 🟡 | Existing dependency used over new one | If project already has a library that can do the job, it is used | New dependency added when existing one already covers the need |
| D-06 | 🟡 | Minimal transitive dependency footprint | New dependency doesn't pull in 50+ transitive packages | Massive dependency tree for minor functionality |
| D-07 | 🟢 | Runtime and dev dependencies separated | Test, lint, and build tools are dev dependencies, not runtime | `pytest` in runtime dependencies |
| D-08 | 🟢 | Dependencies support minimum Python version | All dependencies compatible with project's minimum Python version | Dependency requires Python 3.12 when project targets 3.10+ |

---

## 14. Documentation (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| DO-01 | 🟠 | All public functions have docstrings | Every public function includes description, Args, Returns, Raises | Public function without docstring |
| DO-02 | 🟠 | All public classes have docstrings | Class docstring describes purpose, attributes, and usage | Public class without docstring |
| DO-03 | 🟡 | Module-level docstring present | Every `.py` file starts with a docstring describing the module's purpose | Module has no docstring or only a file path comment |
| DO-04 | 🟡 | Docstrings are accurate | Args, Returns, Raises match actual function behavior | Docstring mentions args that don't exist or omits exceptions that are raised |
| DO-05 | 🟡 | Docstring format is consistent | All docstrings follow the same format (Google, NumPy, or reST) | Mixed docstring formats across modules |
| DO-06 | 🟡 | README updated for behavioral changes | New CLI flags, config options, or behaviors reflected in README | Public behavior changed but README shows old information |
| DO-07 | 🟡 | CHANGELOG updated | New features, fixes, and breaking changes documented in CHANGELOG | Merged changes not reflected in CHANGELOG |
| DO-08 | 🟡 | Inline comments explain WHY, not WHAT | Comments provide reasoning for non-obvious decisions | `# set x to 5` — restates the code |
| DO-09 | 🟢 | No commented-out code | Removed code is deleted, not commented. Version control preserves history. | `# old_function()` — commented code left in place |
| DO-10 | 🟢 | Complex algorithms documented | Regex patterns, bitwise operations, and algorithmic trade-offs have explanatory comments | Complex regex or algorithm with no explanation of what it matches or why |

---

## 15. Configuration (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| CF-01 | 🟠 | No hardcoded environment-specific values | URLs, ports, paths, hostnames come from config or env vars | `http://localhost:8080` hardcoded in source |
| CF-02 | 🟠 | Configuration validated at startup | All config values checked for type, range, and format before use | Invalid config causes cryptic error at runtime, not at startup |
| CF-03 | 🟡 | Sensible defaults provided | Every config parameter has a safe, functional default | Parameter with no default that crashes if unset |
| CF-04 | 🟡 | Configuration loading order documented | CLI → env → config file → defaults, clearly documented and implemented | Unclear which source takes precedence |
| CF-05 | 🟡 | `.env.example` kept in sync | All environment variables listed in `.env.example` with descriptions | New env var added to code but missing from `.env.example` |
| CF-06 | 🟡 | Secure defaults for security-related config | `DEBUG=False`, `VERIFY_SSL=True`, `CORS_ORIGINS=[]` as defaults | `DEBUG=True` or `VERIFY_SSL=False` as default |
| CF-07 | 🟢 | Config values are typed | Pydantic, dataclass, or typed parsing for configuration — not raw strings | `os.getenv("PORT")` used as string without type conversion |
| CF-08 | 🟢 | Feature flags are documented | All feature flags listed with description, default, and impact | Undocumented flag that changes behavior silently |

---

## 16. CI/CD (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| CI-01 | 🟠 | All CI checks pass | Lint, type check, tests, and security scan all green | Any CI check failing |
| CI-02 | 🟡 | No CI configuration changes without justification | Pipeline changes are intentional and documented | CI step disabled or removed without explanation |
| CI-03 | 🟡 | Build is reproducible | Same commit produces same artifact every time. Versions pinned. | Build depends on `latest` tags or unpinned network resources |
| CI-04 | 🟡 | Secrets not exposed in CI logs | CI masks secrets. No echo/print of tokens in pipeline scripts. | Secret visible in CI output |
| CI-05 | 🟡 | Test results are reported | CI produces test report artifact. Coverage number visible. | Tests run but results not captured or published |
| CI-06 | 🟢 | Pipeline runs in reasonable time | Full pipeline completes in < 10 minutes for most projects | Pipeline takes 30+ minutes without caching or optimization |
| CI-07 | 🟢 | Cache configured for dependencies | pip/npm cache used to avoid re-downloading dependencies each run | Full dependency download on every pipeline run |
| CI-08 | 🟢 | Branch protection rules in place | PR required. At least one review. CI must pass. No direct push to main. | Direct push to main allowed. No review requirement. |

---

## 17. Python Best Practices (12 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| PY-01 | 🟠 | Context managers used for all resources | `with open(...)`, `async with client`, `with lock` for every resource | Resource opened without context manager |
| PY-02 | 🟡 | `pathlib.Path` used for file paths | Path manipulation via `pathlib`. `os.path` only when API requires strings. | `os.path.join()` where `Path(a) / b` would work |
| PY-03 | 🟡 | Mutable default arguments avoided | `def f(items: list[str] | None = None)` with `if items is None: items = []` | `def f(items: list[str] = [])` — shared mutable default |
| PY-04 | 🟡 | `__all__` used to control exports | Public API defined explicitly in `__init__.py` with `__all__` | Everything in module is implicitly public |
| PY-05 | 🟡 | Enum used for fixed value sets | `class Status(Enum)` instead of string constants | `status = "active"` — string literal for a fixed set of values |
| PY-06 | 🟡 | `dataclasses` or `pydantic` used for structured data | Typed data structures instead of plain dicts | `result = {"status": "ok", "count": 5}` returned from function |
| PY-07 | 🟡 | f-strings used for string formatting (non-logging) | `f"Hello {name}"` for general string construction | `"Hello %s" % name` or `"Hello {}".format(name)` for non-logging |
| PY-08 | 🟡 | Walrus operator used appropriately (3.8+) | `if (match := pattern.search(text)) is not None:` for assign-and-test | Walrus in complex expressions reducing readability |
| PY-09 | 🟢 | `functools.lru_cache` used for expensive pure functions | Memoization for deterministic functions called repeatedly with same args | Expensive function called repeatedly without caching |
| PY-10 | 🟢 | Generator expressions preferred over list comprehensions when iteration is sufficient | `sum(x for x in range(n))` instead of `sum([x for x in range(n)])` | List comprehension created only to be iterated once |
| PY-11 | 🟢 | `collections` module used appropriately | `defaultdict`, `Counter`, `namedtuple`, `deque` used where they simplify code | Reinventing defaultdict with `if key not in dict: dict[key] = []` |
| PY-12 | 🟢 | Dunder methods implemented correctly | `__repr__`, `__eq__`, `__hash__` consistent. Frozen dataclasses auto-generate. | `__eq__` without `__hash__`. `__repr__` that doesn't round-trip. |

---

## 18. Async Programming (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| AS-01 | 🔴 | No blocking I/O in async functions | All I/O uses `await`. Blocking calls wrapped in `asyncio.to_thread()`. | `open()`, `requests.get()`, `time.sleep()` in `async def` |
| AS-02 | 🟠 | `httpx.AsyncClient` reused across requests | Client created once with `async with` and passed to functions | New `AsyncClient()` per request or per function call |
| AS-03 | 🟠 | Timeouts set on all async operations | `timeout=` parameter on HTTP calls, `asyncio.wait_for()` for tasks | `await` with no timeout — can hang indefinitely |
| AS-04 | 🟠 | `asyncio.gather()` used for concurrent independent operations | Multiple independent async calls batched with `gather()` | Sequential `await` for operations that have no dependency |
| AS-05 | 🟠 | Semaphore used to limit concurrency | `asyncio.Semaphore(N)` prevents resource exhaustion | Launching 10,000 concurrent connections without limit |
| AS-06 | 🟡 | Event loop not blocked by CPU-intensive work | CPU work offloaded to `ProcessPoolExecutor` or `asyncio.to_thread()` | Long-running computation in async function blocking the event loop |
| AS-07 | 🟡 | Async context managers used correctly | `async with` for async resources. `__aenter__`/`__aexit__` implemented properly. | Sync context manager used where async is needed |
| AS-08 | 🟡 | Async generators handle cleanup | `async for` used with `async def` generators. `finally` blocks clean up. | Async generator abandoned without cleanup |
| AS-09 | 🟢 | `asyncio.run()` called only at entry point | Single `asyncio.run(main())` in `__main__`. No nested event loops. | `asyncio.run()` called inside an already-running loop |
| AS-10 | 🟢 | Async and sync APIs not mixed incorrectly | Clear boundary between async and sync code. No `loop.run_until_complete()` inside async. | Sync wrappers around async code creating nested event loops |

---

## 19. Type Hints (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| TH-01 | 🟠 | All function parameters have type hints | Every parameter annotated: `def f(url: str, timeout: float = 30.0)` | Parameters without type annotations |
| TH-02 | 🟠 | All return types annotated | Every function has `-> ReturnType`: including `-> None` | Missing return type annotation |
| TH-03 | 🟡 | `Any` is not used without justification | Concrete types, generics, `Protocol`, or `TypeVar` used instead | `Any` used as a lazy escape hatch |
| TH-04 | 🟡 | Modern union syntax used (Python 3.10+) | `str | None` instead of `Optional[str]`. `int | str` instead of `Union[int, str]`. | `Optional[str]` or `Union[int, str]` on Python 3.10+ project |
| TH-05 | 🟡 | Generic types use modern syntax | `list[int]`, `dict[str, Any]`, `tuple[int, ...]` | `List[int]`, `Dict[str, Any]`, `Tuple[int, ...]` on Python 3.10+ |
| TH-06 | 🟡 | Return type matches all code paths | Function declared `-> str` actually returns `str` in every branch | Function returns `str` in one branch, `None` in another, but declared `-> str` |
| TH-07 | 🟡 | Complex types are aliased for readability | `type Headers = dict[str, str]` or `Headers = dict[str, str]` for complex types | `dict[str, list[tuple[str, int, bool]]]` repeated inline |
| TH-08 | 🟡 | `Protocol` used for structural typing | `Protocol` for duck typing. ABC for inheritance-based polymorphism. | Concrete class type required where any object with the right methods would work |
| TH-09 | 🟢 | `TypeVar` used correctly for generics | Bounded TypeVars where needed. Consistent naming (`T`, `KT`, `VT`). | `TypeVar("T")` used as `Any` substitute |
| TH-10 | 🟢 | `mypy --strict` passes | Code passes strict type checking with zero errors | Type errors suppressed with `# type: ignore` without justification |

---

## 20. Resource Cleanup (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| RC-01 | 🟠 | All files closed after use | `with open(...)` or explicit `f.close()` in `finally` block | File opened without context manager or explicit close |
| RC-02 | 🟠 | All HTTP clients closed after use | `async with httpx.AsyncClient()` or explicit `await client.aclose()` | Client created without close. Connection pool leaked. |
| RC-03 | 🟠 | All database connections returned to pool | Connection released in `finally` or via context manager | Connection acquired but not released on exception path |
| RC-04 | 🟡 | Temporary files cleaned up | `tempfile.NamedTemporaryFile` with `delete=True` or explicit cleanup | Temp files created and never deleted |
| RC-05 | 🟡 | Locks released in all code paths | Lock acquired in `with lock:` or released in `finally` block | Lock acquired, then exception prevents release → deadlock |
| RC-06 | 🟡 | Subprocess processes are waited and cleaned up | `proc.wait()` or `proc.terminate()` called. stdin/stdout/stderr closed. | Subprocess spawned but never waited → zombie process |
| RC-07 | 🟢 | `__del__` not relied upon for cleanup | Deterministic cleanup via context managers or explicit close methods | `__del__` used as the primary cleanup mechanism |
| RC-08 | 🟢 | Signal handlers clean up resources | SIGTERM/SIGINT handlers close connections and flush logs | Application terminated without cleanup on signal |

---

## 21. Edge Cases (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| EC-01 | 🟠 | Empty input handled | Empty string, empty list, empty dict, empty file produce defined behavior | `IndexError`, `KeyError`, or crash on empty input |
| EC-02 | 🟠 | None/null values handled explicitly | `None` checked before use. `Optional` types handled in all branches. | `AttributeError: 'NoneType' has no attribute 'x'` possible |
| EC-03 | 🟡 | Boundary values tested | Zero, one, max_int, min_int, max_length, empty, single-element | Only tested with "happy middle" values |
| EC-04 | 🟡 | Unicode input handled correctly | UTF-8 encoded/decoded explicitly. Non-ASCII characters processed correctly. | `UnicodeDecodeError` on non-ASCII input. Mojibake in output. |
| EC-05 | 🟡 | Very large input handled gracefully | Input above expected size produces a clear error or degrades gracefully | Out of memory, timeout, or crash on large input |
| EC-06 | 🟡 | Concurrent access handled | Shared resources protected. Atomic operations used where needed. | Data corruption when accessed by multiple tasks simultaneously |
| EC-07 | 🟡 | Network unavailability handled | Offline/disconnected state produces clear error message | Unhandled `ConnectionError` or indefinite hang |
| EC-08 | 🟡 | Filesystem permissions handled | Permission denied produces clear error, not stack trace | `PermissionError` propagates as raw exception to user |
| EC-09 | 🟢 | Time zone handling correct | All datetimes are timezone-aware (`datetime.now(tz=UTC)`). No naive datetimes. | Naive `datetime.now()` mixed with timezone-aware datetimes |
| EC-10 | 🟢 | Floating-point comparison correct | `math.isclose()` or epsilon comparison for floats. No `==` for float equality. | `if price == 19.99:` — exact float comparison |

---

## 22. Technical Debt (8 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| TD-01 | 🟡 | No TODO/FIXME/HACK without tracking | Every debt marker has an issue number: `# TODO(#42): optimize query` | Bare `TODO` or `FIXME` with no tracking reference |
| TD-02 | 🟡 | No workarounds without documentation | Workaround has comment explaining: what, why, when it can be removed | Workaround code with no explanation of why it exists |
| TD-03 | 🟡 | No deprecated API usage | Code uses current API versions. No deprecation warnings. | Using `asyncio.get_event_loop()` (deprecated) instead of `asyncio.run()` |
| TD-04 | 🟡 | No copy-pasted code | Duplicated logic extracted to shared function | Same 10-line block appears in 3 files |
| TD-05 | 🟡 | No suppressed warnings without justification | `# noqa`, `# type: ignore`, `# nosec` have inline explanation | Warnings suppressed with no reason given |
| TD-06 | 🟢 | No placeholder implementations | Every function has a real implementation, not `pass` or `return None` | Stub function that does nothing |
| TD-07 | 🟢 | No hardcoded limits that should be configurable | Retry counts, timeouts, batch sizes are configurable, not constants | `for i in range(3):` for retry logic with no way to configure |
| TD-08 | 🟢 | Abstraction level is appropriate | Not over-engineered (YAGNI). Not under-engineered (missing obvious extension points). | Factory-strategy-observer pattern for a 20-line script. Or: monolithic function that will inevitably need splitting. |

---

## 23. Regression Risks (10 Items)

| # | Severity | Item | Pass Criteria | Fail Criteria |
|---|---|---|---|---|
| RR-01 | 🟠 | Existing tests still pass | Full test suite runs green after the change | Existing test failures introduced by the change |
| RR-02 | 🟠 | Public API signatures unchanged (or versioned) | No parameter rename, type change, or removal without deprecation | Callers broken by changed function signature |
| RR-03 | 🟠 | Default behavior preserved | Existing users see no behavior change without opting in | Default value or behavior changed silently |
| RR-04 | 🟡 | Configuration compatibility maintained | Existing config files and env vars still work | New required config parameter breaks existing deployments |
| RR-05 | 🟡 | Import paths unchanged | `from package.module import ClassName` still works | Module renamed or moved without alias |
| RR-06 | 🟡 | Error messages unchanged for machine consumers | Exit codes, error formats, and structured output unchanged | JSON error format changed, breaking downstream parsers |
| RR-07 | 🟡 | Database schema changes are backward-compatible | Additive changes only (new columns with defaults). No column renames or deletions. | Existing data incompatible with new schema |
| RR-08 | 🟡 | Performance not degraded | Benchmark results within 20% of baseline | P95 latency increased by >20% without justification |
| RR-09 | 🟢 | No unintended side effects | Change is isolated to stated scope. No drive-by modifications. | Unrelated functionality altered as side effect |
| RR-10 | 🟢 | Rollback is possible | Change can be reverted cleanly with `git revert`. No one-way migrations. | Data migration that cannot be reversed |

---

## Appendix A — Review Item Summary

| Category | 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | Total |
|---|---|---|---|---|---|
| Architecture | 0 | 5 | 6 | 1 | 12 |
| Security | 7 | 4 | 4 | 0 | 15 |
| Performance | 0 | 3 | 7 | 2 | 12 |
| Concurrency | 1 | 4 | 4 | 1 | 10 |
| Memory | 0 | 2 | 4 | 2 | 8 |
| Error Handling | 2 | 5 | 4 | 1 | 12 |
| Logging | 1 | 1 | 6 | 2 | 10 |
| Testing | 0 | 3 | 7 | 2 | 12 |
| Naming | 0 | 0 | 7 | 2 | 9 |
| Style | 0 | 0 | 4 | 4 | 8 |
| Readability | 0 | 0 | 7 | 3 | 10 |
| Maintainability | 0 | 0 | 7 | 3 | 10 |
| Dependencies | 0 | 3 | 3 | 2 | 8 |
| Documentation | 0 | 2 | 6 | 2 | 10 |
| Configuration | 0 | 2 | 4 | 2 | 8 |
| CI/CD | 0 | 1 | 4 | 3 | 8 |
| Python Best Practices | 0 | 1 | 7 | 4 | 12 |
| Async Programming | 1 | 4 | 3 | 2 | 10 |
| Type Hints | 0 | 2 | 6 | 2 | 10 |
| Resource Cleanup | 0 | 3 | 3 | 2 | 8 |
| Edge Cases | 0 | 2 | 6 | 2 | 10 |
| Technical Debt | 0 | 0 | 5 | 3 | 8 |
| Regression Risks | 0 | 3 | 5 | 2 | 10 |
| **TOTALS** | **12** | **50** | **117** | **51** | **230** |

---

## Appendix B — Minimum Viable Review (Fast Track)

For **trivial changes** (< 20 lines, single file, no architectural impact), use this minimum subset:

| # | Item |
|---|---|
| S-01 | No hardcoded secrets |
| S-02 | All external input validated |
| E-01 | No bare `except:` |
| E-02 | No exceptions silently swallowed |
| L-01 | No `print()` for diagnostics |
| L-02 | No secrets logged |
| T-01 | Tests exist for new/modified functions |
| TH-01 | Function parameters have type hints |
| TH-02 | Return types annotated |
| DO-01 | Public functions have docstrings |
| RR-01 | Existing tests still pass |
| PY-01 | Context managers used for resources |
| AS-01 | No blocking I/O in async functions |
| EC-01 | Empty input handled |
| EC-02 | None/null values handled |

---

## Appendix C — Review Cadence Recommendations

| Change Type | Review Depth | Checklist Scope |
|---|---|---|
| Typo fix, comment update | Skim | Appendix B only |
| Bug fix (< 20 lines) | Focused | Appendix B + relevant category |
| Small feature (1–3 files) | Standard | Full checklist, relevant categories |
| Medium feature (3–10 files) | Thorough | Full checklist, all categories |
| Large feature (10+ files) | Deep | Full checklist + architecture review + performance benchmark |
| Security-related change | Maximum | Full checklist with extra weight on Security (§2) and Edge Cases (§21) |
| Dependency change | Focused | Dependencies (§13) + CI/CD (§16) + Regression (§23) |
| Refactoring | Thorough | Architecture (§1) + Maintainability (§12) + Regression (§23) + Testing (§8) |

---

*End of document. Every item in this checklist is actionable and has objective pass/fail criteria. Use it for every pull request, every code review, and every AI-generated code delivery.*
