# IMPLEMENTATION_WORKFLOW.md — AI Agent Software Development Lifecycle

> **Classification:** Engineering Process Standard  
> **Version:** 1.0  
> **Status:** ACTIVE  
> **Effective Date:** YYYY-MM-DD  
> **Owner:** Principal Engineering — AI-Assisted Development  
> **Companion Documents:**  
> - [AI_CODING_SYSTEM_PROMPT.md](./AI_CODING_SYSTEM_PROMPT.md) — Agent behavioral rules  
> - [PROJECT_REQUIREMENTS.md](./PROJECT_REQUIREMENTS.md) — Requirements specification

---

## Executive Summary

This document defines a **mandatory, phase-gated software development lifecycle** (SDLC) for AI coding agents. It enforces disciplined, incremental delivery with human review at every critical decision point.

**No phase may be skipped. No gate may be bypassed. No implementation may begin without explicit human approval.**

The workflow is modeled on enterprise SDLC practices — adapted for the unique characteristics of AI agents: finite context windows, lack of persistent memory, potential for hallucination, and the need for human oversight on architectural decisions.

---

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI AGENT DEVELOPMENT LIFECYCLE                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                   │
│  │   PHASE 0    │  Project Analysis                                 │
│  │  DISCOVERY   │  Read requirements. Understand scope.             │
│  └──────┬───────┘                                                   │
│         │ Output: Analysis Report                                   │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 1    │  Architecture Design                              │
│  │   DESIGN     │  Define structure, patterns, data flow.           │
│  └──────┬───────┘                                                   │
│         │ Output: Architecture Document                             │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 2    │  Dependency Analysis                              │
│  │ DEPENDENCIES │  Evaluate, justify, lock dependencies.            │
│  └──────┬───────┘                                                   │
│         │ Output: Dependency Manifest                               │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 3    │  Implementation Plan                              │
│  │  PLANNING    │  Break work into ordered, reviewable units.       │
│  └──────┬───────┘                                                   │
│         │ Output: Implementation Plan                               │
│         ▼                                                           │
│  ╔══════════════╗                                                   │
│  ║  GATE G1     ║  ★ HUMAN APPROVAL REQUIRED ★                     │
│  ║  PLAN REVIEW ║  Review all Phase 0–3 outputs.                    │
│  ╚══════╤═══════╝  Approve, reject, or revise.                     │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 4    │  Implementation Sprint N                          │
│  │  BUILD (N)   │  Implement one unit from the plan.                │
│  └──────┬───────┘                                                   │
│         │ Output: Working code + tests                              │
│         ▼                                                           │
│  ╔══════════════╗                                                   │
│  ║  GATE G2     ║  ★ HUMAN REVIEW REQUIRED ★                       │
│  ║ SPRINT REVIEW║  Review code, tests, quality.                     │
│  ╚══════╤═══════╝  Approve, reject, or revise.                     │
│         │                                                           │
│         ├── More units? ──→ Loop back to PHASE 4                    │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 5    │  Integration & Verification                       │
│  │  INTEGRATE   │  Wire modules. Run full test suite.               │
│  └──────┬───────┘                                                   │
│         │ Output: Integrated system + test results                  │
│         ▼                                                           │
│  ╔══════════════╗                                                   │
│  ║  GATE G3     ║  ★ HUMAN APPROVAL REQUIRED ★                     │
│  ║ FINAL REVIEW ║  Full system review. DoD verification.            │
│  ╚══════╤═══════╝                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────┐                                                   │
│  │   PHASE 6    │  Delivery & Handoff                               │
│  │   DELIVER    │  Documentation. Packaging. Deployment notes.      │
│  └──────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Cardinal Rules

These rules are absolute and override all other workflow instructions.

| # | Rule | Consequence of Violation |
|---|---|---|
| 1 | **No phase may be skipped.** | All subsequent work is invalid. Restart from the skipped phase. |
| 2 | **No gate may be bypassed.** | Implementation produced without gate approval must be discarded. |
| 3 | **No implementation before Gate G1 approval.** | Code written before plan approval is wasted effort and must be deleted. |
| 4 | **No forward progress during a WAIT state.** | The agent must stop tool calls and wait for human input. |
| 5 | **Every phase must produce its required outputs.** | A phase without outputs is not complete. |
| 6 | **Rollback must be possible at every phase.** | If rollback is impossible, the approach is too risky. |
| 7 | **Context must be preserved across phases.** | If context is lost (new session), re-read outputs from completed phases before continuing. |

---

## Phase 0 — Project Analysis

### Objectives

1. Achieve complete understanding of the project requirements, constraints, and scope.
2. Identify all ambiguities, gaps, and risks in the requirements documentation.
3. Establish the foundational context that all subsequent phases depend on.
4. Determine whether the project is feasible within stated constraints.

### Inputs

| Input | Source | Required |
|---|---|---|
| Project requirements document | `PROJECT_REQUIREMENTS.md` or equivalent | ⚠️ Yes |
| Existing codebase (if brownfield) | Repository / workspace | If applicable |
| System prompt / coding standards | `AI_CODING_SYSTEM_PROMPT.md` or equivalent | Recommended |
| Stakeholder priorities | Human engineer | ⚠️ Yes |

### Process

```
Step 0.1: Read the requirements document in its entirety.
Step 0.2: Read the system prompt / coding standards if provided.
Step 0.3: If brownfield — inventory the existing codebase:
          - Directory structure
          - Key modules and their responsibilities
          - Existing patterns, conventions, dependencies
          - Test infrastructure
Step 0.4: Identify and document:
          - All functional requirements (what the system must do)
          - All non-functional requirements (how well it must do it)
          - All constraints (what limits implementation choices)
          - All assumptions (what is believed but not verified)
Step 0.5: Identify gaps, ambiguities, and conflicts in requirements.
Step 0.6: Assess feasibility against constraints (time, technology, scope).
Step 0.7: Produce the Analysis Report.
```

### Outputs

**Analysis Report** — A structured document containing:

```markdown
## Analysis Report — {PROJECT_NAME}

### 1. Project Understanding
[2–3 paragraph summary of what the project does, who it's for, and why it exists]

### 2. Requirements Summary
| Category | Count | Status |
|----------|-------|--------|
| Functional Requirements | N | Complete / Has gaps |
| Non-Functional Requirements | N | Complete / Has gaps |
| Constraints | N | Verified / Unverified |
| Assumptions | N | Risk-assessed |

### 3. Identified Gaps
[List of missing or ambiguous requirements that must be resolved]

### 4. Identified Risks
| Risk | Severity | Mitigation |
|------|----------|------------|
| [Description] | High/Medium/Low | [Strategy] |

### 5. Feasibility Assessment
[Can this project be built within the stated constraints? Yes/No/Conditional]

### 6. Questions for Stakeholder
[Numbered list of questions that must be answered before proceeding]
```

### Required Checks

- [ ] Every section of the requirements document has been read
- [ ] Every blocking requirement (⚠️) has been verified as present
- [ ] All gaps have been documented with specific questions
- [ ] All risks have been assessed and documented
- [ ] Feasibility has been evaluated against all constraints
- [ ] No assumptions have been made about missing information

### Approval Gate

**None** — Phase 0 is informational. However, if the Analysis Report contains questions (§6), the agent **MUST WAIT** for answers before proceeding to Phase 1. Unresolved questions are blocking.

### Rollback Strategy

Phase 0 produces only documentation — no code, no configuration, no files. Rollback is trivial: discard the Analysis Report and repeat the analysis.

### Completion Criteria

| Criterion | Verification |
|---|---|
| All requirements read and understood | Analysis Report §1 is coherent and accurate |
| All gaps identified | §3 is non-empty OR explicitly states "no gaps found" |
| All risks documented | §4 is non-empty OR explicitly states "no significant risks" |
| All blocking questions answered | §6 is empty OR answers have been received |
| Feasibility confirmed | §5 states "Yes" or "Conditional" with accepted conditions |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Requirements document is incomplete | High | High | Identify gaps in §3. Ask before proceeding. |
| Agent misunderstands requirements | Medium | Critical | Analysis Report provides opportunity for human correction. |
| Brownfield codebase has undocumented patterns | Medium | Medium | Inventory existing code thoroughly in Step 0.3. |
| Constraints make project infeasible | Low | Critical | Feasibility assessment in §5 catches this early. |

---

## Phase 1 — Architecture Design

### Objectives

1. Define the high-level system architecture — modules, layers, boundaries, and data flow.
2. Select architectural patterns appropriate to the project's requirements and constraints.
3. Establish dependency direction rules that all implementation must follow.
4. Define the folder structure and module responsibilities.
5. Identify external system boundaries where error handling, timeouts, and retries are critical.

### Inputs

| Input | Source | Required |
|---|---|---|
| Analysis Report | Phase 0 output | ⚠️ Yes |
| Resolved questions | Human engineer responses | ⚠️ Yes (if questions existed) |
| Architecture requirements | `PROJECT_REQUIREMENTS.md` §12 | ⚠️ Yes |
| Constraints | `PROJECT_REQUIREMENTS.md` §10 | ⚠️ Yes |

### Process

```
Step 1.1: Select the architectural style based on project requirements:
          - Pipeline (for data-flow-oriented tools)
          - Layered (for traditional applications)
          - Hexagonal (for high-testability needs)
          - Modular monolith (for medium complexity)
          - Microservice (only if explicitly required)

Step 1.2: Define layers and their responsibilities:
          - Core / Domain (business logic, no I/O)
          - Infrastructure (network, filesystem, database)
          - Interface (CLI, API, UI entry points)

Step 1.3: Define dependency direction:
          - Interface → Core ← Infrastructure
          - Core NEVER imports from Infrastructure or Interface

Step 1.4: Define the folder structure:
          - Every directory has a stated purpose
          - Test directories mirror source directories

Step 1.5: Define module specifications:
          - Each module: name, path, responsibility, public interface
          - Each module: "Does NOT" list (anti-responsibilities)

Step 1.6: Define data flow:
          - Input → Processing → Output chain
          - Identify where concurrency, batching, and streaming are needed

Step 1.7: Define external system boundaries:
          - Network calls, filesystem access, database queries
          - Each boundary requires: error handling, timeout, retry policy

Step 1.8: Produce the Architecture Document.
```

### Outputs

**Architecture Document** — containing:

```markdown
## Architecture Document — {PROJECT_NAME}

### 1. Architectural Style
[Selected style with justification]

### 2. System Layers
[Layer definitions with responsibilities]

### 3. Dependency Direction
[Diagram or description showing allowed dependencies]

### 4. Folder Structure
[Complete directory tree with purpose annotations]

### 5. Module Specifications
[Per-module: name, path, responsibility, interface, dependencies, anti-responsibilities]

### 6. Data Flow
[Input-to-output processing chain]

### 7. External Boundaries
[List of external system touchpoints with error handling requirements]

### 8. Design Decisions
[Key decisions with rationale and alternatives considered]
```

### Required Checks

- [ ] Architectural style is justified against project requirements
- [ ] Dependency direction is unidirectional — no circular dependencies
- [ ] Every module has a single, clear responsibility
- [ ] No module responsibilities overlap
- [ ] Folder structure matches module specifications
- [ ] Data flow covers all functional requirements
- [ ] External boundaries are identified with error handling plans
- [ ] Architecture respects all constraints from Phase 0
- [ ] Design decisions document alternatives and rationale

### Approval Gate

**None** — Phase 1 output will be reviewed at Gate G1 (after Phase 3). However, if the agent identifies a fundamental architectural question with multiple viable approaches and significantly different trade-offs, it **SHOULD** present the options and wait for direction before continuing to Phase 2.

### Rollback Strategy

Phase 1 produces only documentation. Rollback: discard the Architecture Document and redesign from the Analysis Report. No code to revert.

### Completion Criteria

| Criterion | Verification |
|---|---|
| Architectural style selected and justified | §1 is complete with rationale |
| All modules specified | Every file in folder structure has a module spec |
| Dependency direction defined and acyclic | §3 shows no circular paths |
| Data flow covers all FRs | Every FR maps to a point in the data flow |
| External boundaries documented | §7 is non-empty |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Over-engineering architecture for simple projects | Medium | Medium | Match complexity to project size. CLI tools rarely need hexagonal. |
| Under-engineering for complex projects | Low | High | Phase 0 risk assessment should flag complexity. |
| Architecture incompatible with constraints | Low | Critical | Cross-check every decision against constraint list. |
| Architecture not testable | Medium | High | Verify every module can be tested in isolation. |

---

## Phase 2 — Dependency Analysis

### Objectives

1. Identify all external libraries required by the architecture.
2. Evaluate each dependency against project constraints (license, security, maintenance, size).
3. Identify transitive dependencies and assess supply chain risk.
4. Lock dependency versions to ensure reproducible builds.
5. Produce a complete dependency manifest.

### Inputs

| Input | Source | Required |
|---|---|---|
| Architecture Document | Phase 1 output | ⚠️ Yes |
| Dependency Policy | `PROJECT_REQUIREMENTS.md` §26 | ⚠️ Yes |
| Constraints (license, native deps) | `PROJECT_REQUIREMENTS.md` §10 | ⚠️ Yes |

### Process

```
Step 2.1: From the Architecture Document, identify every capability
          that requires an external library:
          - HTTP client → httpx
          - Data validation → pydantic
          - CLI parsing → argparse / typer

Step 2.2: For each dependency, evaluate against the Dependency Policy:
          - Is it actively maintained? (last commit < 6 months)
          - Is the license compatible? (check §10 constraints)
          - Does it have known CVEs? (check advisories)
          - How many transitive dependencies? (< 10 preferred)
          - Does it require native compilation? (check constraints)

Step 2.3: For each dependency, identify alternatives:
          - At least one alternative per dependency
          - Include "standard library only" as an option where feasible
          - Document trade-offs

Step 2.4: Separate runtime vs development dependencies.

Step 2.5: Pin exact versions for all dependencies.

Step 2.6: Produce the Dependency Manifest.
```

### Outputs

**Dependency Manifest** — containing:

```markdown
## Dependency Manifest — {PROJECT_NAME}

### 1. Runtime Dependencies
| Package | Version | Purpose | License | Transitive Deps | CVEs | Alternative |
|---------|---------|---------|---------|-----------------|------|-------------|
| httpx   | 0.27.0  | HTTP    | BSD-3   | 7               | None | aiohttp     |

### 2. Development Dependencies
| Package | Version | Purpose | License |
|---------|---------|---------|---------|
| pytest  | 8.2.0   | Testing | MIT     |

### 3. Constraint Verification
| Constraint | Status |
|------------|--------|
| All licenses permissive | ✅ Pass / ❌ Fail |
| No native compilation required | ✅ Pass / ❌ Fail |
| No unpatched critical CVEs | ✅ Pass / ❌ Fail |

### 4. Supply Chain Risk Assessment
[Overall risk level: Low / Medium / High]
[Justification and any mitigations]

### 5. Lock File
[Reference to pyproject.toml / requirements.txt with pinned versions]
```

### Required Checks

- [ ] Every external import in the architecture has a corresponding dependency
- [ ] Every dependency passes all constraint checks
- [ ] Every dependency has at least one documented alternative
- [ ] License compatibility verified for all dependencies
- [ ] No known critical CVEs in any dependency
- [ ] Versions are pinned to exact releases
- [ ] Runtime and dev dependencies are separated
- [ ] Total transitive dependency count is documented

### Approval Gate

**None** — Phase 2 output will be reviewed at Gate G1 (after Phase 3). However, if a required dependency fails a constraint check (e.g., license incompatibility, native compilation required), the agent **MUST STOP** and escalate to the human engineer for a decision.

### Rollback Strategy

Phase 2 produces only documentation. Rollback: discard the Dependency Manifest. No code, no installed packages, no lock files.

### Completion Criteria

| Criterion | Verification |
|---|---|
| All dependencies identified | Manifest §1 and §2 are complete |
| All constraints verified | §3 shows all-pass or escalated failures |
| Supply chain risk assessed | §4 is complete |
| Versions pinned | §5 references a lock file or pinned versions |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Dependency has undetected vulnerability | Low | High | Pin versions. Monitor CVEs post-deployment. |
| Dependency becomes unmaintained | Low | Medium | Document alternatives for every dependency. |
| License conflict discovered late | Low | Critical | Verify all licenses in Step 2.2 before any code is written. |
| Transitive dependency introduces risk | Medium | Medium | Audit transitive tree. Prefer libraries with minimal deps. |

---

## Phase 3 — Implementation Plan

### Objectives

1. Decompose the architecture into ordered, independently reviewable implementation units.
2. Define the implementation sequence based on dependency order (foundations first).
3. Estimate the scope and complexity of each unit.
4. Define what "done" looks like for each unit (per-unit acceptance criteria).
5. Create the blueprint that the iterative build phase will follow.

### Inputs

| Input | Source | Required |
|---|---|---|
| Architecture Document | Phase 1 output | ⚠️ Yes |
| Dependency Manifest | Phase 2 output | ⚠️ Yes |
| Functional Requirements | `PROJECT_REQUIREMENTS.md` §4 | ⚠️ Yes |
| Acceptance Criteria | `PROJECT_REQUIREMENTS.md` §28 | ⚠️ Yes |
| Definition of Done | `PROJECT_REQUIREMENTS.md` §29 | ⚠️ Yes |

### Process

```
Step 3.1: Identify all implementation units.
          A unit is the smallest piece of work that can be:
          - Implemented independently
          - Tested independently
          - Reviewed independently
          Typical units: one module, one class, one integration point.

Step 3.2: Order units by dependency:
          - Foundation modules first (models, exceptions, config)
          - Core logic modules second (analyzers, processors)
          - Infrastructure modules third (HTTP client, report writer)
          - Integration/wiring fourth (main entry point, CLI)
          - Polish last (documentation, packaging)

Step 3.3: For each unit, define:
          - Files to create or modify
          - Functions/classes to implement
          - Tests to write
          - Dependencies on other units (what must be done first)
          - Estimated complexity (S/M/L)
          - Per-unit acceptance criteria

Step 3.4: Identify units that can be parallelized (no mutual dependencies).

Step 3.5: Produce the Implementation Plan.
```

### Outputs

**Implementation Plan** — containing:

```markdown
## Implementation Plan — {PROJECT_NAME}

### Implementation Sequence

#### Sprint 1: Foundation
| Unit | Files | Complexity | Dependencies | Acceptance |
|------|-------|------------|-------------|------------|
| U-01: Project scaffold | pyproject.toml, __init__.py, ... | S | None | Project installs and imports |
| U-02: Data models | models.py | S | U-01 | Models instantiate, serialize |
| U-03: Exceptions | exceptions.py | S | U-01 | Exceptions raise and catch |
| U-04: Configuration | settings.py | M | U-01, U-02 | Config loads from env/file |

#### Sprint 2: Core Logic
| Unit | Files | Complexity | Dependencies | Acceptance |
|------|-------|------------|-------------|------------|
| U-05: Header analyzer | header_analyzer.py | M | U-02, U-03 | Analyzes headers, returns findings |
| U-06: TLS analyzer | tls_analyzer.py | M | U-02, U-03 | Analyzes TLS, returns findings |
| U-07: Aggregator | aggregator.py | S | U-02 | Combines findings from analyzers |

#### Sprint 3: Infrastructure
| Unit | Files | Complexity | Dependencies | Acceptance |
|------|-------|------------|-------------|------------|
| U-08: HTTP client | http_client.py | M | U-03, U-04 | Fetches URLs with timeout/retry |
| U-09: Report writer | report_writer.py | M | U-02 | Generates JSON/text reports |

#### Sprint 4: Integration
| Unit | Files | Complexity | Dependencies | Acceptance |
|------|-------|------------|-------------|------------|
| U-10: CLI interface | main.py | M | U-04, U-08, U-09 | CLI parses args, runs scan |
| U-11: End-to-end wiring | main.py | M | All above | Full scan pipeline works |

#### Sprint 5: Polish
| Unit | Files | Complexity | Dependencies | Acceptance |
|------|-------|------------|-------------|------------|
| U-12: README | README.md | S | U-10 | Accurate, complete docs |
| U-13: Packaging | pyproject.toml | S | All above | pip install works |

### Parallelization Opportunities
- U-05 and U-06 have no mutual dependency — can be implemented in parallel.
- U-08 and U-09 have no mutual dependency — can be implemented in parallel.

### Total Estimated Units: 13
### Estimated Sprints: 5
```

### Required Checks

- [ ] Every module from the Architecture Document has a corresponding unit
- [ ] Every functional requirement is covered by at least one unit
- [ ] Dependency order is correct — no unit depends on a later unit
- [ ] Every unit has per-unit acceptance criteria
- [ ] Every unit has associated test files
- [ ] Complexity estimates are provided
- [ ] No unit is too large (> 200 lines of implementation, not counting tests)

### Approval Gate

### ★ GATE G1 — PLAN REVIEW ★

**This is a mandatory human approval gate.** The agent must:

1. Present the complete outputs of Phases 0, 1, 2, and 3
2. Highlight key decisions, trade-offs, and risks
3. List all questions or concerns
4. **STOP. WAIT for explicit human approval.**

The human may:
- **APPROVE** — Agent proceeds to Phase 4
- **APPROVE WITH MODIFICATIONS** — Agent updates the plan, then proceeds
- **REJECT** — Agent returns to the specified phase and repeats
- **CANCEL** — Project is abandoned; no further work

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ★ GATE G1: PLAN REVIEW                                     ║
║                                                               ║
║   STATUS: WAITING FOR HUMAN APPROVAL                          ║
║                                                               ║
║   The agent MUST NOT proceed until one of the following       ║
║   is received:                                                ║
║                                                               ║
║     • "Approved" / "Proceed" / "Go ahead"                     ║
║     • "Approved with changes: [details]"                      ║
║     • "Rejected: [reason and target phase]"                   ║
║     • "Cancelled"                                             ║
║                                                               ║
║   ANY implementation before approval is FORBIDDEN.            ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### Rollback Strategy

Phase 3 produces only documentation. Rollback: revise the Implementation Plan based on human feedback. No code to revert.

### Completion Criteria

| Criterion | Verification |
|---|---|
| All modules covered | Unit count ≥ module count from Architecture |
| All FRs traced | Every FR appears in at least one unit's acceptance |
| Dependency order valid | No forward references in the sequence |
| Plan is reviewable | Each unit is small enough to review in one pass |
| Gate G1 passed | Human has given explicit approval |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Plan is too granular (too many tiny units) | Medium | Low | Merge units that are < 20 lines into logical groups |
| Plan is too coarse (units too large) | Medium | Medium | Split units > 200 lines into sub-units |
| Dependency order is wrong | Low | High | Validate by tracing import chains |
| Plan doesn't cover all requirements | Low | Critical | Cross-reference against FR list before presenting |

---

## Phase 4 — Implementation Sprint (Iterative)

> **This phase repeats for each implementation unit (sprint) defined in Phase 3.**
> **Each sprint is followed by Gate G2 — Human Review.**

### Objectives

1. Implement exactly one unit from the Implementation Plan.
2. Write comprehensive tests for the implemented unit.
3. Verify the unit meets its per-unit acceptance criteria.
4. Ensure the unit integrates cleanly with previously implemented units.
5. Produce production-quality code that passes all quality gates.

### Inputs

| Input | Source | Required |
|---|---|---|
| Implementation Plan (approved) | Phase 3 output + Gate G1 approval | ⚠️ Yes |
| Architecture Document | Phase 1 output | ⚠️ Yes |
| Module Specifications | Phase 1 §5 | ⚠️ Yes |
| Previously implemented units | Prior Phase 4 sprints | If applicable |
| Human feedback from prior review | Gate G2 (prior sprint) | If applicable |

### Process

```
Step 4.1: IDENTIFY the current unit from the Implementation Plan.
          Announce: "Starting Sprint N: Unit U-XX — [description]"

Step 4.2: VERIFY prerequisites:
          - All dependency units are complete and approved
          - Human feedback from prior sprint (if any) has been incorporated

Step 4.3: REVIEW the module specification for this unit:
          - Read the responsibility, public interface, dependencies
          - Read the "Does NOT" list
          - Read the per-unit acceptance criteria

Step 4.4: IMPLEMENT the unit:
          - Create source files as specified in the folder structure
          - Implement functions/classes per the module specification
          - Follow all coding standards (types, docstrings, naming)
          - Handle all error cases per §19 (Error Handling)
          - Use logging per §20 (Logging)
          - Implement security controls per §21 (Security)

Step 4.5: WRITE TESTS:
          - Unit tests for every public function
          - Happy path, error paths, edge cases
          - Test file mirrors source file location
          - Tests must be independent and deterministic

Step 4.6: SELF-REVIEW:
          - Run through the Code Review Checklist (applicable tier)
          - Verify type hints, docstrings, error handling
          - Verify no forbidden patterns (bare except, print, hardcoded secrets)
          - Verify backward compatibility with prior units

Step 4.7: VERIFY acceptance criteria:
          - Check every per-unit acceptance criterion
          - Document pass/fail for each

Step 4.8: PRODUCE the Sprint Report.
```

### Outputs

**Working code** — Source files and test files for the implemented unit.

**Sprint Report** — containing:

```markdown
## Sprint N Report — Unit U-XX: [Name]

### Files Created/Modified
| File | Action | Lines |
|------|--------|-------|
| path/to/file.py | Created | 85 |
| tests/unit/test_file.py | Created | 120 |

### Implementation Summary
[Brief description of what was implemented]

### Acceptance Criteria Results
| Criterion | Status |
|-----------|--------|
| [From plan] | ✅ Pass / ❌ Fail |

### Self-Review Results
| Check | Status |
|-------|--------|
| Type hints complete | ✅ |
| Docstrings complete | ✅ |
| Error handling complete | ✅ |
| Tests pass (mental verification) | ✅ |
| No forbidden patterns | ✅ |

### Integration Notes
[How this unit connects to previously completed units]

### Concerns / Questions
[Any issues discovered during implementation]
```

### Required Checks

- [ ] Only one unit is implemented per sprint (no scope creep)
- [ ] All prerequisite units are complete and approved
- [ ] Code follows the module specification exactly
- [ ] All public functions have type hints and docstrings
- [ ] All error paths are handled
- [ ] No forbidden patterns (bare except, print, hardcoded secrets, TODO)
- [ ] Tests cover happy path, error paths, and edge cases
- [ ] Tests are independent and deterministic
- [ ] Per-unit acceptance criteria all pass
- [ ] Self-review checklist completed
- [ ] Code integrates with previously completed units

### Approval Gate

### ★ GATE G2 — SPRINT REVIEW ★

**This is a mandatory human review gate.** After each sprint, the agent must:

1. Present the Sprint Report
2. Highlight any concerns, deviations from plan, or discovered risks
3. **STOP. WAIT for human review.**

The human may:
- **APPROVE** — Agent proceeds to the next sprint
- **APPROVE WITH CHANGES** — Agent applies requested changes, then proceeds
- **REJECT** — Agent reverts the sprint and re-implements
- **PAUSE** — Agent waits for further instruction

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ★ GATE G2: SPRINT REVIEW — Sprint N                        ║
║                                                               ║
║   STATUS: WAITING FOR HUMAN REVIEW                            ║
║                                                               ║
║   Delivered: Unit U-XX — [description]                        ║
║   Files: [N] created, [N] modified                            ║
║   Tests: [N] test functions                                   ║
║   Acceptance: [N/N] criteria passed                           ║
║                                                               ║
║   Awaiting: approve / revise / reject / pause                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### Rollback Strategy

| Scope | Action |
|---|---|
| Single function has issues | Revert the function. Fix and re-present. |
| Entire unit has issues | Delete all files created in this sprint. Re-implement from the module specification. |
| Architectural flaw discovered | Escalate to human. May require returning to Phase 1. |
| Prior unit needs modification | Apply minimal targeted edits to the prior unit. Document the change. Get approval. |

### Completion Criteria

| Criterion | Verification |
|---|---|
| Unit implemented per specification | Code matches module spec §5 |
| All tests written and passing | Test file exists and all assertions would pass |
| Self-review completed | Sprint Report §4 shows all checks passing |
| Acceptance criteria met | Sprint Report §3 shows all criteria passing |
| Gate G2 passed | Human has approved or approved-with-changes |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Implementation deviates from specification | Medium | Medium | Self-review catches deviations before G2 |
| Discovered need to modify prior units | Medium | Medium | Apply minimal edits. Document in Sprint Report. |
| Unit is more complex than estimated | Medium | Low | Split into sub-units if needed. Update the plan. |
| Context window pressure on large units | High | High | Keep units small (< 200 lines). Re-read specs at start. |
| Integration issues with prior units | Medium | Medium | Verify imports and interfaces match before implementing |

---

## Phase 5 — Integration & Verification

### Objectives

1. Wire all implemented units into a complete, functioning system.
2. Run the full test suite and verify all tests pass.
3. Verify all end-to-end acceptance criteria.
4. Verify all non-functional requirements (performance, security, resource usage).
5. Produce a comprehensive verification report.

### Inputs

| Input | Source | Required |
|---|---|---|
| All completed and approved sprint outputs | Phase 4 (all sprints) | ⚠️ Yes |
| Acceptance Criteria | `PROJECT_REQUIREMENTS.md` §28 | ⚠️ Yes |
| Non-Functional Requirements | `PROJECT_REQUIREMENTS.md` §5 | ⚠️ Yes |
| Definition of Done | `PROJECT_REQUIREMENTS.md` §29 | ⚠️ Yes |
| Performance Requirements | `PROJECT_REQUIREMENTS.md` §22 | ⚠️ Yes |

### Process

```
Step 5.1: WIRE all units together in the entry point (main.py / CLI).
          Verify imports resolve across all modules.

Step 5.2: RUN the full test suite (mental simulation or actual execution):
          - All unit tests
          - All integration tests
          - Identify any failures

Step 5.3: VERIFY end-to-end acceptance criteria:
          - Walk through every Given-When-Then scenario
          - Document pass/fail for each

Step 5.4: VERIFY non-functional requirements:
          - Performance: would the system meet response time targets?
          - Security: are all controls in place?
          - Resource usage: are memory/CPU limits respected?

Step 5.5: RUN the Definition of Done checklist for the complete system.

Step 5.6: IDENTIFY any remaining issues, gaps, or concerns.

Step 5.7: PRODUCE the Verification Report.
```

### Outputs

**Verification Report** — containing:

```markdown
## Verification Report — {PROJECT_NAME}

### 1. Test Results
| Category | Total | Pass | Fail | Skip |
|----------|-------|------|------|------|
| Unit | N | N | 0 | 0 |
| Integration | N | N | 0 | 0 |
| E2E | N | N | 0 | 0 |

### 2. Acceptance Criteria Results
| ID | Criterion | Status |
|----|-----------|--------|
| AC-001 | [Description] | ✅ Pass |

### 3. Non-Functional Verification
| Requirement | Target | Actual/Expected | Status |
|-------------|--------|-----------------|--------|
| NF-001 Response Time | < 5s | ~2s estimated | ✅ |
| NF-002 Memory | < 256 MB | ~50 MB estimated | ✅ |

### 4. Definition of Done
| Item | Status |
|------|--------|
| [From DoD] | ✅ / ❌ |

### 5. Known Issues
[Any remaining issues, limitations, or technical debt]

### 6. Security Verification
| Control | Status |
|---------|--------|
| Input validation on all surfaces | ✅ |
| No hardcoded secrets | ✅ |
| TLS verification enabled | ✅ |
```

### Required Checks

- [ ] All modules integrate without import errors
- [ ] Full test suite passes with zero failures
- [ ] All acceptance criteria pass
- [ ] All critical and important NFRs are met
- [ ] Definition of Done checklist passes
- [ ] Security controls verified
- [ ] No TODO/FIXME/HACK comments remain in codebase
- [ ] All public APIs have documentation

### Approval Gate

### ★ GATE G3 — FINAL REVIEW ★

**This is the final mandatory human approval gate.** The agent must:

1. Present the Verification Report
2. Demonstrate (or describe) the complete system working end-to-end
3. List all known issues and limitations
4. **STOP. WAIT for final approval.**

The human may:
- **APPROVE** — Agent proceeds to Phase 6 (Delivery)
- **APPROVE WITH ISSUES** — Agent documents known issues. Proceeds to Phase 6.
- **REJECT** — Agent returns to specified phase for rework
- **REJECT AND REDESIGN** — Agent returns to Phase 1 for architectural changes

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ★ GATE G3: FINAL REVIEW                                    ║
║                                                               ║
║   STATUS: WAITING FOR FINAL APPROVAL                          ║
║                                                               ║
║   Tests:        [N] pass, [N] fail                            ║
║   Acceptance:   [N/N] criteria passed                         ║
║   NFRs:         [N/N] met                                     ║
║   DoD:          [N/N] items complete                          ║
║   Known Issues: [N]                                           ║
║                                                               ║
║   Awaiting: approve / reject / redesign                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### Rollback Strategy

| Scope | Action |
|---|---|
| Integration wiring issue | Fix wiring in entry point. No module changes. |
| Test failure in single unit | Return to that unit's sprint. Fix and re-review (G2). |
| Systemic issue across modules | Escalate. May require return to Phase 1. |
| Performance target not met | Profile, identify bottleneck, propose targeted fix. |

### Completion Criteria

| Criterion | Verification |
|---|---|
| All tests pass | Verification Report §1 shows 0 failures |
| All acceptance criteria pass | §2 shows all-pass |
| All critical NFRs met | §3 shows all critical items passing |
| DoD complete | §4 shows all items passing |
| Gate G3 passed | Human has given final approval |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Integration reveals interface mismatches | Medium | Medium | Module specs defined interfaces. Sprints verified integration. |
| Performance targets not met | Medium | High | Profile and optimize. May require architectural change. |
| Security gap discovered | Low | Critical | Fix immediately. Security is non-negotiable. |
| DoD items missed | Low | Medium | Systematic checklist prevents omissions. |

---

## Phase 6 — Delivery & Handoff

### Objectives

1. Finalize all documentation (README, CHANGELOG, API docs, architecture docs).
2. Prepare the project for deployment, distribution, or handoff to another team.
3. Create packaging and installation artifacts.
4. Produce a final delivery summary.

### Inputs

| Input | Source | Required |
|---|---|---|
| Approved codebase | Phase 5 + Gate G3 | ⚠️ Yes |
| Verification Report | Phase 5 output | ⚠️ Yes |
| Documentation Standards | `PROJECT_REQUIREMENTS.md` §25 | ⚠️ Yes |

### Process

```
Step 6.1: FINALIZE README.md:
          - Accurate project description
          - Installation instructions (verified)
          - Usage examples (verified)
          - Configuration reference
          - Development setup

Step 6.2: FINALIZE CHANGELOG.md:
          - All changes from v0.0.0 to current version
          - Organized by Added, Changed, Fixed, Security

Step 6.3: VERIFY packaging:
          - pyproject.toml / setup.cfg is correct
          - Package installs cleanly: pip install .
          - Entry points are configured (CLI commands)

Step 6.4: CREATE .env.example:
          - All environment variables with placeholder values
          - Comments explaining each variable

Step 6.5: VERIFY .gitignore:
          - __pycache__, *.pyc, .env, dist/, build/, *.egg-info/

Step 6.6: PRODUCE the Delivery Summary.
```

### Outputs

**Delivery Summary** — containing:

```markdown
## Delivery Summary — {PROJECT_NAME} v{VERSION}

### Deliverables
| Artifact | Path | Status |
|----------|------|--------|
| Source code | {project_name}/ | ✅ Complete |
| Tests | tests/ | ✅ Complete |
| README | README.md | ✅ Complete |
| CHANGELOG | CHANGELOG.md | ✅ Complete |
| Package config | pyproject.toml | ✅ Complete |
| Environment template | .env.example | ✅ Complete |
| Git ignore | .gitignore | ✅ Complete |

### Installation Verification
[Steps to install and run, verified working]

### Known Limitations
[From Verification Report §5]

### Recommendations for Next Phase
[Suggestions for the team taking over, referencing Roadmap §30]
```

### Required Checks

- [ ] README is accurate and complete
- [ ] CHANGELOG is up to date
- [ ] Package installs and runs correctly
- [ ] .env.example lists all environment variables
- [ ] .gitignore is comprehensive
- [ ] No TODO/FIXME/HACK comments in codebase
- [ ] No debug artifacts in codebase
- [ ] All files are in their specified locations per folder structure

### Approval Gate

**None** — Phase 6 is the final phase. The Delivery Summary serves as the project handoff document. The human may provide feedback for future improvements, which should be captured in the project's issue tracker or roadmap.

### Rollback Strategy

Phase 6 produces documentation and packaging only. Rollback: revise documentation. No code changes.

### Completion Criteria

| Criterion | Verification |
|---|---|
| All deliverables present | Delivery Summary table shows all ✅ |
| Installation verified | Project installs and runs from clean environment |
| Documentation accurate | README matches actual behavior |
| No loose ends | No TODO/FIXME/HACK in codebase |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Documentation doesn't match code | Medium | Medium | Verify every README instruction by running it |
| Packaging configuration is wrong | Low | Medium | Test installation in a clean environment |
| Missing files in deliverables | Low | Low | Check every file against folder structure |

---

## Session Continuity Protocol

AI coding agents may lose context between sessions (new conversation, context window exhaustion, session timeout). This protocol ensures work can be resumed correctly.

### Starting a New Session

When resuming work in a new session, the agent must:

```
Step C.1: Read this workflow document.
Step C.2: Identify the current phase from the latest output artifact.
Step C.3: Read all output artifacts from completed phases:
          - Analysis Report (Phase 0)
          - Architecture Document (Phase 1)
          - Dependency Manifest (Phase 2)
          - Implementation Plan (Phase 3)
          - Sprint Reports (Phase 4, all completed sprints)
Step C.4: Identify the next unit to implement.
Step C.5: Announce: "Resuming from Phase [N], Sprint [N], Unit U-XX."
Step C.6: Proceed from the identified point — do NOT repeat completed work.
```

### Context Preservation Artifacts

Every phase output is a persistence artifact. The agent relies on these to reconstruct context after a session break. They must be:

- Written to stable file paths (not ephemeral chat messages)
- Self-contained (understandable without prior conversation context)
- Kept up to date (modified when plans change)

### Session Handoff Protocol

If a different agent continues the work (e.g., switching from Claude to Gemini):

1. The new agent must read all output artifacts from completed phases
2. The new agent must NOT repeat completed phases
3. The new agent must NOT change architectural decisions without re-entering Gate G1
4. The new agent must follow this workflow document exactly

---

## Appendix A — Phase Transition Rules

```
Phase 0 → Phase 1:
  Requires: Analysis Report complete. All blocking questions answered.
  Forbidden if: Analysis Report has unanswered questions in §6.

Phase 1 → Phase 2:
  Requires: Architecture Document complete.
  Forbidden if: Architectural questions are pending human decision.

Phase 2 → Phase 3:
  Requires: Dependency Manifest complete. All constraints pass.
  Forbidden if: Any dependency fails a constraint check without resolution.

Phase 3 → Phase 4:
  Requires: Implementation Plan complete. Gate G1 APPROVED.
  Forbidden if: Gate G1 has not been explicitly approved by a human.

Phase 4 Sprint N → Phase 4 Sprint N+1:
  Requires: Sprint N Gate G2 APPROVED. All prerequisite units complete.
  Forbidden if: Sprint N has not been reviewed and approved.

Phase 4 (last sprint) → Phase 5:
  Requires: All sprints complete and approved.
  Forbidden if: Any sprint is unapproved or has pending changes.

Phase 5 → Phase 6:
  Requires: Verification Report complete. Gate G3 APPROVED.
  Forbidden if: Gate G3 has not been explicitly approved by a human.
```

---

## Appendix B — Gate Decision Reference

| Gate | Approver | Acceptable Responses | Result |
|---|---|---|---|
| G1 | Human Engineer | Approve / Approve with mods / Reject / Cancel | Proceed / Revise / Redo / Stop |
| G2 | Human Engineer | Approve / Approve with changes / Reject / Pause | Next sprint / Fix then next / Redo sprint / Wait |
| G3 | Human Engineer | Approve / Approve with issues / Reject / Redesign | Deliver / Deliver with notes / Rework / Restart |

---

## Appendix C — Emergency Procedures

### Discovered Critical Security Vulnerability

1. **STOP** all implementation work.
2. Document the vulnerability: what, where, severity, exploitability.
3. Escalate to human engineer immediately.
4. Do NOT proceed until the vulnerability is addressed.

### Discovered Fundamental Architecture Flaw

1. **STOP** all implementation work.
2. Document the flaw: what doesn't work, why, which units are affected.
3. Escalate to human engineer.
4. Human decides: targeted fix (continue from current phase) or redesign (return to Phase 1).

### Context Window Exhaustion

1. Produce a **handoff summary** before context is lost:
   - Current phase and sprint
   - What was just completed
   - What is next
   - Any pending concerns
2. Write the summary to a file (not just chat).
3. Follow the Session Continuity Protocol when resuming.

### Unresolvable Conflict Between Requirements

1. Document the conflict: which requirements, what the contradiction is.
2. Present both interpretations with implications.
3. **WAIT** for human decision. Do NOT choose an interpretation.

---

*End of document. This workflow is mandatory for all AI-assisted development sessions. No phase may be skipped. No gate may be bypassed.*
