# 13_AI_AGENT_GUIDE.md — AI Agent Integration & Coding Manual (v2.0)

## 1. Purpose
This document provides instructions for AI Coding Agents (such as Claude Code, Cursor, RooCode, etc.) working on the WebPulse codebase. It establishes coding limits, forbidden behaviors, architectural boundaries, and naming standards to ensure code safety and style consistency.

---

## 2. Overview
WebPulse is built on a highly modular, async-first Python architecture. AI agents must understand the dependency boundaries, plugin structures, and test patterns before attempting to write or refactor code.

---

## 3. Core Naming Conventions & Terminology
To maintain consistency across the codebase, AI agents must strictly follow these naming rules:

* **File Names:** All python module files must use `snake_case` (e.g. `plugin_loader.py`, `html_parser.py`).
* **Class Names:** All class definitions must use `PascalCase` (e.g. `PluginLoader`, `AsyncScheduler`).
* **Method & Function Names:** Use `snake_case` with action verbs (e.g. `execute()`, `discover_plugins()`, `validate_manifest()`).
* **Constants:** Global constants must use `UPPER_SNAKE_CASE` (e.g. `DEFAULT_RATE_LIMIT`, `MAX_RETRIES`).
* **Private Methods:** Prefix with a single underscore to denote module-private status (e.g. `_resolve_dependencies()`).

### 3.1 Terminology Vocabulary Check
AI agents must use uniform terminology. Never use these words interchangeably:
* Use **`Target`** (The target model/URL scanned), never *Host*, *Domain*, *URI*, or *Site*.
* Use **`Finding`** (The object representing a scanner audit issue), never *Issue*, *Result*, or *Vulnerability*.

---

## 4. Architectural Import Constraints

To prevent circular imports and maintain strict layer separation, AI agents must follow these dependency rules:

```
┌──────────────────┐
│  webpulse.core   │ (Cannot import from webpulse.modules or webpulse.reports)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ webpulse.modules │ (Can import from webpulse.core and webpulse.utils)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ webpulse.reports │ (Can import from webpulse.modules and webpulse.core)
└────────────────────────────────────────────────────────────────────────┘
```

* **Core Protection:** Code in `webpulse/core/` must never import from `webpulse/modules/` or `webpulse/reports/`.
* **Plugin Interfaces:** Plugins must interact with the core via abstract base classes in `webpulse.modules.base`. Do not import concrete core classes inside analyzer modules.
* **Shared Network Client:** Plugins must use the shared client instance injected via the DI container instead of instantiating `httpx.AsyncClient` directly.

---

## 5. Forbidden Behaviors (Red Flags)

AI agents must **never** engage in the following practices:

* ❌ **No Global Event Loop Manipulation:** Do not call `asyncio.get_event_loop()` or modify the active loop policy. Let the CLI engine control loop initialization.
* ❌ **No Blocking Calls in Async Paths:** Never call blocking IO functions (e.g. `time.sleep()`, `urllib.request()`, or synchronous file reads) within async methods. Use `asyncio.sleep()`, `aiofiles`, or run blocking operations in an executor thread.
* ❌ **No CPU-Bound Execution in main thread:** Never run HTML parsing (BeautifulSoup) or technology fingerprint searches inside the main event loop thread. You must offload them using `asyncio.to_thread` or `loop.run_in_executor`.
* ❌ **No Direct Sockets or Raw Requests:** Never bypass `AsyncNetworkClient` to make outbound HTTP requests. Network clients enforce critical SSRF validations.
* ❌ **No Bare Exception Catching:** Never write `except:` or `except Exception: pass`. Always catch specific exception classes (e.g. `httpx.RequestError`) and log or raise them accordingly.
* ❌ **No Exploitation Payloads:** Do not write methods that construct exploit payloads or attempt brute forcing. Keep the code strictly defensive as defined in `11_NON_GOALS.md`.

---

## 6. Phase-Gated AI Implementation Workflow

When assigned a coding task in this repository, follow these steps sequentially:

1. **Phase 1 (Design Review):** Read relevant spec files in `docs/specs/`. Write a concise implementation plan before modifying any code.
2. **Phase 2 (Dependency Verification):** Check if your changes require new dependencies. Verify they conform to the allowed dependencies in `02_PRODUCT_REQUIREMENTS.md`.
3. **Phase 3 (Write Tests First):** Add failing unit test definitions in the `tests/` directory representing the new feature or bug fix (TDD approach).
4. **Phase 4 (Build & Fix):** Write the minimal source code needed to make the tests pass.
5. **Phase 5 (Lint & Type-Check):** Run `ruff` and `mypy` locally to ensure compliance. Clean up all type errors.

---

## 7. Design Decisions
* **Decision:** We require AI agents to verify class structures using Python's typing system (`mypy` static analysis) during local runs.
* **Rationale:** AI agents occasionally fail to match signatures on abstract base class methods. Strict type-checking catches these discrepancies immediately before committing.

---

## 8. References
* Python Typing PEP 484: https://peps.python.org/pep-0484/
* PEP 8 Style Guide: https://peps.python.org/pep-0008/

---

## 9. Validation Rules
* Any generated python file must contain `# type: ignore` comments only when interacting with third-party libraries that lack type stubs.
* Every class constructor must document its injected parameters in its docstring.

---

## 10. Engineering Notes
* If your prompt context gets congested, review this guide to re-align with core architectural conventions.

---

## 11. AI Self-Checklist
Before submitting your code review request, verify:
- [ ] No circular imports were introduced.
- [ ] No raw `print()` statements are left in the code.
- [ ] Test coverage for new lines of code is $\ge$ 90%.
- [ ] All network operations use the injected async client with timeouts.
- [ ] All CPU-bound DOM parsing calls are offloaded to background threads.
