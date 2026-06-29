# PROJECT_REQUIREMENTS.md — Software & Product Requirements Specification

> **Classification:** Project Engineering Specification  
> **Version:** 1.0  
> **Status:** DRAFT | REVIEW | APPROVED | LOCKED  
> **Created:** YYYY-MM-DD  
> **Last Updated:** YYYY-MM-DD  
> **Owner:** [Project Lead / Engineering Manager]  
> **Approvers:** [Names of approvers]

---

## How to Use This Document

This document is the **single source of truth** for all engineering requirements before implementation begins. It is designed to be consumed by both human engineers and AI coding agents.

**For AI agents:** Do NOT write source code until every applicable section of this document has been completed and approved. If a section is marked `[TBD]` or `[PLACEHOLDER]`, stop and request the missing information before proceeding.

**Template conventions:**

- `{PROJECT_NAME}` — Replace with the actual project name
- `[TBD]` — Information that must be provided before implementation
- `[PLACEHOLDER]` — Example content to be replaced
- `[OPTIONAL]` — Section may be omitted if not applicable
- Items marked with ⚠️ are blocking — implementation cannot proceed without them

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Vision](#2-project-vision)
3. [Business Goals](#3-business-goals)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Success Metrics](#6-success-metrics)
7. [Scope](#7-scope)
8. [Out of Scope](#8-out-of-scope)
9. [Assumptions](#9-assumptions)
10. [Constraints](#10-constraints)
11. [User Personas](#11-user-personas)
12. [Architecture Overview](#12-architecture-overview)
13. [Folder Structure](#13-folder-structure)
14. [Module Specifications](#14-module-specifications)
15. [Public Interfaces](#15-public-interfaces)
16. [CLI / API Requirements](#16-cli--api-requirements)
17. [Configuration](#17-configuration)
18. [Environment Variables](#18-environment-variables)
19. [Error Handling](#19-error-handling)
20. [Logging](#20-logging)
21. [Security Requirements](#21-security-requirements)
22. [Performance Requirements](#22-performance-requirements)
23. [Scalability Requirements](#23-scalability-requirements)
24. [Coding Standards](#24-coding-standards)
25. [Documentation Standards](#25-documentation-standards)
26. [Dependency Policy](#26-dependency-policy)
27. [Testing Requirements](#27-testing-requirements)
28. [Acceptance Criteria](#28-acceptance-criteria)
29. [Definition of Done](#29-definition-of-done)
30. [Future Roadmap](#30-future-roadmap)

---

## 1. Executive Summary

### Purpose

The Executive Summary provides a concise overview of the entire project in language that any stakeholder — technical or non-technical — can understand in under two minutes. It anchors the project's identity, scope, and value proposition so that every subsequent section can be understood in context.

### Requirements

| ID | Requirement |
|---|---|
| ES-01 | ⚠️ Define the project name, codename, and version. |
| ES-02 | ⚠️ State what the software does in one to three sentences. |
| ES-03 | State who the software is for (target audience). |
| ES-04 | State the primary problem the software solves. |
| ES-05 | State the primary technology stack (language, runtime, frameworks). |
| ES-06 | State the deployment target (local, cloud, hybrid, embedded). |
| ES-07 | State the current project phase (greenfield, MVP, v2, maintenance). |

### Example

```
Project Name:       {PROJECT_NAME}
Codename:           [PLACEHOLDER]
Version:            0.1.0
Description:        {PROJECT_NAME} is an async Python CLI tool that audits
                    web application security headers, TLS configuration,
                    and common misconfigurations.
Target Audience:    Security engineers, DevOps teams, penetration testers.
Primary Problem:    Manual security header analysis is slow, inconsistent,
                    and error-prone across large environments.
Technology Stack:   Python 3.10+, httpx, pydantic, asyncio
Deployment Target:  Local CLI, CI/CD pipelines
Project Phase:      Greenfield (MVP)
```

### Validation Rules

- Every field in ES-01 through ES-07 must be completed before any module specification is written.
- The technology stack must match the language and runtime requirements in §24 (Coding Standards).
- The deployment target must be consistent with §22 (Performance) and §23 (Scalability).

### AI Implementation Notes

- Parse this section first. It establishes the foundational context for all downstream decisions.
- If the technology stack names a language, all code you produce must be in that language.
- If the project phase is "greenfield," you may create new patterns and structures. If "maintenance," you must discover and follow existing patterns.
- If any field is `[TBD]`, do NOT begin implementation. Ask for the missing information.

---

## 2. Project Vision

### Purpose

The Project Vision defines the aspirational long-term goal of the software — the "north star" that guides every architectural and design decision. It is distinct from Business Goals (§3), which are measurable and time-bound. The Vision is directional and enduring.

### Requirements

| ID | Requirement |
|---|---|
| VI-01 | ⚠️ State the project vision in one to two sentences. |
| VI-02 | Describe what the world looks like when this project succeeds. |
| VI-03 | State the core differentiator — what makes this project unique or better than alternatives. |

### Example

```
Vision:         "Every web application in production is continuously audited
                 for security misconfigurations, with zero manual effort."
Success State:  Teams integrate {PROJECT_NAME} into CI/CD and receive
                actionable findings before deployment, reducing security
                incidents by 80%.
Differentiator: Fully async, sub-second single-target scan time, structured
                machine-readable output, zero configuration required.
```

### Validation Rules

- The vision must be achievable through software. Visions that require hardware, policy changes, or organizational restructuring are out of scope.
- The differentiator must be technically verifiable — "better" or "faster" alone is insufficient; specify a concrete dimension.

### AI Implementation Notes

- Use the vision to guide trade-off decisions. When two approaches are equally correct, choose the one that better serves the vision.
- The differentiator informs architectural priorities. If the differentiator is speed, optimize the hot path. If it's zero-configuration, invest in smart defaults.

---

## 3. Business Goals

### Purpose

Business Goals translate the vision into measurable, time-bound objectives. They are the success criteria against which the project will be evaluated. Every feature, module, and line of code should trace back to at least one business goal.

### Requirements

| ID | Requirement |
|---|---|
| BG-01 | ⚠️ Define at least two business goals using the SMART framework (Specific, Measurable, Achievable, Relevant, Time-bound). |
| BG-02 | Each goal must have a measurable Key Result (KR). |
| BG-03 | Each goal must have a priority: P0 (must have), P1 (should have), P2 (nice to have). |

### Example

```
BG-01 [P0]: Deliver a functional MVP that can scan a single URL and produce
            a structured security report within 4 weeks.
  KR: Scan completes in < 5 seconds. Report contains ≥ 10 security checks.

BG-02 [P1]: Achieve adoption by 3 internal teams within 8 weeks of release.
  KR: ≥ 3 teams running {PROJECT_NAME} in their CI/CD pipelines.

BG-03 [P2]: Support batch scanning of up to 100 URLs from a file.
  KR: Batch scan of 100 URLs completes in < 60 seconds with concurrency.
```

### Validation Rules

- Every P0 goal must be addressed by at least one module in §14 (Module Specifications).
- Goals with no corresponding functional requirement (§4) are aspirational only — they do not drive implementation.
- P0 goals are blocking for MVP release. P1 goals are blocking for v1.0. P2 goals are backlog.

### AI Implementation Notes

- When prioritizing work, implement P0 goals first, then P1, then P2.
- If a P0 goal conflicts with a P2 goal, the P0 goal wins.
- If a feature does not trace to any business goal, do NOT implement it — it is scope creep.
- Use the Key Results to derive test assertions and acceptance criteria.

---

## 4. Functional Requirements

### Purpose

Functional Requirements define **what the software must do** — the specific behaviors, features, inputs, outputs, and interactions that the system must support. They are the primary input for module design and test case generation.

### Requirements

| ID | Requirement |
|---|---|
| FR-01 | ⚠️ Every functional requirement must have a unique identifier (FR-NNN). |
| FR-02 | ⚠️ Every functional requirement must specify: trigger (what initiates it), input, processing logic, output, and error behavior. |
| FR-03 | Every functional requirement must be testable — it must be possible to write a test that objectively passes or fails. |
| FR-04 | Every functional requirement must trace to at least one Business Goal (§3). |
| FR-05 | Requirements must be grouped by feature area or module. |

### Example

```
FR-001: Single URL Scan
  Trigger:   User provides a URL via CLI argument.
  Input:     A single fully-qualified URL (https://example.com).
  Process:   Perform async HTTP HEAD request. Analyze response headers
             against security best practices. Evaluate TLS configuration.
  Output:    Structured report (JSON or human-readable) containing
             findings with severity, description, and remediation.
  Error:     If URL is unreachable, return error with clear message.
             If URL is malformed, reject with validation error before request.
  Traces To: BG-01

FR-002: Batch URL Scan
  Trigger:   User provides a file path containing one URL per line.
  Input:     Path to a text file. Each line is a URL.
  Process:   Read file. Validate all URLs. Scan concurrently with
             configurable concurrency limit (default: 10).
  Output:    Aggregated report for all URLs. Individual findings per URL.
  Error:     Skip invalid URLs with warning. Continue scanning valid URLs.
             If file is empty, return error. If file does not exist, return error.
  Traces To: BG-03
```

### Validation Rules

- Every FR must have all five components: trigger, input, process, output, error. If any is missing, the requirement is incomplete.
- Every FR must trace to a BG. Orphan FRs must be justified or removed.
- Ambiguous verbs ("handle," "process," "manage") must be expanded to specify concrete behavior.
- Negative requirements ("must NOT") are valid and testable.

### AI Implementation Notes

- Parse FRs as your primary implementation driver. Each FR typically maps to one or more functions or methods.
- The "process" section defines the algorithm. The "error" section defines the exception handling.
- If an FR's process section says "TBD" or is vague, stop and ask for clarification.
- Generate at least one test case per FR component: one for happy path, one for each error condition, one for edge cases.

---

## 5. Non-Functional Requirements

### Purpose

Non-Functional Requirements (NFRs) define **how the software must behave** — quality attributes like performance, reliability, security, usability, and maintainability that constrain the implementation without specifying features.

### Requirements

| ID | Requirement |
|---|---|
| NF-01 | ⚠️ Define measurable NFRs for at least: performance, reliability, security, and maintainability. |
| NF-02 | Every NFR must have a quantitative threshold or qualitative standard that can be verified. |
| NF-03 | NFRs must be prioritized: Critical (must meet at launch), Important (must meet at v1.0), Desirable (target for future). |

### Example

```
NF-001 [Critical]: Response Time
  A single-URL scan must complete in < 5 seconds on a standard connection.

NF-002 [Critical]: Reliability
  The tool must not crash on malformed input. All input errors must produce
  a user-friendly error message and a non-zero exit code.

NF-003 [Important]: Memory Usage
  Peak memory usage must not exceed 256 MB for a batch scan of 100 URLs.

NF-004 [Important]: Compatibility
  Must run on Python 3.10, 3.11, 3.12 without modification.

NF-005 [Desirable]: Accessibility
  CLI output must be screen-reader friendly (no reliance on color alone).
```

### Validation Rules

- "Fast," "reliable," "scalable" are NOT valid NFRs. They must include specific numbers or standards.
- Every Critical NFR must have a corresponding test or benchmark in §27 (Testing Requirements).
- NFRs must not contradict each other (e.g., "encrypt everything" vs "< 1ms response time").

### AI Implementation Notes

- NFRs constrain your implementation choices. If NF-001 says "< 5 seconds," you must use async I/O, not blocking requests.
- If an NFR specifies memory limits, use generators and streaming instead of loading data into lists.
- If an NFR specifies Python version compatibility, verify that all syntax and library features you use are available on the minimum version.
- Run performance benchmarks against NFR thresholds as part of your verification.

---

## 6. Success Metrics

### Purpose

Success Metrics define how the project's success will be measured after deployment. They go beyond functional correctness to measure real-world impact, adoption, and value delivery.

### Requirements

| ID | Requirement |
|---|---|
| SM-01 | Define at least three success metrics with target values and measurement methods. |
| SM-02 | Each metric must be measurable without modifying the core application (instrumentation, logs, external tools). |
| SM-03 | Define a measurement cadence (daily, weekly, monthly). |

### Example

```
SM-001: Adoption
  Metric:    Number of unique CI/CD pipelines running {PROJECT_NAME}.
  Target:    ≥ 10 pipelines within 90 days of release.
  Measure:   Opt-in telemetry or manual survey.
  Cadence:   Monthly.

SM-002: Scan Accuracy
  Metric:    False positive rate on security findings.
  Target:    < 5% false positive rate.
  Measure:   Manual review of a random sample of 100 findings per month.
  Cadence:   Monthly.

SM-003: Performance
  Metric:    P95 scan duration for single-URL scans.
  Target:    < 3 seconds.
  Measure:   Automated benchmark suite in CI.
  Cadence:   Per release.
```

### Validation Rules

- Metrics must be quantitative. "User satisfaction" requires a specific survey instrument and threshold.
- Targets must be realistic given the constraints in §10.
- At least one metric must directly measure the core differentiator stated in §2.

### AI Implementation Notes

- You are NOT responsible for implementing measurement infrastructure unless explicitly asked.
- Use success metrics to validate that your implementation priorities are correct. If the top metric is "scan accuracy," prioritize correctness over speed.
- If the metrics reference telemetry, ensure any data collection respects privacy requirements in §21.

---

## 7. Scope

### Purpose

Scope defines the precise boundaries of what will be built in the current phase. It is the authoritative answer to "Is this part of the project?" Every feature either is in scope or is not. There is no ambiguity.

### Requirements

| ID | Requirement |
|---|---|
| SC-01 | ⚠️ List every feature, module, and deliverable that is in scope for the current phase. |
| SC-02 | Each scope item must trace to a Functional Requirement (§4). |
| SC-03 | State the target milestone or release for each scope item. |

### Example

```
In Scope — MVP (v0.1.0):
  ✓ SC-001: Single URL scanning (FR-001)
  ✓ SC-002: Security header analysis (FR-003)
  ✓ SC-003: TLS configuration check (FR-004)
  ✓ SC-004: CLI interface with URL argument (FR-005)
  ✓ SC-005: JSON output format (FR-006)
  ✓ SC-006: Human-readable terminal output (FR-007)
  ✓ SC-007: Exit codes (0 = clean, 1 = findings, 2 = error) (FR-008)

In Scope — v1.0:
  ✓ SC-008: Batch URL scanning from file (FR-002)
  ✓ SC-009: HTML report generation (FR-009)
  ✓ SC-010: Configuration file support (FR-010)
```

### Validation Rules

- Every scope item must reference a Functional Requirement. If it doesn't, it's either missing an FR (add one) or it's out of scope.
- Scope must be consistent with the Business Goals' priorities. P0 goals must be in scope for MVP.
- If scope changes, this document must be updated before implementation proceeds.

### AI Implementation Notes

- This is your **implementation boundary**. If a feature is not listed here, do NOT implement it — even if it seems like a good idea.
- If you identify a missing feature that seems necessary (e.g., input validation is not listed but obviously required), ask whether it should be added to scope rather than implementing silently.
- Check scope items against the folder structure (§13) to ensure every module has a home.

---

## 8. Out of Scope

### Purpose

Out of Scope explicitly lists features, integrations, and capabilities that will NOT be built in the current phase. This section prevents scope creep by providing a definitive "no" list that both humans and AI agents can reference.

### Requirements

| ID | Requirement |
|---|---|
| OS-01 | ⚠️ List at least five items that are explicitly out of scope. |
| OS-02 | For each item, state why it is out of scope (complexity, time, dependency, not needed yet). |
| OS-03 | Indicate which items may be reconsidered in future phases (reference §30 Roadmap). |

### Example

```
OS-001: Web UI dashboard              — Complexity exceeds MVP timeline. See Roadmap v2.0.
OS-002: Authentication/authorization   — CLI tool, no multi-user access needed.
OS-003: Database storage of results    — Output to files/stdout is sufficient for MVP.
OS-004: Real-time monitoring           — Batch scanning is the MVP use case.
OS-005: Plugin/extension system        — Premature abstraction. Revisit at v2.0.
OS-006: Windows-specific optimizations — Cross-platform via Python stdlib is sufficient.
```

### Validation Rules

- Out of scope items must not appear in §7 (Scope). If they do, there is a conflict.
- Out of scope items must not be implemented. This is a hard constraint.
- "Not yet" items must appear in §30 (Future Roadmap) with a target version.

### AI Implementation Notes

- Before implementing any feature, verify it is NOT in this list.
- If you believe an out-of-scope item is actually necessary for a scoped feature to work correctly, raise it as a question rather than implementing it.
- Do not build abstractions, interfaces, or extension points "in preparation" for out-of-scope features unless explicitly instructed to do so. That is YAGNI.

---

## 9. Assumptions

### Purpose

Assumptions document the conditions that are believed to be true but have not been verified. They represent risk — if an assumption proves false, the implementation may need to change. Documenting them explicitly enables proactive risk management.

### Requirements

| ID | Requirement |
|---|---|
| AS-01 | List all assumptions about the runtime environment, dependencies, infrastructure, user behavior, and external systems. |
| AS-02 | Classify each assumption by risk: Low (unlikely to be wrong), Medium (possible), High (could easily be wrong). |
| AS-03 | For High-risk assumptions, define a mitigation strategy. |

### Example

```
AS-001 [Low]:    Python 3.10+ is available in the target environment.
AS-002 [Low]:    Network access is available (tool scans remote URLs).
AS-003 [Medium]: Target websites respond within 30 seconds.
  Mitigation:    Configurable timeout with sensible default.
AS-004 [Medium]: Users have basic CLI proficiency.
AS-005 [High]:   All target URLs use standard HTTP/HTTPS protocols.
  Mitigation:    Validate URL scheme before scanning. Reject unsupported schemes
                 with a clear error message.
```

### Validation Rules

- Every assumption must be verifiable — it must be possible to check whether it is true or false.
- High-risk assumptions without mitigations are blocking. They must be resolved before implementation.
- Assumptions must not contradict constraints (§10).

### AI Implementation Notes

- Treat assumptions as design inputs. If AS-003 assumes 30-second responses, set your default timeout to 30 seconds.
- When you encounter a situation where an assumption might be wrong, implement the mitigation strategy — do not ignore it.
- If you discover a new assumption during implementation, add it to this section and flag it for review.

---

## 10. Constraints

### Purpose

Constraints are non-negotiable restrictions imposed by business, technical, legal, or organizational factors. Unlike assumptions (which may be wrong), constraints are known truths that limit implementation choices.

### Requirements

| ID | Requirement |
|---|---|
| CN-01 | ⚠️ List all technical constraints (language, runtime, OS, hardware). |
| CN-02 | List all business constraints (timeline, budget, team size). |
| CN-03 | List all legal/regulatory constraints (licenses, data privacy, compliance). |
| CN-04 | List all infrastructure constraints (deployment target, network, storage). |

### Example

```
Technical:
  CN-001: Language must be Python 3.10+.
  CN-002: Must use only async I/O for network operations.
  CN-003: Must run without root/admin privileges.
  CN-004: No native/compiled dependencies — pure Python or wheels only.

Business:
  CN-005: MVP must be deliverable within 4 weeks.
  CN-006: Team size: 1 developer + AI agent.

Legal:
  CN-007: All dependencies must use permissive licenses (MIT, BSD, Apache 2.0).
  CN-008: No storage of scanned website content (privacy).

Infrastructure:
  CN-009: Must run in CI/CD environments (GitHub Actions, GitLab CI, Jenkins).
  CN-010: Must work behind corporate proxies (configurable proxy support).
```

### Validation Rules

- Constraints are immutable during the current phase. If a constraint needs to change, the entire document must be re-reviewed.
- Implementation must satisfy ALL constraints. A solution that violates any constraint is rejected.
- Constraints must not contradict each other.

### AI Implementation Notes

- Check every implementation decision against this list. If CN-004 says "no native dependencies," you cannot use `lxml` (requires compilation) — use `defusedxml` or `html.parser` instead.
- Language and runtime constraints override your preferences. If CN-001 says Python 3.10+, do not use Python 3.12-only features.
- License constraints apply to all dependencies. Verify licenses before adding any dependency.

---

## 11. User Personas

### Purpose

User Personas define who will use the software, how they will use it, what they value, and what frustrates them. Personas inform UI/UX decisions, error message wording, default values, and documentation tone.

### Requirements

| ID | Requirement |
|---|---|
| UP-01 | Define at least two user personas. |
| UP-02 | Each persona must include: name, role, technical proficiency, primary use case, pain points, and success criteria. |
| UP-03 | Identify the primary persona — the one whose needs take priority in design trade-offs. |

### Example

```
Persona 1 (Primary): "Alex — Security Engineer"
  Role:         Application Security Engineer at a mid-size SaaS company.
  Proficiency:  Expert. Comfortable with CLI tools, scripting, CI/CD.
  Use Case:     Runs {PROJECT_NAME} in CI pipeline on every deployment.
                Needs machine-readable output (JSON) for integration.
  Pain Points:  False positives waste time. Slow scans block pipelines.
                Inconsistent report formats across tools.
  Success:      Zero-config scan that produces actionable, low-noise findings.

Persona 2: "Jordan — DevOps Engineer"
  Role:         DevOps engineer responsible for deployment automation.
  Proficiency:  Intermediate. Uses CLI daily but not a security specialist.
  Use Case:     Adds {PROJECT_NAME} as a quality gate in deployment pipeline.
                Needs clear pass/fail exit codes and human-readable summaries.
  Pain Points:  Security tools that require extensive configuration.
                Cryptic error messages that require security expertise to decode.
  Success:      Drop-in tool that "just works" with sensible defaults.
```

### Validation Rules

- The primary persona's needs must be prioritized when trade-offs arise.
- Error messages and documentation tone must be appropriate for the lowest-proficiency persona.
- Every CLI flag, configuration option, and output format should serve at least one persona.

### AI Implementation Notes

- Use personas to calibrate error messages. If Jordan is "intermediate," error messages must explain what went wrong and suggest a fix — not just dump a stack trace.
- Use personas to set defaults. If Alex wants "zero-config," the tool must work correctly with no arguments except the target URL.
- If a design decision favors one persona over another, call it out and ask for direction.

---

## 12. Architecture Overview

### Purpose

The Architecture Overview defines the high-level system design: how modules relate to each other, how data flows through the system, and which architectural patterns are used. It is the blueprint that ensures all modules are designed consistently and integrate correctly.

### Requirements

| ID | Requirement |
|---|---|
| AO-01 | ⚠️ Define the architectural style (layered, hexagonal, microservice, modular monolith, pipeline, etc.). |
| AO-02 | ⚠️ Define the dependency direction (which modules depend on which). |
| AO-03 | Provide a data flow diagram or description showing how input transforms into output. |
| AO-04 | Identify external system boundaries (network, filesystem, databases, APIs). |
| AO-05 | State which modules are "core" (business logic, no I/O) and which are "infrastructure" (I/O, network, filesystem). |

### Example

```
Architecture: Pipeline with Clean Architecture layers.

Data Flow:
  CLI Input → URL Validation → HTTP Client → Response Parser
  → [Header Analyzer, TLS Analyzer, Cookie Analyzer]
  → Finding Aggregator → Report Formatter → Output (stdout/file)

Layers:
  Core (no I/O):     models, analyzers, aggregator
  Infrastructure:    http_client, report_writer, cli
  Interface:         main.py (entry point)

Dependency Direction:
  cli → core ← infrastructure
  Core never imports from infrastructure or interface.
```

### Validation Rules

- Dependency direction must be unidirectional. Circular dependencies between layers are forbidden.
- Every module in §14 must appear in the architecture diagram/description.
- External system boundaries must correspond to error handling requirements in §19.

### AI Implementation Notes

- Produce code that respects the dependency direction. If the architecture says "core never imports from infrastructure," enforce this in every `import` statement.
- Use the data flow to determine function call chains and argument passing.
- External system boundaries are where you must implement error handling, timeouts, and retries.

---

## 13. Folder Structure

### Purpose

The Folder Structure defines the physical organization of source code, tests, configuration, and documentation. A consistent, well-documented structure enables any contributor — human or AI — to locate any file predictably.

### Requirements

| ID | Requirement |
|---|---|
| FS-01 | ⚠️ Define the complete directory tree for the project. |
| FS-02 | Every directory must have a stated purpose. |
| FS-03 | Every directory must contain an `__init__.py` (for Python packages) or equivalent for the chosen language. |
| FS-04 | Test directories must mirror the source directory structure. |

### Example

```
{project_name}/
├── {project_name}/           # Main source package
│   ├── __init__.py           # Package initialization, version export
│   ├── main.py               # CLI entry point
│   ├── core/                 # Business logic (no I/O)
│   │   ├── __init__.py
│   │   ├── models.py         # Data models (dataclasses, enums)
│   │   ├── analyzers/        # Analysis modules
│   │   │   ├── __init__.py
│   │   │   ├── header_analyzer.py
│   │   │   ├── tls_analyzer.py
│   │   │   └── cookie_analyzer.py
│   │   └── aggregator.py     # Combines findings from analyzers
│   ├── infra/                # Infrastructure (I/O, network)
│   │   ├── __init__.py
│   │   ├── http_client.py    # Async HTTP client wrapper
│   │   └── report_writer.py  # Output formatting (JSON, text, HTML)
│   ├── config/               # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py       # Pydantic settings / env var parsing
│   └── exceptions.py         # Project exception hierarchy
├── tests/                    # All tests
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── unit/                 # Unit tests (mirror source structure)
│   │   ├── core/
│   │   └── infra/
│   └── integration/          # Integration tests
├── docs/                     # Documentation
├── pyproject.toml            # Project metadata, dependencies
├── README.md                 # Project overview
├── CHANGELOG.md              # Release history
├── LICENSE                   # License file
└── .gitignore                # Git ignore rules
```

### Validation Rules

- Every source file referenced in §14 (Module Specifications) must have a corresponding path in this tree.
- Test directory structure must mirror source directory structure exactly.
- No source files may live at the project root (they must be inside the source package).

### AI Implementation Notes

- Create this exact structure when initializing the project. Do not invent alternative structures.
- When adding new modules, place them in the directory that matches their architectural layer (§12).
- If a file is not listed in this structure, ask before creating it — it may indicate scope creep or misunderstanding.

---

## 14. Module Specifications

### Purpose

Module Specifications define the responsibility, interface, dependencies, and behavior of each module in the system. They are the bridge between architecture (§12) and implementation. Each module spec is a contract that the implementation must fulfill.

### Requirements

| ID | Requirement |
|---|---|
| MS-01 | ⚠️ Every module listed in §13 must have a specification. |
| MS-02 | Each specification must include: module name, file path, responsibility (single sentence), public interface (functions/classes with signatures), internal dependencies, external dependencies, and error behavior. |
| MS-03 | Module responsibilities must not overlap — each behavior must be owned by exactly one module. |
| MS-04 | Specifications must state what the module does NOT do. |

### Example

```
Module:         header_analyzer
Path:           {project_name}/core/analyzers/header_analyzer.py
Responsibility: Analyze HTTP response headers against security best practices.
Does NOT:       Make HTTP requests. Format output. Access filesystem.

Public Interface:
  async def analyze_headers(
      headers: dict[str, str],
      target_url: str,
  ) -> list[Finding]:
      """Analyze response headers and return security findings."""

Dependencies:
  Internal:  models.Finding, models.Severity
  External:  None (pure logic module)

Error Behavior:
  - Never raises exceptions. Returns empty list if headers are empty.
  - Logs warnings for unrecognized header patterns.

Traces To:  FR-003, SC-002
```

### Validation Rules

- Every public function must have complete type annotations.
- No module may have more than one responsibility (SRP).
- Dependencies must flow in the direction defined in §12.
- "Does NOT" must be respected. If a module "does not make HTTP requests," it must not import `httpx`.

### AI Implementation Notes

- Implement each module **exactly** as specified. The public interface is a contract — do not change function names, parameter names, or return types without approval.
- The "Does NOT" section defines testing boundaries — you can test this module without mocking external systems.
- If a module needs a capability that its specification forbids, ask for the specification to be updated rather than violating it.

---

## 15. Public Interfaces

### Purpose

Public Interfaces define the exact API surface that the software exposes to its consumers — whether that's a CLI, REST API, library API, or SDK. They are the **external contract** of the system.

### Requirements

| ID | Requirement |
|---|---|
| PI-01 | ⚠️ Define every public function, class, and constant that consumers can use. |
| PI-02 | Each interface must include: full signature with types, docstring, arguments, return type, raised exceptions. |
| PI-03 | Interfaces must be versioned. State the stability guarantee (stable, beta, experimental). |
| PI-04 | Internal modules must not be exposed as public interfaces. |

### Example

```
Public API (stable):

  {project_name}.scan(url: str, *, timeout: float = 30.0) -> ScanReport
  {project_name}.scan_batch(urls: list[str], *, concurrency: int = 10) -> list[ScanReport]
  {project_name}.ScanReport          — dataclass with findings, metadata, timing
  {project_name}.Finding             — dataclass with category, severity, title, description
  {project_name}.Severity            — enum (CRITICAL, HIGH, MEDIUM, LOW, INFO)

Internal (not part of public API):
  {project_name}.core.*
  {project_name}.infra.*
  {project_name}.config.*
```

### Validation Rules

- Public interfaces must be stable. Changing a stable interface requires a major version bump.
- All public interfaces must have comprehensive docstrings and type hints.
- Internal modules must be marked as internal (leading underscore or documented as private).

### AI Implementation Notes

- These signatures are contracts. Implement them exactly.
- Export public interfaces from the top-level `__init__.py`.
- Write tests against the public interface, not internal implementation details.
- If you need to change a public interface, stop and ask — it's a breaking change.

---

## 16. CLI / API Requirements

### Purpose

CLI/API Requirements define how users interact with the software through its command-line interface or API endpoints. This includes commands, arguments, flags, output formats, exit codes, and error responses.

### Requirements

| ID | Requirement |
|---|---|
| CL-01 | ⚠️ Define every CLI command, subcommand, argument, and flag. |
| CL-02 | Define exit codes and their meanings. |
| CL-03 | Define output formats (JSON, text, HTML, CSV) and how to select them. |
| CL-04 | Define help text for every command and flag. |
| CL-05 | [OPTIONAL] For API projects: define every endpoint, method, request/response schema, and status codes. |

### Example

```
CLI:
  {project_name} <url>                          — Scan a single URL
  {project_name} --file <path>                  — Scan URLs from a file
  {project_name} --format [json|text|html]      — Output format (default: text)
  {project_name} --timeout <seconds>            — Request timeout (default: 30)
  {project_name} --concurrency <n>              — Max concurrent scans (default: 10)
  {project_name} --output <path>                — Write report to file (default: stdout)
  {project_name} --verbose                      — Enable verbose logging
  {project_name} --version                      — Print version and exit
  {project_name} --help                         — Print help and exit

Exit Codes:
  0 — Scan completed, no findings of severity HIGH or above.
  1 — Scan completed, findings of severity HIGH or above detected.
  2 — Scan failed due to an error (network, configuration, input).
```

### Validation Rules

- Every flag must have a long form (`--format`). Short forms (`-f`) are optional.
- Default values must be documented.
- Exit codes must be exhaustive — every possible outcome must map to an exit code.
- Help text must be auto-generated from argument definitions (e.g., `argparse` or `typer`).

### AI Implementation Notes

- Implement CLI using the library specified in §26 (Coding Standards) or §12.4 of the system prompt.
- Every flag must correspond to a configuration parameter (§17) or environment variable (§18).
- Test CLI behavior with subprocess tests that verify exit codes and output format.
- Never use `sys.exit()` in library code — only in the CLI entry point.

---

## 17. Configuration

### Purpose

Configuration defines all tunable parameters, their defaults, valid ranges, and how they are loaded. It ensures the software works correctly out of the box while remaining customizable for different environments.

### Requirements

| ID | Requirement |
|---|---|
| CF-01 | ⚠️ List every configurable parameter with name, type, default, range, and description. |
| CF-02 | Define the configuration loading order (CLI flags → env vars → config file → defaults). |
| CF-03 | Define the configuration file format and location. |
| CF-04 | All configuration must be validated at startup. Invalid configuration must cause a clear error and immediate exit. |

### Example

```
Loading Order (highest to lowest priority):
  1. CLI flags
  2. Environment variables
  3. Configuration file ({project_name}.toml or .{project_name}.yaml)
  4. Hardcoded defaults

Parameters:
  | Name          | Type   | Default | Range       | Description                  |
  |---------------|--------|---------|-------------|------------------------------|
  | timeout       | float  | 30.0    | 1.0–300.0   | HTTP request timeout (secs)  |
  | concurrency   | int    | 10      | 1–100       | Max concurrent scans         |
  | format        | str    | "text"  | text/json/html | Output format             |
  | verbose       | bool   | false   | true/false  | Enable verbose logging       |
  | proxy         | str    | null    | valid URL   | HTTP proxy URL               |
  | max_redirects | int    | 5       | 0–20        | Max HTTP redirect follows    |
  | verify_ssl    | bool   | true    | true/false  | Verify TLS certificates      |
```

### Validation Rules

- Every parameter must have a default that produces correct behavior.
- Range validation must reject out-of-range values at startup with a clear error message.
- The configuration loading order must be documented and consistently implemented.
- `verify_ssl=false` must trigger a security warning in the log.

### AI Implementation Notes

- Use `pydantic-settings` or equivalent for type-safe configuration with validation.
- Implement the loading order exactly as specified. CLI flags must override everything.
- Validate ALL configuration at startup. Do not defer validation to first use.
- Never hardcode values that are listed as configurable.

---

## 18. Environment Variables

### Purpose

Environment Variables define the runtime configuration that is injected from the deployment environment. They are the primary mechanism for environment-specific configuration (development, staging, production) and secrets.

### Requirements

| ID | Requirement |
|---|---|
| EV-01 | ⚠️ List every environment variable with name, type, required/optional, default, and description. |
| EV-02 | Define a consistent naming convention (e.g., `{PROJECT_NAME}_TIMEOUT`). |
| EV-03 | Clearly mark which variables contain secrets. |
| EV-04 | Provide a `.env.example` file listing all variables with placeholder values. |

### Example

```
Naming Convention: {PROJECT_NAME_UPPER}_<PARAMETER>

| Variable                   | Type   | Required | Default | Secret | Description          |
|----------------------------|--------|----------|---------|--------|----------------------|
| WEBPULSE_TIMEOUT           | float  | No       | 30.0    | No     | Request timeout      |
| WEBPULSE_CONCURRENCY       | int    | No       | 10      | No     | Max concurrent scans |
| WEBPULSE_LOG_LEVEL         | str    | No       | INFO    | No     | Logging level        |
| WEBPULSE_PROXY             | str    | No       | null    | No     | HTTP proxy URL       |
| WEBPULSE_API_KEY           | str    | No       | null    | Yes    | API key for auth     |
| WEBPULSE_OUTPUT_DIR        | path   | No       | ./      | No     | Report output dir    |
```

### Validation Rules

- All environment variable names must use the defined prefix to avoid collisions.
- Secret variables must NEVER be logged, even at DEBUG level.
- Required variables with no default must cause a startup error if missing.
- Provide a `.env.example` that is committed to the repository (no real secrets).

### AI Implementation Notes

- Parse environment variables through the configuration system (§17), not directly via `os.getenv()`.
- Never provide default values for secret variables — they must be explicitly set.
- When generating `.env.example`, use placeholder values like `your-api-key-here`.
- Mark all secret variables in the configuration class so logging can redact them automatically.

---

## 19. Error Handling

### Purpose

Error Handling defines how the software responds to failures — from user input errors to network failures to internal bugs. Consistent error handling ensures the software fails predictably, provides actionable feedback, and never exposes internal details.

### Requirements

| ID | Requirement |
|---|---|
| EH-01 | ⚠️ Define the project's exception hierarchy (base exception class and subclasses). |
| EH-02 | Define error response format for each output channel (CLI, API, log). |
| EH-03 | Define retry policy for transient errors (which errors, max retries, backoff strategy). |
| EH-04 | Define graceful degradation behavior (what happens when a non-critical component fails). |

### Example

```
Exception Hierarchy:
  {ProjectName}Error (base)
  ├── ConfigurationError        — Invalid configuration at startup
  ├── ValidationError           — Invalid user input
  ├── NetworkError              — All network-related failures
  │   ├── ConnectionError       — Cannot connect to target
  │   ├── TimeoutError          — Request exceeded timeout
  │   └── TLSError              — TLS/SSL verification failure
  ├── ScanError                 — Error during scan processing
  └── ReportError               — Error generating report

Retry Policy:
  Retryable:    ConnectionError, TimeoutError (transient)
  Not Retryable: ValidationError, ConfigurationError, TLSError
  Max Retries:  3
  Backoff:      Exponential (1s, 2s, 4s) with jitter

Graceful Degradation:
  If one analyzer fails, log the error and continue with remaining analyzers.
  The report should indicate which checks could not be completed.
```

### Validation Rules

- Every exception class must include sufficient context (URL, operation, input) for debugging.
- User-facing error messages must never expose internal details (file paths, stack traces, SQL).
- Retry policy must specify which errors are retryable. Never retry non-idempotent operations blindly.
- Graceful degradation must produce partial results, not silent omissions.

### AI Implementation Notes

- Implement this exact exception hierarchy. Do not invent additional exceptions without approval.
- Catch specific exceptions — never bare `except:` or `except Exception`.
- For retryable errors, implement the specified backoff strategy.
- When a component fails gracefully, include a warning in the output indicating the incomplete check.

---

## 20. Logging

### Purpose

Logging defines what the software records about its operation, at what verbosity levels, and in what format. Effective logging enables debugging, monitoring, and auditing without exposing sensitive data.

### Requirements

| ID | Requirement |
|---|---|
| LG-01 | ⚠️ Define the log format (structured JSON, plaintext, or both). |
| LG-02 | Define log levels and what each level captures. |
| LG-03 | Define what must NEVER be logged (secrets, PII, credentials). |
| LG-04 | Define log output destinations (stderr, file, syslog). |

### Example

```
Format:    Plaintext for CLI, structured JSON when --log-format=json.
Output:    stderr (to keep stdout clean for report output).
Default:   INFO

Levels:
  DEBUG:    HTTP request/response details (headers, timing, redirects).
  INFO:     Scan started, scan completed, configuration loaded.
  WARNING:  Analyzer skipped due to error, retry attempt, deprecated feature.
  ERROR:    Scan failed for a specific URL, report generation error.
  CRITICAL: Application cannot start (config error, missing dependency).

Never Log:
  - API keys, tokens, passwords, cookies
  - Full response bodies (may contain sensitive content)
  - User-supplied credentials or authentication headers
```

### Validation Rules

- `DEBUG` logs must never appear in production unless explicitly enabled.
- Log format must be parseable by standard log aggregation tools.
- Every logged message must include a timestamp and severity level.
- The "Never Log" list is a hard constraint — violations are security findings.

### AI Implementation Notes

- Use `logging.getLogger(__name__)` in every module.
- Configure logging once in the entry point, not in library modules.
- Use lazy formatting (`%s`) with the standard logging module.
- Include correlation context (target URL, scan ID) in log messages where applicable.

---

## 21. Security Requirements

### Purpose

Security Requirements define the security controls, standards, and practices that the software must implement. They ensure the software protects itself, its users, and its targets from abuse.

### Requirements

| ID | Requirement |
|---|---|
| SR-01 | ⚠️ List all security controls required for the project. |
| SR-02 | Define input validation requirements for each input surface. |
| SR-03 | Define data handling requirements (storage, transmission, retention). |
| SR-04 | Define credential management requirements. |
| SR-05 | Define abuse prevention requirements (rate limiting, access control). |

### Example

```
SR-001: Input Validation
  All URLs must be validated before scanning (scheme, host, format).
  Reject private IP ranges to prevent SSRF-like behavior.
  Reject file:// and other non-HTTP schemes.

SR-002: Data Handling
  No scanned content is stored persistently.
  Reports are written to user-specified locations only.
  No telemetry or data transmission without opt-in consent.

SR-003: Credential Management
  API keys are read from environment variables only — never CLI args.
  Proxy credentials support authentication via standard URL format.

SR-004: Abuse Prevention
  Rate limiting for batch scans: configurable delay between requests.
  Respect robots.txt when configured to do so.
  Include identifying User-Agent header.

SR-005: TLS
  Verify TLS certificates by default. Never disable without explicit flag.
  Log a warning when TLS verification is disabled.
```

### Validation Rules

- Every input surface (CLI args, config files, environment variables, network responses) must have validation rules.
- Security requirements must not be "downgraded" without a documented risk acceptance.
- Any requirement that weakens security (e.g., disabling TLS verification) must require explicit opt-in and produce a warning.

### AI Implementation Notes

- Implement all security controls before feature work. Security is a foundation, not a finishing touch.
- SSRF prevention (blocking private IPs) is critical for any tool that makes outbound HTTP requests based on user input.
- Test security controls with adversarial inputs (malformed URLs, private IPs, path traversal attempts).

---

## 22. Performance Requirements

### Purpose

Performance Requirements define the speed, throughput, and resource consumption targets that the software must meet. They translate vague expectations ("it should be fast") into measurable, testable thresholds.

### Requirements

| ID | Requirement |
|---|---|
| PR-01 | ⚠️ Define response time targets (P50, P95, P99) for primary operations. |
| PR-02 | Define throughput targets (operations per second, items per minute). |
| PR-03 | Define resource consumption limits (memory, CPU, disk, network). |
| PR-04 | Define performance testing approach and benchmarks. |

### Example

```
PR-001: Single URL Scan
  P50: < 2 seconds    P95: < 5 seconds    P99: < 10 seconds

PR-002: Batch Scan (100 URLs)
  Throughput: ≥ 20 URLs/second with concurrency=10
  Total time: < 60 seconds

PR-003: Resource Consumption
  Peak memory: < 256 MB for batch scan of 100 URLs
  CPU: Single-core sufficient. Multi-core utilized via async I/O.
  Disk: No disk I/O during scan (reports written after completion).

PR-004: Benchmarks
  Run `pytest tests/benchmarks/ --benchmark` on every release.
  Compare against baseline. Fail if P95 regresses by > 20%.
```

### Validation Rules

- All performance targets must be measurable with automated benchmarks.
- P95 and P99 targets must account for real-world conditions (variable network latency).
- Resource limits must be tested under load (not just idle).

### AI Implementation Notes

- Choose algorithms and data structures that meet these targets. If P50 is < 2 seconds, you cannot make blocking sequential HTTP calls.
- Use `asyncio.gather()` for concurrent operations. Use `asyncio.Semaphore` to enforce concurrency limits.
- Use streaming/generators for large datasets to respect memory limits.
- Include timing in log output to make performance debugging possible.

---

## 23. Scalability Requirements

### Purpose

Scalability Requirements define how the software should behave as workload grows — more URLs, more concurrent users, larger reports, longer runtimes. They ensure the architecture supports growth without redesign.

### Requirements

| ID | Requirement |
|---|---|
| SL-01 | Define horizontal scaling approach (if applicable). |
| SL-02 | Define vertical scaling limits (single instance). |
| SL-03 | Define data volume limits (input size, output size). |
| SL-04 | Define concurrent user limits (if applicable). |

### Example

```
SL-001: Vertical Scaling
  Single instance must handle up to 1,000 URLs per batch scan.
  Above 1,000 URLs, performance degrades gracefully (not crashes).

SL-002: Horizontal Scaling
  Not applicable for MVP. The tool runs as a standalone CLI.
  Future: support distributed scanning via task queue (see Roadmap §30).

SL-003: Data Volumes
  Input file: up to 10,000 URLs (one per line, < 10 MB).
  Output report: up to 50 MB for large batch scans.
  Read input as a stream, not loaded entirely into memory.

SL-004: Concurrent Users
  Not applicable (CLI tool, single user per invocation).
```

### Validation Rules

- Graceful degradation under excess load is required. The software must never crash due to volume.
- Memory-safe patterns (streaming, generators) must be used for data volumes above stated limits.
- "Not applicable" is a valid answer but must be explicitly stated.

### AI Implementation Notes

- Design for the stated limits. If SL-001 says 1,000 URLs, test with 1,000 URLs.
- If the input file could be large, read it line-by-line with a generator — never `file.read().splitlines()`.
- Implement backpressure (semaphores, bounded queues) to prevent resource exhaustion.

---

## 24. Coding Standards

### Purpose

Coding Standards define the code quality rules, formatting conventions, and tooling that all code must adhere to. They ensure consistency, readability, and maintainability across the codebase.

### Requirements

| ID | Requirement |
|---|---|
| CS-01 | ⚠️ Define the language version and minimum supported version. |
| CS-02 | Define the formatting tool and configuration. |
| CS-03 | Define the linting tool and configuration. |
| CS-04 | Define the type checking tool and strictness level. |
| CS-05 | Define naming conventions (files, classes, functions, variables, constants). |
| CS-06 | Define complexity limits (cyclomatic, nesting, function length). |

### Example

```
Language:     Python 3.10+
Formatter:    ruff format (line length: 99)
Linter:       ruff check (all rules enabled, select ignores documented)
Type Checker: mypy --strict
Security:     bandit

Naming:
  Files:       snake_case.py
  Classes:     PascalCase
  Functions:   snake_case
  Variables:   snake_case
  Constants:   UPPER_SNAKE_CASE
  Private:     _leading_underscore

Limits:
  Cyclomatic complexity:  ≤ 10 per function
  Nesting depth:          ≤ 3 levels
  Function length:        ≤ 40 lines
  Function parameters:    ≤ 5
```

### Validation Rules

- All code must pass formatter, linter, and type checker with zero errors before delivery.
- Naming violations are blocking — they must be fixed before review.
- Complexity violations require refactoring — extract functions, use early returns, flatten logic.

### AI Implementation Notes

- Run all tools mentally before presenting code. Your code must pass `ruff check`, `ruff format`, `mypy --strict`, and `bandit` without errors.
- Use modern Python syntax appropriate for the minimum version (e.g., `str | None` for 3.10+).
- When unsure about a naming convention, follow the existing codebase. For greenfield, follow this standard.

---

## 25. Documentation Standards

### Purpose

Documentation Standards define what must be documented, how, and where. They ensure the project is understandable, maintainable, and onboarding-friendly.

### Requirements

| ID | Requirement |
|---|---|
| DS-01 | Define required documentation artifacts (README, CHANGELOG, API docs, etc.). |
| DS-02 | Define docstring format and requirements. |
| DS-03 | Define inline comment policy. |
| DS-04 | Define architecture documentation requirements. |

### Example

```
Required Artifacts:
  README.md       — Project overview, setup, usage
  CHANGELOG.md    — Release history (Keep a Changelog format)
  API.md          — Public API reference (or auto-generated from docstrings)
  ARCHITECTURE.md — System design, data flow, module relationships

Docstrings:
  Format:  Google style (Args, Returns, Raises)
  Scope:   All public functions, classes, and modules
  Private: Docstrings encouraged but not required

Inline Comments:
  Explain WHY, not WHAT
  Required for: regex patterns, bitwise operations, algorithm trade-offs
  Forbidden:    commented-out code, TODO/FIXME without linked issue

Architecture:
  Updated when modules are added, removed, or restructured.
  Includes data flow diagram and dependency direction.
```

### Validation Rules

- Every public function without a docstring is a blocking issue.
- README must be accurate for the current version — stale instructions are bugs.
- CHANGELOG must be updated with every release.

### AI Implementation Notes

- Write docstrings as you implement — not as a separate pass.
- Match the project's existing docstring format. If none exists, use Google style.
- Generate README content that reflects actual behavior, not aspirational features.

---

## 26. Dependency Policy

### Purpose

The Dependency Policy governs how external libraries are selected, evaluated, added, updated, and removed. It protects the project from supply chain risks, license conflicts, and maintenance burden.

### Requirements

| ID | Requirement |
|---|---|
| DP-01 | ⚠️ List all approved dependencies with exact versions. |
| DP-02 | Define criteria for adding new dependencies. |
| DP-03 | Define the update policy (when and how often to update). |
| DP-04 | Define prohibited dependencies or categories. |

### Example

```
Approved Dependencies (MVP):
  | Package          | Version  | Purpose                  | License |
  |------------------|----------|--------------------------|---------|
  | httpx            | 0.27.0   | Async HTTP client        | BSD-3   |
  | pydantic         | 2.7.0    | Data validation/models   | MIT     |
  | pydantic-settings | 2.3.0   | Env var configuration    | MIT     |
  | rich             | 13.7.0   | Terminal output styling  | MIT     |

Dev Dependencies:
  | Package          | Version  | Purpose                  | License |
  |------------------|----------|--------------------------|---------|
  | pytest           | 8.2.0    | Test framework           | MIT     |
  | pytest-asyncio   | 0.23.0   | Async test support       | Apache  |
  | pytest-cov       | 5.0.0    | Coverage reporting       | MIT     |
  | ruff             | 0.4.0    | Linter + formatter       | MIT     |
  | mypy             | 1.10.0   | Type checker             | MIT     |
  | bandit           | 1.7.0    | Security linter          | Apache  |

Criteria for New Dependencies:
  1. Active maintenance (commit within last 6 months)
  2. Permissive license (MIT, BSD, Apache 2.0)
  3. No unpatched critical CVEs
  4. < 10 transitive dependencies
  5. Justified need (cannot be achieved with stdlib)

Prohibited:
  - GPL-licensed libraries (incompatible with project license)
  - Libraries requiring native compilation (portability constraint)
  - `requests` (use `httpx` for consistency)

Update Policy:
  - Security patches: within 48 hours of CVE publication
  - Minor updates: monthly review
  - Major updates: per release cycle with migration plan
```

### Validation Rules

- Any dependency not on the approved list requires explicit approval before use.
- Every dependency must have its license verified against the project's license.
- Dependency versions must be pinned to exact versions in the lock file.

### AI Implementation Notes

- Use ONLY the approved dependencies. Do not add alternatives without asking.
- If you discover a need for a new dependency, present the justification against the criteria before adding it.
- When writing import statements, verify the import is from an approved dependency.

---

## 27. Testing Requirements

### Purpose

Testing Requirements define the testing strategy, coverage expectations, test infrastructure, and quality gates that ensure the software works correctly and continues to work as it evolves.

### Requirements

| ID | Requirement |
|---|---|
| TR-01 | ⚠️ Define the test framework and test runner. |
| TR-02 | Define coverage targets. |
| TR-03 | Define test categories and when each is run. |
| TR-04 | Define test data management approach. |
| TR-05 | Define test quality standards. |

### Example

```
Framework:   pytest with pytest-asyncio
Runner:      pytest (CLI), pytest in CI/CD pipeline
Coverage:    ≥ 80% line coverage for core/ modules
             ≥ 60% line coverage overall

Categories:
  | Category       | Location           | Run When       | Speed    |
  |----------------|--------------------|----------------|----------|
  | Unit tests     | tests/unit/        | Every commit   | < 30s    |
  | Integration    | tests/integration/ | Every PR       | < 2 min  |
  | Benchmarks     | tests/benchmarks/  | Every release  | < 5 min  |
  | E2E (optional) | tests/e2e/         | Pre-release    | < 10 min |

Test Data:
  Use fixtures and factories — no real URLs in unit tests.
  Use httpx MockTransport for HTTP mocking.
  Store test fixtures in tests/fixtures/ as static files.

Quality Standards:
  - Every test must have a descriptive name: test_<unit>_<scenario>_<expected>
  - No flaky tests — mock all non-deterministic dependencies
  - Arrange-Act-Assert structure
  - One assertion concept per test (multiple asserts on same concept OK)
  - No test interdependencies — each test must pass in isolation
```

### Validation Rules

- All tests must pass before any code is merged. Zero tolerance for failures.
- Coverage targets are minimums, not goals. Critical paths should have higher coverage.
- Flaky tests must be fixed or quarantined within 24 hours of detection.
- Benchmark regressions > 20% from baseline are blocking.

### AI Implementation Notes

- Write tests alongside implementation — not as a separate phase.
- For every function you implement, write: one happy path test, one error test, one edge case test.
- Mock at architectural boundaries (network, filesystem). Never mock the unit under test.
- Test file structure must mirror source structure: `{project_name}/core/analyzers/header_analyzer.py` → `tests/unit/core/analyzers/test_header_analyzer.py`.

---

## 28. Acceptance Criteria

### Purpose

Acceptance Criteria define the specific, testable conditions that must be true for each feature to be considered "done." They are the bridge between requirements (what to build) and testing (how to verify it).

### Requirements

| ID | Requirement |
|---|---|
| AC-01 | ⚠️ Every Functional Requirement (§4) must have at least one acceptance criterion. |
| AC-02 | Each criterion must be binary — it either passes or fails, with no ambiguity. |
| AC-03 | Criteria must be written in Given-When-Then format where applicable. |

### Example

```
AC-001 (for FR-001: Single URL Scan):
  GIVEN a valid HTTPS URL
  WHEN the user runs `{project_name} https://example.com`
  THEN the tool outputs a report containing security findings
  AND the report includes at least 10 security checks
  AND the exit code is 0 (if no HIGH+ findings) or 1 (if HIGH+ findings)
  AND the scan completes within 10 seconds

AC-002 (for FR-001: Error Handling):
  GIVEN a malformed URL (e.g., "not-a-url")
  WHEN the user runs `{project_name} not-a-url`
  THEN the tool prints a user-friendly error message
  AND the error message suggests the correct URL format
  AND the exit code is 2
  AND no network request is made

AC-003 (for FR-002: Batch Scan):
  GIVEN a file containing 50 valid URLs
  WHEN the user runs `{project_name} --file urls.txt`
  THEN the tool scans all 50 URLs concurrently
  AND produces a combined report with per-URL findings
  AND completes within 30 seconds
```

### Validation Rules

- Acceptance criteria must be objectively testable — no subjective terms ("looks good," "works well").
- Each criterion must map directly to at least one automated test.
- Criteria that reference performance thresholds must match §22 (Performance Requirements).

### AI Implementation Notes

- Use acceptance criteria to generate integration and E2E test cases.
- The Given-When-Then format maps directly to test structure: Given = Arrange, When = Act, Then = Assert.
- If an acceptance criterion cannot be tested automatically, flag it for manual verification.
- Do not mark a feature as complete until ALL its acceptance criteria pass.

---

## 29. Definition of Done

### Purpose

The Definition of Done (DoD) is the universal checklist that every piece of work must satisfy before it is considered complete. It applies to every task, story, or feature — regardless of size.

### Requirements

| ID | Requirement |
|---|---|
| DD-01 | ⚠️ Define a single, unambiguous DoD checklist. |
| DD-02 | The DoD must cover: code quality, testing, documentation, security, and review. |
| DD-03 | Every item must be objectively verifiable. |

### Example

```
Definition of Done — Every task must satisfy ALL items:

Code:
  [ ] Code implements the stated requirement — nothing more, nothing less
  [ ] Code passes ruff format, ruff check, mypy --strict, and bandit with zero errors
  [ ] All functions have type hints and docstrings
  [ ] No TODO, FIXME, HACK, or placeholder code
  [ ] No hardcoded secrets, credentials, or environment-specific values
  [ ] Error handling covers all expected failure modes

Testing:
  [ ] Unit tests written for all new/modified functions
  [ ] All tests pass (pytest exits with code 0)
  [ ] Code coverage meets or exceeds targets in §27
  [ ] Edge cases and error conditions are tested

Documentation:
  [ ] README updated if public behavior changed
  [ ] CHANGELOG updated with the change description
  [ ] Docstrings accurate and complete

Security:
  [ ] All input validated
  [ ] No injection vulnerabilities
  [ ] No secrets in code or logs
  [ ] Dependencies checked for known CVEs

Review:
  [ ] Self-review completed using §18 checklist
  [ ] Change summary provided to reviewer
  [ ] All acceptance criteria (§28) pass
```

### Validation Rules

- The DoD is non-negotiable. A task that passes 9 of 10 items is NOT done.
- If a DoD item is not applicable (e.g., "CHANGELOG updated" for an internal refactor), it must be explicitly marked "N/A — [reason]."
- Teams may ADD to the DoD but may not REMOVE items without stakeholder approval.

### AI Implementation Notes

- Check every DoD item before declaring work complete.
- If you cannot verify a DoD item (e.g., you cannot actually run `pytest`), state what you verified mentally and what requires manual verification.
- Never mark work as "done" if any DoD item is incomplete. If blocked, state the blocker.

---

## 30. Future Roadmap

### Purpose

The Future Roadmap captures features, capabilities, and improvements that are planned for future versions but are explicitly OUT OF SCOPE for the current phase. It provides direction without creating scope pressure.

### Requirements

| ID | Requirement |
|---|---|
| RD-01 | Organize roadmap by target version or timeframe. |
| RD-02 | Each item must include: feature description, estimated effort, dependencies, and status. |
| RD-03 | Roadmap items must NOT influence current architecture unless explicitly agreed. |

### Example

```
v1.0 (Post-MVP):
  [ ] Batch scanning from file (FR-002)               — Medium — No blockers
  [ ] HTML report generation                           — Medium — Requires template engine
  [ ] Configuration file support (.toml)               — Small  — No blockers
  [ ] Custom rule definitions                          — Large  — Requires rule engine design

v2.0 (Future):
  [ ] Web UI dashboard                                 — X-Large — Requires frontend stack
  [ ] Plugin/extension system                          — Large   — Requires architecture review
  [ ] Distributed scanning via task queue              — Large   — Requires Redis/RabbitMQ
  [ ] API server mode (REST)                           — Large   — Requires web framework
  [ ] Integration with CI/CD platforms (native)        — Medium  — Per-platform effort

v3.0 (Aspirational):
  [ ] Real-time monitoring and alerting                — X-Large — Requires persistent storage
  [ ] Compliance reporting (SOC 2, PCI DSS)            — Large   — Requires compliance mapping
  [ ] Multi-protocol support (FTP, SMTP, DNS)          — Large   — Per-protocol effort
```

### Validation Rules

- Roadmap items must not be implemented in the current phase unless explicitly moved to §7 (Scope).
- "Architecture for future extensibility" is acceptable ONLY if it adds no complexity to the current scope.
- Effort estimates are indicative, not commitments.

### AI Implementation Notes

- Do NOT implement roadmap items. Do NOT build abstractions, hooks, or extension points for them unless the current architecture naturally supports them.
- If a roadmap item would significantly benefit from a current architecture decision (e.g., using protocols/ABCs at a boundary that a future plugin system would use), mention it as a note — but do not add complexity for it.
- Reference roadmap items when explaining why something is out of scope: "OS-005 defers the plugin system to v2.0."

---

## Appendix A — Requirement Traceability Matrix

Use this matrix to verify every requirement is covered by implementation, tests, and acceptance criteria.

```
| Requirement | Module(s)         | Test(s)                    | Acceptance Criteria |
|-------------|-------------------|----------------------------|---------------------|
| FR-001      | header_analyzer   | test_header_analyzer.py    | AC-001, AC-002      |
| FR-002      | main, http_client | test_batch_scan.py         | AC-003              |
| NF-001      | http_client       | test_performance.py        | AC-001 (timing)     |
| SR-001      | main, validators  | test_input_validation.py   | AC-002              |
```

### AI Implementation Notes

- After completing all modules, fill in this matrix to verify full coverage.
- Any FR without a test is a gap. Any test without an FR may be unnecessary.

---

## Appendix B — Glossary

Define project-specific terms to avoid ambiguity:

```
| Term       | Definition                                                  |
|------------|-------------------------------------------------------------|
| Finding    | A single security observation with severity and remediation |
| Scan       | The complete analysis of one URL across all analyzers       |
| Analyzer   | A module that checks one category of security properties    |
| Report     | The aggregated output of a scan (text, JSON, or HTML)       |
| Target     | The URL being scanned                                       |
```

---

## Appendix C — Document Approval

| Role | Name | Date | Signature |
|---|---|---|---|
| Project Lead | [TBD] | [TBD] | [ ] |
| Technical Lead | [TBD] | [TBD] | [ ] |
| Security Lead | [TBD] | [TBD] | [ ] |
| Product Owner | [TBD] | [TBD] | [ ] |

---

*End of document. No implementation shall begin until all ⚠️ requirements are satisfied and this document is in APPROVED status.*
