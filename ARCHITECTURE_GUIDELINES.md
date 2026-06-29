# ARCHITECTURE_GUIDELINES.md — Software Architecture Handbook

> **Classification:** Engineering Architecture Standard  
> **Version:** 1.0  
> **Applicability:** All projects — greenfield and brownfield  
> **Companion Documents:**  
> - [CODING_STANDARDS.md](./CODING_STANDARDS.md) — Code-level standards  
> - [IMPLEMENTATION_WORKFLOW.md](./IMPLEMENTATION_WORKFLOW.md) — Phase-gated SDLC  
> - [SECURITY_GUIDELINES.md](./SECURITY_GUIDELINES.md) — Security controls

---

## How to Use This Document

This handbook provides architectural guidance for AI coding agents and human engineers making structural decisions. It is organized into three parts:

1. **Architectural Styles** — High-level system organization patterns
2. **Design Patterns** — Reusable solutions to recurring design problems
3. **Engineering Principles** — Universal laws governing software quality

**For AI agents:** Consult this document during Phase 1 (Architecture Design) of the Implementation Workflow. When making structural decisions, reference the Decision Trees (§17) and Trade-off Analysis (§18) sections before committing to an approach.

**Core philosophy:** Architecture is the art of making decisions that are expensive to change later. Every pattern has a cost. Apply patterns only when the problem demands them — never "just in case."

---

## Table of Contents

### Part I — Architectural Styles
1. [Clean Architecture](#1-clean-architecture)
2. [Layered Architecture](#2-layered-architecture)
3. [Hexagonal Architecture](#3-hexagonal-architecture)
4. [Domain-Driven Design (High-Level)](#4-domain-driven-design)

### Part II — Design Patterns
5. [Repository Pattern](#5-repository-pattern)
6. [Factory Pattern](#6-factory-pattern)
7. [Strategy Pattern](#7-strategy-pattern)
8. [Dependency Injection](#8-dependency-injection)

### Part III — Engineering Principles
9. [SOLID Principles](#9-solid-principles)
10. [DRY — Don't Repeat Yourself](#10-dry--dont-repeat-yourself)
11. [KISS — Keep It Simple, Stupid](#11-kiss--keep-it-simple-stupid)
12. [YAGNI — You Aren't Gonna Need It](#12-yagni--you-arent-gonna-need-it)
13. [High Cohesion](#13-high-cohesion)
14. [Low Coupling](#14-low-coupling)
15. [Modularity](#15-modularity)
16. [Scalability & Maintainability](#16-scalability--maintainability)

### Part IV — Decision Framework
17. [Architecture Decision Trees](#17-architecture-decision-trees)
18. [Trade-off Analysis](#18-trade-off-analysis)
19. [When NOT to Use a Pattern](#19-when-not-to-use-a-pattern)
20. [When Simplicity Wins](#20-when-simplicity-wins)
21. [Architecture Review Checklists](#21-architecture-review-checklists)

---

# Part I — Architectural Styles

## 1. Clean Architecture

### What It Is

Clean Architecture, proposed by Robert C. Martin, organizes code into concentric rings where dependencies point **inward**. The innermost ring (Entities/Domain) has zero external dependencies. Each outer ring depends on inner rings, never the reverse.

```
┌─────────────────────────────────────────────────┐
│  Frameworks & Drivers (outermost)               │
│  ┌─────────────────────────────────────────┐    │
│  │  Interface Adapters                      │    │
│  │  ┌─────────────────────────────────┐    │    │
│  │  │  Application / Use Cases         │    │    │
│  │  │  ┌─────────────────────────┐    │    │    │
│  │  │  │  Entities / Domain       │    │    │    │
│  │  │  │  (business rules)        │    │    │    │
│  │  │  └─────────────────────────┘    │    │    │
│  │  └─────────────────────────────────┘    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### The Dependency Rule

> Source code dependencies must point **inward only**. Nothing in an inner ring may reference anything in an outer ring — not a name, a type, a function, or a module.

### Layer Definitions

| Layer | Responsibility | May Import From | Must NOT Import From |
|---|---|---|---|
| **Entities** | Core business objects and rules | Nothing (pure) | Use Cases, Adapters, Frameworks |
| **Use Cases** | Application-specific business logic | Entities | Adapters, Frameworks |
| **Adapters** | Convert data between Use Cases and external systems | Entities, Use Cases | Frameworks (ideally) |
| **Frameworks** | Web server, database driver, HTTP client, CLI | All inner layers | — |

### Python Implementation

```python
# ── entities/ (innermost — no external imports) ──
# entities/models.py
from dataclasses import dataclass
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass(frozen=True)
class Finding:
    title: str
    severity: Severity
    description: str

# ── use_cases/ (imports entities only) ──
# use_cases/analyze_headers.py
from entities.models import Finding, Severity

class AnalyzeHeaders:
    """Use case: analyze HTTP headers for security issues."""

    def execute(self, headers: dict[str, str]) -> list[Finding]:
        findings: list[Finding] = []
        if "strict-transport-security" not in headers:
            findings.append(Finding(
                title="Missing HSTS",
                severity=Severity.HIGH,
                description="Strict-Transport-Security header is absent.",
            ))
        return findings

# ── adapters/ (imports entities + use_cases) ──
# adapters/http_fetcher.py
import httpx
from entities.models import Finding
from use_cases.analyze_headers import AnalyzeHeaders

class HttpHeaderFetcher:
    """Adapter: fetches headers via HTTP and runs use case."""

    def __init__(self, analyzer: AnalyzeHeaders) -> None:
        self._analyzer = analyzer

    async def fetch_and_analyze(self, url: str) -> list[Finding]:
        async with httpx.AsyncClient() as client:
            response = await client.head(url, timeout=30.0)
            return self._analyzer.execute(dict(response.headers))
```

### When to Use

- Projects with complex business rules that must be testable without infrastructure
- Long-lived projects where frameworks may be swapped (e.g., Flask → FastAPI)
- Systems where domain logic must be shared across multiple interfaces (CLI, API, worker)

### When NOT to Use

- **Small scripts or CLI tools** (< 500 lines) — the overhead of 4 layers is unjustified
- **CRUD applications** with no business logic — the "Entities" layer would be empty
- **Prototypes or MVPs** where speed-to-market outweighs architectural purity
- **Data pipelines** where data flows linearly (Pipeline architecture is better)

### Trade-offs

| Benefit | Cost |
|---|---|
| Domain logic testable without infrastructure | More files, more indirection |
| Framework independence | Must write adapters for every external system |
| Clear boundaries | Overhead for simple operations that span layers |
| Forced separation of concerns | Risk of "interface ceremony" (protocols/ABCs for one implementation) |

---

## 2. Layered Architecture

### What It Is

Layered Architecture is the most common and straightforward pattern. Code is organized into horizontal layers where each layer has a specific responsibility and can only depend on the layer directly below it.

```
┌──────────────────────────────┐
│  Presentation / Interface     │  CLI, API endpoints, UI
├──────────────────────────────┤
│  Business Logic / Service     │  Rules, validation, orchestration
├──────────────────────────────┤
│  Data Access / Persistence    │  Database, file I/O, external APIs
└──────────────────────────────┘
```

### Layer Definitions

| Layer | Responsibility | Depends On |
|---|---|---|
| **Interface** | Receive input, format output, route requests | Service layer |
| **Service** | Business rules, orchestration, validation | Data Access layer |
| **Data Access** | Read/write data to/from external systems | External systems (DB, APIs, filesystem) |

### Python Implementation

```python
# ── data_access/ ──
class ScanRepository:
    """Reads and writes scan results to database."""
    async def save(self, result: ScanResult) -> None: ...
    async def get_by_id(self, scan_id: str) -> ScanResult | None: ...

# ── service/ (depends on data_access) ──
class ScanService:
    """Business logic: orchestrate scanning and analysis."""
    def __init__(self, repo: ScanRepository, client: HttpClient) -> None:
        self._repo = repo
        self._client = client

    async def scan_url(self, url: str) -> ScanResult:
        response = await self._client.fetch(url)
        findings = self._analyze(response)
        result = ScanResult(url=url, findings=findings)
        await self._repo.save(result)
        return result

# ── interface/ (depends on service) ──
@app.post("/scan")
async def scan_endpoint(request: ScanRequest, service: ScanService):
    result = await service.scan_url(request.url)
    return ScanResponse.from_result(result)
```

### When to Use

- Most standard applications — it's the safe default
- CRUD applications with moderate business logic
- Teams familiar with traditional n-tier architecture
- Projects where simplicity and convention trump flexibility

### When NOT to Use

- When business logic needs to be tested without any infrastructure
- When the application has no clear "layers" (e.g., event-driven systems)
- When layers become "pass-through" — just forwarding calls without adding value

### Trade-offs

| Benefit | Cost |
|---|---|
| Simple mental model | Strict layering can force unnecessary pass-through layers |
| Well-understood by most developers | Doesn't naturally support multiple interfaces |
| Easy to navigate codebase | Business logic often leaks into interface or data layers |
| Framework conventions align with layers | Changes in data layer can cascade upward |

---

## 3. Hexagonal Architecture

### What It Is

Hexagonal Architecture (Ports and Adapters), proposed by Alistair Cockburn, isolates the application core from external concerns. The core defines **ports** (interfaces) and external systems connect via **adapters**. The core knows nothing about the outside world.

```
                   ┌─────────────────────┐
  HTTP Adapter ──▶ │  PORT (in)           │
                   │                     │
  CLI Adapter  ──▶ │   APPLICATION CORE   │ ──▶ PORT (out) ──▶ DB Adapter
                   │                     │
  Test Adapter ──▶ │   (domain logic)     │ ──▶ PORT (out) ──▶ API Adapter
                   │                     │
                   └─────────────────────┘
```

### Key Concepts

| Concept | Definition |
|---|---|
| **Port** | An interface (Protocol/ABC) that defines how the core communicates with the outside |
| **Adapter** | A concrete implementation of a port for a specific technology |
| **Driving Port** | Input port — how the outside world calls the core (API, CLI) |
| **Driven Port** | Output port — how the core calls the outside world (DB, HTTP, email) |

### Python Implementation

```python
# ── ports/ (interfaces — no implementation) ──
from typing import Protocol

class ScanRepository(Protocol):
    """Driven port: persist and retrieve scan results."""
    async def save(self, result: ScanResult) -> None: ...
    async def get_by_id(self, scan_id: str) -> ScanResult | None: ...

class HttpFetcher(Protocol):
    """Driven port: fetch data from URLs."""
    async def fetch(self, url: str) -> HttpResponse: ...

# ── core/ (depends on ports, NOT adapters) ──
class ScanService:
    """Application core: pure business logic."""
    def __init__(self, fetcher: HttpFetcher, repo: ScanRepository) -> None:
        self._fetcher = fetcher
        self._repo = repo

    async def scan_url(self, url: str) -> ScanResult:
        response = await self._fetcher.fetch(url)
        findings = analyze(response)
        result = ScanResult(url=url, findings=findings)
        await self._repo.save(result)
        return result

# ── adapters/ (implement ports with real technology) ──
class HttpxFetcher:
    """Adapter: implements HttpFetcher using httpx."""
    async def fetch(self, url: str) -> HttpResponse:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            return HttpResponse(status=response.status_code, headers=dict(response.headers))

class PostgresRepository:
    """Adapter: implements ScanRepository using PostgreSQL."""
    async def save(self, result: ScanResult) -> None: ...
    async def get_by_id(self, scan_id: str) -> ScanResult | None: ...

class InMemoryRepository:
    """Adapter: implements ScanRepository for testing."""
    def __init__(self) -> None:
        self._store: dict[str, ScanResult] = {}
    async def save(self, result: ScanResult) -> None:
        self._store[result.id] = result
    async def get_by_id(self, scan_id: str) -> ScanResult | None:
        return self._store.get(scan_id)
```

### When to Use

- Systems that need high testability (swap real adapters for fakes in tests)
- Systems with multiple input channels (API + CLI + worker + scheduled task)
- Projects where external dependencies may change (switching databases, APIs)
- Long-lived systems with high maintainability requirements

### When NOT to Use

- **Simple CRUD apps** — creating ports and adapters for a single DB table is overhead
- **Prototypes** — speed-to-market matters more than architectural purity
- **Projects with one adapter per port** — the abstraction serves nothing if there's only one implementation and no tests that swap it out

### Trade-offs

| Benefit | Cost |
|---|---|
| Core is 100% testable without infrastructure | Every external integration requires a port + adapter |
| Technology-independent core | More files, more interfaces, more indirection |
| Easy to swap implementations | Over-engineering risk for simple projects |
| Clear boundaries | Learning curve for developers unfamiliar with the pattern |

---

## 4. Domain-Driven Design

### What It Is (High-Level)

Domain-Driven Design (DDD), introduced by Eric Evans, is a philosophy that complex software should be structured around the **domain model** — the mental model of the business problem. It provides tactical and strategic patterns for managing complexity.

### Strategic Patterns (Organizational)

| Pattern | Purpose | Example |
|---|---|---|
| **Bounded Context** | Define clear boundaries where a model applies | "Scanning" context vs "Reporting" context |
| **Ubiquitous Language** | Use the same terms in code, docs, and conversation | `Finding`, `Severity`, `Scan`, not `Result`, `Level`, `Job` |
| **Context Map** | Define how bounded contexts interact | Scanning publishes events; Reporting consumes them |

### Tactical Patterns (Code-Level)

| Pattern | Purpose | Example |
|---|---|---|
| **Entity** | Object with identity that persists over time | `User(id=123)` — identity matters, not attributes |
| **Value Object** | Object defined by its attributes, not identity | `Severity.HIGH` — interchangeable with any other HIGH |
| **Aggregate** | Cluster of entities treated as a unit for changes | `ScanReport` contains `Findings`; modified through the root |
| **Repository** | Abstraction for data persistence | `ScanRepository.get_by_id()` |
| **Domain Event** | Record of something significant that happened | `ScanCompleted(scan_id, timestamp, finding_count)` |
| **Domain Service** | Logic that doesn't belong to any single entity | `RiskCalculator.calculate(findings)` |

### Python Implementation

```python
# ── Value Object (frozen, compared by value) ──
@dataclass(frozen=True)
class Severity:
    level: str
    weight: int

    CRITICAL = None  # Defined after class (see below)

Severity.CRITICAL = Severity(level="critical", weight=10)
Severity.HIGH = Severity(level="high", weight=5)

# Better: Use Enum for simple value objects
class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# ── Entity (identity-based equality) ──
@dataclass
class ScanReport:
    id: str                              # Identity
    url: str
    findings: list[Finding]
    created_at: datetime
    status: ScanStatus = ScanStatus.PENDING

    def add_finding(self, finding: Finding) -> None:
        """Business rule: findings can only be added to pending scans."""
        if self.status != ScanStatus.PENDING:
            raise DomainError("Cannot add findings to completed scan")
        self.findings.append(finding)

    def complete(self) -> None:
        """Business rule: scan must have at least one check to complete."""
        if not self.findings:
            raise DomainError("Cannot complete scan with zero findings")
        self.status = ScanStatus.COMPLETED

# ── Domain Event ──
@dataclass(frozen=True)
class ScanCompleted:
    scan_id: str
    finding_count: int
    highest_severity: Severity
    timestamp: datetime
```

### When to Use DDD

- **Complex domains** where business rules are the primary challenge (finance, healthcare, logistics)
- **Large teams** where shared language prevents miscommunication
- **Long-lived systems** where the domain model must evolve safely

### When NOT to Use DDD

- **Simple CRUD applications** — DDD adds massive overhead with no benefit
- **Data-pipeline tools** — the "domain" is data transformation, not business rules
- **Small teams with clear communication** — ubiquitous language is implicit
- **CLI utilities and scripts** — no domain complexity to manage

### Trade-offs

| Benefit | Cost |
|---|---|
| Code reflects business language | Significant upfront investment in domain modeling |
| Complex rules are explicit and testable | Over-engineering for simple domains |
| Bounded contexts prevent model corruption | Requires ongoing discipline to maintain boundaries |
| Teams share vocabulary | Learning curve for DDD-unfamiliar developers |

---

# Part II — Design Patterns

## 5. Repository Pattern

### What It Is

The Repository pattern provides a collection-like interface for accessing domain objects. It abstracts data persistence, allowing business logic to work with objects without knowing how they are stored (database, file, API, memory).

### Implementation

```python
from typing import Protocol

# ── Port (interface) ──
class ScanRepository(Protocol):
    async def save(self, scan: ScanReport) -> None: ...
    async def get_by_id(self, scan_id: str) -> ScanReport | None: ...
    async def list_by_url(self, url: str) -> list[ScanReport]: ...
    async def delete(self, scan_id: str) -> None: ...

# ── Production Adapter ──
class PostgresScanRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def save(self, scan: ScanReport) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO scans (id, url, findings, created_at) VALUES ($1, $2, $3, $4)",
                scan.id, scan.url, json.dumps(scan.findings), scan.created_at,
            )

    async def get_by_id(self, scan_id: str) -> ScanReport | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM scans WHERE id = $1", scan_id)
            return ScanReport.from_row(row) if row else None

# ── Test Adapter ──
class InMemoryScanRepository:
    def __init__(self) -> None:
        self._store: dict[str, ScanReport] = {}

    async def save(self, scan: ScanReport) -> None:
        self._store[scan.id] = scan

    async def get_by_id(self, scan_id: str) -> ScanReport | None:
        return self._store.get(scan_id)
```

### When to Use

- Business logic needs to be tested without a real database
- Multiple storage backends may be needed (dev: SQLite, prod: PostgreSQL)
- Data access patterns are complex enough to warrant abstraction

### When NOT to Use

- **Direct ORM usage** suffices and there's only one storage backend
- **Simple scripts** that read one file and write one file
- **One repository implementation** with no tests that swap it — the abstraction serves nothing

### Common Mistake: Repository as Query Builder

```python
# ❌ BAD — Repository exposes query internals
class ScanRepository:
    def find_where(self, column: str, operator: str, value: Any): ...
    def raw_query(self, sql: str): ...

# ✅ GOOD — Repository exposes domain-meaningful methods
class ScanRepository:
    async def get_by_id(self, scan_id: str) -> ScanReport | None: ...
    async def list_recent(self, limit: int = 10) -> list[ScanReport]: ...
    async def list_by_severity(self, min_severity: Severity) -> list[ScanReport]: ...
```

---

## 6. Factory Pattern

### What It Is

The Factory pattern encapsulates object creation logic. Instead of constructing objects directly with complex initialization, a factory function or class handles the construction, selection, and configuration of the right object.

### Implementation

```python
# ── Simple Factory Function ──
FORMATTERS: dict[str, type[ReportFormatter]] = {
    "json": JsonFormatter,
    "text": TextFormatter,
    "html": HtmlFormatter,
}

def create_formatter(format_name: str) -> ReportFormatter:
    """Create the appropriate report formatter."""
    formatter_class = FORMATTERS.get(format_name)
    if formatter_class is None:
        available = ", ".join(sorted(FORMATTERS.keys()))
        raise ValueError(f"Unknown format: {format_name!r}. Available: {available}")
    return formatter_class()

# ── Factory with Configuration ──
def create_http_client(config: Settings) -> httpx.AsyncClient:
    """Create an HTTP client configured from application settings."""
    return httpx.AsyncClient(
        timeout=config.timeout,
        follow_redirects=config.follow_redirects,
        verify=config.verify_ssl,
        proxy=config.proxy,
        headers={"User-Agent": config.user_agent},
    )
```

### When to Use

- Object creation involves logic (choosing which class, configuring parameters)
- Multiple implementations of an interface exist (selected at runtime)
- Construction is complex enough to obscure the calling code

### When NOT to Use

- **Simple construction** — `Scanner()` is clearer than `ScannerFactory.create()`
- **Only one implementation** — a factory to create one class is noise
- **Constructor parameters are trivial** — don't wrap `MyClass(a, b)` in a factory

### Common Mistake: Premature Factory

```python
# ❌ BAD — Factory for one class
class ScannerFactory:
    @staticmethod
    def create() -> Scanner:
        return Scanner()   # Just... call Scanner() directly

# ✅ GOOD — Direct construction when there's nothing to encapsulate
scanner = Scanner(client=client, config=config)
```

---

## 7. Strategy Pattern

### What It Is

The Strategy pattern defines a family of interchangeable algorithms. The caller selects which algorithm to use at runtime without changing its own logic. Each algorithm is encapsulated in a separate class or function.

### Implementation

```python
from typing import Protocol

# ── Strategy Interface ──
class RiskScorer(Protocol):
    def calculate(self, findings: list[Finding]) -> float: ...

# ── Concrete Strategies ──
class SimpleRiskScorer:
    """Sum of severity weights, normalized."""
    def calculate(self, findings: list[Finding]) -> float:
        if not findings:
            return 0.0
        total_weight = sum(f.severity.weight for f in findings)
        return min(total_weight / 100.0, 1.0)

class WeightedRiskScorer:
    """Weighted by finding confidence and severity."""
    def calculate(self, findings: list[Finding]) -> float:
        if not findings:
            return 0.0
        weighted = sum(f.severity.weight * f.confidence for f in findings)
        return min(weighted / 100.0, 1.0)

# ── Context (uses any strategy) ──
class ScanReporter:
    def __init__(self, scorer: RiskScorer) -> None:
        self._scorer = scorer

    def generate(self, findings: list[Finding]) -> Report:
        risk_score = self._scorer.calculate(findings)
        return Report(findings=findings, risk_score=risk_score)

# ── Usage ──
reporter = ScanReporter(scorer=WeightedRiskScorer())
report = reporter.generate(findings)
```

### When to Use

- Multiple algorithms for the same operation (scoring, formatting, sorting)
- Algorithm selection at runtime (user choice, configuration, A/B testing)
- You want to test algorithms independently

### When NOT to Use

- **Only one algorithm** and no realistic prospect of more — just write the function
- **Simple conditionals** — a 3-line `if/else` is simpler than a strategy hierarchy
- **Algorithms differ by one parameter** — pass the parameter, not a new class

---

## 8. Dependency Injection

### What It Is

Dependency Injection (DI) is a technique where a component receives its dependencies from the outside rather than creating them internally. This inverts the control of object creation, making components testable, configurable, and loosely coupled.

### Three Forms

```python
# ── Constructor Injection (preferred) ──
class ScanService:
    def __init__(self, client: HttpClient, repo: ScanRepository) -> None:
        self._client = client
        self._repo = repo

# ── Parameter Injection ──
async def scan_url(url: str, client: HttpClient) -> ScanResult:
    response = await client.get(url)
    return analyze(response)

# ── Module-Level (for simple cases) ──
# Configured at application startup in main.py
client = httpx.AsyncClient(timeout=30.0)
service = ScanService(client=client, repo=PostgresRepository(pool))
```

### When to Use

- Any component that performs I/O (network, database, filesystem)
- Any component that needs to be tested with fakes/mocks
- When you need different configurations for different environments

### When NOT to Use

- **Pure functions** with no dependencies — just call them
- **Loggers** — `logging.getLogger(__name__)` is the standard pattern; injecting loggers adds noise
- **Standard library utilities** — don't inject `json`, `pathlib`, or `datetime`

### Common Mistake: Over-Injection

```python
# ❌ BAD — Injecting things that don't need injection
class Scanner:
    def __init__(
        self,
        client: HttpClient,        # ✅ Correct — I/O dependency
        logger: Logger,            # ❌ Over-injection — use getLogger(__name__)
        json_parser: JsonParser,   # ❌ Over-injection — use json.loads()
        path_builder: PathBuilder, # ❌ Over-injection — use pathlib.Path
    ): ...

# ✅ GOOD — Inject only what varies
class Scanner:
    def __init__(self, client: HttpClient, repo: ScanRepository) -> None:
        self._client = client
        self._repo = repo
        self._logger = logging.getLogger(__name__)  # Standard, not injected
```

---

# Part III — Engineering Principles

## 9. SOLID Principles

### S — Single Responsibility Principle

> A class should have **one, and only one, reason to change.**

```python
# ❌ BAD — Multiple responsibilities
class ScanManager:
    def scan(self, url): ...          # Network I/O
    def analyze(self, response): ...   # Business logic
    def format_report(self, data): ... # Presentation
    def send_email(self, report): ...  # Notification

# ✅ GOOD — One responsibility each
class Scanner:
    async def scan(self, url: str) -> Response: ...

class Analyzer:
    def analyze(self, response: Response) -> list[Finding]: ...

class ReportFormatter:
    def format(self, findings: list[Finding]) -> str: ...
```

### O — Open/Closed Principle

> Software entities should be **open for extension** but **closed for modification.**

```python
# ❌ BAD — Must modify function to add new format
def generate_report(findings, format_type):
    if format_type == "json": ...
    elif format_type == "html": ...
    # Adding "csv" requires modifying this function

# ✅ GOOD — Extend by adding, not modifying
FORMATTERS: dict[str, ReportFormatter] = {
    "json": JsonFormatter(),
    "html": HtmlFormatter(),
}
# Adding "csv" = one line: "csv": CsvFormatter()
```

### L — Liskov Substitution Principle

> Objects of a supertype must be **replaceable with objects of a subtype** without breaking correctness.

```python
# ❌ BAD — Subclass violates parent's contract
class ReadOnlyRepository:
    def get(self, id: str) -> Item: ...
    def save(self, item: Item) -> None:
        raise NotImplementedError("Read only!")  # Breaks callers expecting save()

# ✅ GOOD — Separate interfaces
class Readable(Protocol):
    def get(self, id: str) -> Item: ...

class Writable(Protocol):
    def save(self, item: Item) -> None: ...

class ReadWriteRepository:  # Implements both
    def get(self, id: str) -> Item: ...
    def save(self, item: Item) -> None: ...
```

### I — Interface Segregation Principle

> Clients should not be forced to depend on interfaces they do not use.

```python
# ❌ BAD — Fat interface forces unnecessary implementation
class DataStore(Protocol):
    def read(self) -> Data: ...
    def write(self, data: Data) -> None: ...
    def delete(self, id: str) -> None: ...
    def backup(self) -> None: ...          # Not all stores need backup
    def replicate(self) -> None: ...       # Not all stores replicate

# ✅ GOOD — Segregated interfaces
class Readable(Protocol):
    def read(self) -> Data: ...

class Writable(Protocol):
    def write(self, data: Data) -> None: ...
```

### D — Dependency Inversion Principle

> High-level modules should not depend on low-level modules. Both should depend on **abstractions.**

```python
# ❌ BAD — Business logic depends on concrete HTTP library
from httpx import AsyncClient

class Scanner:
    async def scan(self, url: str) -> list[Finding]:
        async with AsyncClient() as client:   # Tightly coupled to httpx
            response = await client.get(url)

# ✅ GOOD — Business logic depends on abstraction
class HttpFetcher(Protocol):
    async def get(self, url: str) -> Response: ...

class Scanner:
    def __init__(self, fetcher: HttpFetcher) -> None:
        self._fetcher = fetcher    # Depends on protocol, not library

    async def scan(self, url: str) -> list[Finding]:
        response = await self._fetcher.get(url)
```

---

## 10. DRY — Don't Repeat Yourself

> Every piece of knowledge must have a **single, unambiguous, authoritative representation** in the system.

### What DRY Actually Means

DRY is about **knowledge duplication**, not code duplication. Two functions with similar code but different purposes are NOT a DRY violation. Two functions encoding the same business rule in two places ARE a violation.

```python
# ❌ DRY VIOLATION — Same business rule in two places
# validators.py
def validate_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

# scanner.py (same rule, duplicated)
def is_valid_target(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

# ✅ CORRECT — Single authoritative definition
# validators.py
def is_valid_http_url(url: str) -> bool:
    """Single source of truth for URL validation."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)
```

### When DRY Goes Wrong

```python
# ❌ BAD — Forced DRY creates harmful coupling
# Two similar but semantically different validations merged into one:
def validate(value: str, context: str) -> bool:
    if context == "url":
        return value.startswith("http")
    elif context == "email":
        return "@" in value
    # These have nothing in common — separating them is correct

# ✅ CORRECT — Similar code, different purposes = keep separate
def validate_url(url: str) -> bool: ...
def validate_email(email: str) -> bool: ...
```

**Rule:** Duplication is cheaper than the wrong abstraction. If you can't name the shared concept, the code isn't truly duplicated — it just looks similar.

---

## 11. KISS — Keep It Simple, Stupid

> The simplest solution that works correctly is the best solution.

### What KISS Means in Practice

| Situation | Complex Approach | Simple Approach |
|---|---|---|
| 3 report formats | AbstractFormatterFactory → FormatterStrategy → ... | `dict[str, Callable]` dispatch table |
| One database | RepositoryProtocol + PostgresAdapter + InMemoryAdapter | Direct SQLAlchemy queries |
| Feature toggle | FeatureFlagService + A/B testing framework | `if settings.enable_feature_x:` |
| String building | Builder pattern with fluent API | f-string or `str.join()` |

```python
# ❌ OVER-ENGINEERED — Enterprise complexity for a simple task
class ReportBuilderFactory:
    def create_builder(self, type: str) -> AbstractReportBuilder:
        registry = BuilderRegistry.get_instance()
        return registry.resolve(type)

builder = ReportBuilderFactory().create_builder("json")
report = builder.set_title(t).set_findings(f).set_metadata(m).build()

# ✅ SIMPLE — Same result, 1/10th the code
report = {"title": title, "findings": findings, "metadata": metadata}
output = json.dumps(report, indent=2)
```

---

## 12. YAGNI — You Aren't Gonna Need It

> Do not implement functionality until it is **actually needed** — not "might be needed someday."

### The Cost of Premature Features

| YAGNI Violation | Cost |
|---|---|
| Plugin system for a tool with zero plugins | Architecture complexity, testing burden, documentation |
| Database abstraction for a tool that only uses SQLite | Extra interfaces, adapters, mapping code |
| Multi-language support for an internal tool | Translation files, string extraction, testing matrix |
| Microservice architecture for a 200-line tool | Deployment complexity, network latency, distributed debugging |

```python
# ❌ YAGNI — Building for a future that may never come
class Scanner:
    def __init__(self, plugin_manager: PluginManager):  # No plugins exist
        self._plugins = plugin_manager

    async def scan(self, url: str, strategy: ScanStrategy):  # Only one strategy
        ...

# ✅ CORRECT — Build what you need now
class Scanner:
    async def scan(self, url: str) -> ScanResult:
        ...
    # When a second strategy is actually needed, refactor then
```

**The golden rule:** Write code for today's requirements. Refactoring when needs change is cheaper than maintaining unused abstractions.

---

## 13. High Cohesion

> Every module should contain elements that are **functionally related** and work together to fulfill a single purpose.

### Measuring Cohesion

```python
# ❌ LOW COHESION — Unrelated functions sharing a module
# utils.py
def validate_url(url): ...        # Input validation
def format_bytes(n): ...          # Display formatting
def send_email(to, body): ...     # Email delivery
def retry(func, n): ...           # Error handling
def hash_password(pw): ...        # Security

# ✅ HIGH COHESION — Related functions in focused modules
# validators.py     → validate_url(), validate_email(), validate_ip()
# formatters.py     → format_bytes(), format_duration(), format_table()
# notifications.py  → send_email(), send_slack(), send_webhook()
# retry.py          → retry(), with_backoff(), circuit_breaker()
# security.py       → hash_password(), verify_password(), generate_token()
```

### Test: If you can't name the module without using "and" or "utils," cohesion is low.

---

## 14. Low Coupling

> Modules should have **minimal dependencies** on each other. Changes to one module should not cascade to many others.

### Coupling Spectrum

```
TIGHT COUPLING ──────────────────────────── LOOSE COUPLING
 Content    Common    Control    Stamp    Data    Message
 (worst)                                           (best)
```

| Coupling Type | Description | Example |
|---|---|---|
| **Content** | Module A directly accesses B's internals | `module_b._private_var = 5` |
| **Common** | Modules share global mutable state | Global `config` dict modified by multiple modules |
| **Control** | Module A passes a flag that controls B's behavior | `process(data, use_legacy=True)` |
| **Stamp** | Module A passes a large structure when B needs only part | `process(entire_request)` when only `request.url` is needed |
| **Data** | Modules communicate through well-defined parameters | `process(url: str, timeout: float)` |
| **Message** | Modules communicate through events/messages | `event_bus.publish(ScanCompleted(...))` |

```python
# ❌ TIGHT COUPLING — Scanner knows Report internals
class Scanner:
    def scan(self, url: str) -> None:
        findings = self._analyze(url)
        self.report._findings_list.append(findings)  # Accessing internal state!
        self.report._recalculate_risk()               # Calling internal method!

# ✅ LOOSE COUPLING — Communication through public interface
class Scanner:
    def scan(self, url: str) -> list[Finding]:
        return self._analyze(url)     # Returns data, doesn't touch Report

# Report is assembled elsewhere from the returned data
findings = scanner.scan(url)
report = Report(findings=findings)
```

---

## 15. Modularity

> A system should be decomposed into **independent, replaceable modules** with well-defined interfaces.

### Module Quality Checklist

| Quality | Test | Pass | Fail |
|---|---|---|---|
| **Independent** | Can this module be tested alone? | Yes, with only its declared dependencies | Needs 5 other modules to run a single test |
| **Replaceable** | Can this module be swapped? | Yes, anything implementing the interface works | Hardcoded references to implementation details |
| **Understandable** | Can someone understand this module without reading others? | Module's purpose is clear from its name and docstring | Understanding requires reading 3 other modules |
| **Focused** | Does this module do one thing? | Single responsibility, < 300 lines | Multiple responsibilities, > 500 lines |

```python
# ✅ MODULAR — Each module is independent and focused
# analyzers/header_analyzer.py
class HeaderAnalyzer:
    """Analyzes HTTP headers. No I/O, no dependencies on other analyzers."""
    def analyze(self, headers: dict[str, str]) -> list[Finding]:
        ...

# analyzers/tls_analyzer.py
class TLSAnalyzer:
    """Analyzes TLS configuration. Independent of header analysis."""
    def analyze(self, cert_info: CertInfo) -> list[Finding]:
        ...

# Each can be tested, understood, and replaced independently
```

---

## 16. Scalability & Maintainability

### Scalability Strategies

| Strategy | When | Implementation |
|---|---|---|
| **Async I/O** | I/O-bound operations (HTTP, DB, files) | `asyncio`, `httpx.AsyncClient` |
| **Concurrency limiting** | Prevent resource exhaustion | `asyncio.Semaphore(max_concurrent)` |
| **Streaming** | Large data volumes | Generators, `async for`, chunked reads |
| **Batching** | Many small operations | Batch database writes, bulk API calls |
| **Caching** | Repeated expensive computations | `functools.lru_cache`, Redis |
| **Horizontal** | Single instance reaches limits | Task queues, worker processes |

### Maintainability Strategies

| Strategy | How | Measure |
|---|---|---|
| **Consistent naming** | Follow conventions throughout | Grep for convention violations |
| **Small functions** | ≤ 40 lines, ≤ 5 parameters | Linter rules |
| **Clear dependencies** | Constructor injection, explicit imports | Dependency graph is a DAG |
| **Comprehensive tests** | ≥ 80% coverage, meaningful assertions | Coverage reports |
| **Up-to-date docs** | Docstrings match code, README is current | Review checklist |
| **Low complexity** | Cyclomatic complexity ≤ 10 | `radon` or `ruff` rules |

---

# Part IV — Decision Framework

## 17. Architecture Decision Trees

### Decision Tree 1: Choosing an Architectural Style

```
START: What is the project complexity?
│
├── Simple (< 500 lines, single purpose)
│   └── → No formal architecture. Single module with functions.
│
├── Medium (500–5,000 lines, moderate business logic)
│   ├── Is testability critical?
│   │   ├── Yes → Layered Architecture with dependency injection
│   │   └── No  → Simple Layered Architecture (3 layers)
│   │
│   └── Are there multiple input channels (CLI + API)?
│       ├── Yes → Hexagonal Architecture (Ports & Adapters)
│       └── No  → Layered Architecture
│
└── Complex (> 5,000 lines, rich domain, long-lived)
    ├── Is domain modeling the primary challenge?
    │   ├── Yes → DDD + Clean Architecture
    │   └── No  → Clean Architecture or Hexagonal
    │
    └── Are there multiple bounded contexts?
        ├── Yes → DDD with Context Mapping
        └── No  → Clean Architecture
```

### Decision Tree 2: Choosing a Design Pattern

```
START: What problem are you solving?
│
├── Creating objects with complex configuration?
│   ├── Multiple implementations selected at runtime? → Factory Pattern
│   └── One implementation with many parameters? → Builder or Config dataclass
│
├── Swapping algorithms at runtime?
│   ├── Multiple algorithms exist? → Strategy Pattern
│   └── One algorithm with variations? → Parameterize the function
│
├── Abstracting data persistence?
│   ├── Need to test without database? → Repository Pattern
│   └── Direct ORM usage is sufficient? → No pattern needed
│
├── Decoupling components?
│   ├── Component needs I/O dependency? → Dependency Injection
│   └── Components communicate events? → Observer / Event Bus
│
└── None of the above?
    └── → Write plain functions. Don't apply a pattern without a problem.
```

### Decision Tree 3: Abstractions

```
START: Should I create an abstraction (Protocol, ABC)?
│
├── Do you have 2+ implementations right now?
│   ├── Yes → Create the abstraction
│   └── No  → Continue...
│
├── Do tests need to swap the implementation?
│   ├── Yes → Create a Protocol for the dependency
│   └── No  → Continue...
│
├── Is this at an architectural boundary (network, DB, filesystem)?
│   ├── Yes → Create a Protocol (boundaries change)
│   └── No  → Continue...
│
└── None of the above?
    └── → DO NOT create an abstraction. Use concrete types.
        Refactor when you actually need the abstraction.
```

---

## 18. Trade-off Analysis

### Architecture Trade-off Matrix

| Decision | Speed Benefit | Complexity Cost | Testability Benefit | Maintainability Benefit | When Worth It |
|---|---|---|---|---|---|
| **Clean Architecture** | None | High (+4 layers) | Very High | Very High | Complex, long-lived projects |
| **Layered Architecture** | Slight | Low (+3 layers) | Medium | High | Most standard applications |
| **Hexagonal** | None | Medium (+ports/adapters) | Very High | High | Multi-channel input systems |
| **Repository Pattern** | None | Medium (+interface) | High | High | When testing without DB matters |
| **Strategy Pattern** | None | Low (+interface + classes) | Medium | High | ≥ 2 algorithms exist |
| **Factory Pattern** | None | Low (+function) | Low | Medium | Complex object creation |
| **Dependency Injection** | None | Low (+parameters) | Very High | High | Any I/O dependency |
| **DDD** | None | Very High | High | Very High | Complex domain models |

### The Complexity Budget

Every project has a complexity budget. Each pattern you add consumes part of that budget.

```
Simple CLI Tool:        ████░░░░░░ Budget: 4/10
Medium Web Service:     ████████░░ Budget: 8/10
Enterprise Platform:    ██████████ Budget: 10/10

Pattern costs:
  Clean Architecture:   ████  (4 units)
  Hexagonal:            ███   (3 units)
  Layered:              ██    (2 units)
  Repository:           █     (1 unit)
  Strategy:             █     (1 unit)
  Factory:              ░     (0.5 units)
  DI:                   ░     (0.5 units)
  DDD:                  █████ (5 units)
```

**Rule:** Never exceed the complexity budget. A CLI tool with Clean Architecture + DDD + Repository + Strategy has consumed 11/4 of its budget — it will collapse under its own weight.

---

## 19. When NOT to Use a Pattern

### Pattern Overuse Signals

| Signal | What's Happening | Solution |
|---|---|---|
| "Interface with one implementation" | Premature abstraction | Delete the interface. Use the concrete class. |
| "Factory that creates one type" | Unnecessary indirection | Call the constructor directly. |
| "Strategy with one strategy" | Solving a problem that doesn't exist | Use the function directly. |
| "Repository for one test file" | Testing pattern, not architectural need | Consider inline fakes or mocks. |
| "Event bus for two components" | Over-decoupling | Direct function calls are fine. |
| "DI container for 3 classes" | Framework overkill | Manual constructor injection. |
| "Microservices for 500 lines" | Architecture astronautics | Monolith. Always start monolith. |

### The "Delete Test"

For any pattern in your codebase, ask:

> "If I deleted this pattern and replaced it with the simplest alternative, what concrete problem would I face?"

If the answer is "none" or "we might need it someday," delete the pattern.

### Specific Anti-Recommendations

```python
# ❌ DON'T — Abstract for one implementation
class IUserService(ABC):
    @abstractmethod
    def get_user(self, id: str) -> User: ...

class UserService(IUserService):   # The ONLY implementation
    def get_user(self, id: str) -> User: ...

# ✅ DO — Concrete until you need abstraction
class UserService:
    def get_user(self, id: str) -> User: ...

# ❌ DON'T — Pattern for trivial operation
class StringFormatterStrategy(Protocol):
    def format(self, value: str) -> str: ...

class UpperCaseFormatter:
    def format(self, value: str) -> str:
        return value.upper()

# ✅ DO — Just call the function
result = value.upper()
```

---

## 20. When Simplicity Wins

### The Simplicity Hierarchy

Choose the **simplest level** that satisfies your requirements:

```
Level 1: Plain function
Level 2: Module with functions
Level 3: Class with methods
Level 4: Class with injected dependencies
Level 5: Interface + implementation
Level 6: Multiple implementations behind interface
Level 7: Framework with registries and dispatching
```

### Case Studies

**Case: URL Validation**

```python
# Level 1: SUFFICIENT for most projects
def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"Invalid scheme: {parsed.scheme}")
    return url

# Level 5: OVERKILL unless you have multiple validation strategies
class UrlValidator(Protocol):
    def validate(self, url: str) -> str: ...

class HttpUrlValidator:
    def validate(self, url: str) -> str: ...
```

**Case: Configuration Loading**

```python
# Level 2: SUFFICIENT for small tools
# config.py
TIMEOUT = float(os.getenv("TIMEOUT", "30"))
RETRIES = int(os.getenv("RETRIES", "3"))

# Level 4: APPROPRIATE for medium projects
class Settings(BaseSettings):
    timeout: float = 30.0
    retries: int = 3

# Level 6: OVERKILL unless you actually swap config sources
class ConfigProvider(Protocol):
    def load(self) -> Settings: ...
class EnvConfigProvider: ...
class FileConfigProvider: ...
class VaultConfigProvider: ...
```

### The Complexity Razor

> When two solutions solve the same problem, choose the one with fewer concepts, fewer files, fewer layers, and fewer abstractions. Bias toward simplicity. Add complexity only when a concrete, immediate problem demands it.

---

## 21. Architecture Review Checklists

### Checklist 1: Pre-Implementation Architecture Review

Perform this review during **Phase 1** (Architecture Design) before any code is written.

| # | Check | Pass | Fail |
|---|---|---|---|
| AR-01 | Architectural style is justified by project complexity | Style matches project size and requirements | Over-engineered or under-engineered for the problem |
| AR-02 | Dependency direction is defined and acyclic | Clear diagram showing allowed dependencies | No direction defined, or cycles exist |
| AR-03 | Every module has a single, named responsibility | Module names are nouns/verbs that describe one thing | Module named "utils," "helpers," or "manager" |
| AR-04 | External boundaries identified | Network, DB, filesystem touchpoints are listed | External systems accessed from arbitrary modules |
| AR-05 | Error strategy defined per boundary | Each external boundary has timeout, retry, fallback plan | No error handling plan for external systems |
| AR-06 | Data flow is documented | Input → Processing → Output chain is clear | No data flow, or data flow has gaps |
| AR-07 | Module count is proportional to complexity | ≤ 15 modules for MVP, ≤ 50 for large systems | 30 modules for a 500-line tool |
| AR-08 | Patterns are justified by concrete needs | Each pattern solves an identified problem | Patterns applied "in case we need them" |
| AR-09 | Folder structure is defined and documented | Every directory has a stated purpose | Files in arbitrary locations |
| AR-10 | Public API surface is minimal | Only necessary functions/classes are public | Everything is public by default |

---

### Checklist 2: Post-Implementation Architecture Review

Perform this review during **Phase 5** (Integration & Verification).

| # | Check | Pass | Fail |
|---|---|---|---|
| PR-01 | Dependency direction followed in code | Imports flow in the defined direction | Core imports from infrastructure |
| PR-02 | No circular dependencies | `importlib` or manual trace shows no cycles | Module A imports B imports A |
| PR-03 | Module responsibilities match specification | Each module does what its spec says | Module grew additional responsibilities |
| PR-04 | "Does NOT" constraints respected | Modules don't do things their specs exclude | Data access module contains business logic |
| PR-05 | Abstractions have ≥ 2 justifications | Each Protocol/ABC has tests or multiple implementations | Interface with one implementation and no test fakes |
| PR-06 | Complexity budget not exceeded | Patterns used ≤ project complexity level | CLI tool with 4 architectural layers and DDD |
| PR-07 | Cross-cutting concerns handled consistently | Logging, error handling, config are uniform | Different error patterns in different modules |
| PR-08 | Data flow matches architecture document | Actual code follows the documented flow | Code shortcuts bypass architectural layers |
| PR-09 | No God objects | No class with > 10 public methods or > 5 dependencies | One class that does everything |
| PR-10 | No dead abstractions | Every interface is used. Every factory is called. | Interfaces, factories, or strategies with no consumers |

---

### Checklist 3: Architecture Decision Record (ADR) Template

For significant architectural decisions, create an ADR:

```markdown
# ADR-NNN: [Decision Title]

## Status
PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED

## Context
[What problem are we solving? What forces are at play?]

## Decision
[What did we decide? Be specific.]

## Alternatives Considered
| Alternative | Pros | Cons | Rejected Because |
|---|---|---|---|
| [Option A] | ... | ... | ... |
| [Option B] | ... | ... | ... |

## Consequences
### Positive
- [Benefit 1]
- [Benefit 2]

### Negative
- [Cost 1]
- [Cost 2]

### Risks
- [Risk and mitigation]

## Review Date
[When should this decision be revisited?]
```

---

### Checklist 4: "Is This Over-Engineered?" Audit

Run this audit when you suspect a design is too complex:

| # | Question | If Yes |
|---|---|---|
| OE-01 | Does any interface have exactly one implementation? | Consider removing the interface |
| OE-02 | Does any factory create exactly one type? | Consider direct construction |
| OE-03 | Are there layers that just pass data through? | Consider collapsing the layer |
| OE-04 | Is there an abstraction with no test that uses it? | Consider removing the abstraction |
| OE-05 | Would deleting a pattern cause zero concrete problems? | Delete the pattern |
| OE-06 | Is the total file count > 3× the class/function count? | Modules are too granular |
| OE-07 | Does understanding one feature require reading > 5 files? | Too much indirection |
| OE-08 | Are more than 30% of lines interfaces/protocols/ABCs? | Abstraction-heavy, implementation-light |
| OE-09 | Is there a design pattern whose name you can't explain to a junior? | Pattern may not be justified |
| OE-10 | Would a new developer need > 1 hour to understand the structure? | Simplify for onboarding |

**Scoring:**
- **0–2 "Yes"** — Architecture is appropriately complex
- **3–5 "Yes"** — Simplification opportunities exist
- **6+ "Yes"** — Architecture is over-engineered; simplify before adding features

---

## Appendix A — Quick Reference: Pattern Selection

| Problem | Pattern | Complexity | Minimum Justification |
|---|---|---|---|
| Need testability for I/O dependency | **Dependency Injection** | Low | One test that needs a fake |
| Multiple algorithms for same operation | **Strategy** | Low | Two algorithms exist now |
| Complex object creation logic | **Factory** | Low | Creation involves conditional logic |
| Data persistence abstraction | **Repository** | Medium | Tests need to run without DB |
| Swappable external systems | **Hexagonal (Ports)** | Medium | Two adapters or mandatory testability |
| Rich domain with business rules | **DDD** | High | Non-trivial domain logic |
| Framework independence | **Clean Architecture** | High | Framework may change, or multiple interfaces |

---

## Appendix B — Architecture Smells

| Smell | Symptom | Root Cause | Fix |
|---|---|---|---|
| **Rigidity** | Small change requires modifying many files | High coupling between modules | Introduce boundaries and interfaces at pain points |
| **Fragility** | Changes in one area break unrelated areas | Hidden dependencies, shared mutable state | Eliminate global state, use explicit dependencies |
| **Immobility** | Cannot extract a module for reuse | Module has too many dependencies | Reduce coupling, extract interfaces |
| **Viscosity** | Doing things "the right way" is harder than hacking | Architecture is too complex for the problem | Simplify the architecture |
| **Needless Complexity** | Patterns that solve no current problem | Premature abstraction, YAGNI violation | Delete unused patterns and abstractions |
| **Needless Repetition** | Same logic in multiple places | Missing shared abstraction | Extract common logic into shared module |
| **Opacity** | Code is hard to understand | Poor naming, deep nesting, missing docs | Refactor for clarity, add documentation |

---

*End of document. Architecture exists to serve the product, not the other way around. Choose the simplest architecture that solves your problem. Add complexity only when the problem demands it.*
