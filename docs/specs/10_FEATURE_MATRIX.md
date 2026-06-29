# 10_FEATURE_MATRIX.md — Feature Matrix & Roadmap (v2.0)

## 1. Purpose
This document defines the lifecycle roadmap, feature maturity matrix, and version availability for the WebPulse auditing framework. It aligns the development team and community contributors on current, future, experimental, and deprecated capabilities.

---

## 2. Overview
WebPulse is developed in incremental phases, progressing from a fast, low-dependency CLI auditing tool to an enterprise-grade distributed system. The feature matrix below acts as our release map.

---

## 3. WebPulse Version Release Roadmap

| Feature / Capability | Category | v1 (MVP) | v2 (Core) | v3 (Scale) | v4 (Enterprise) |
|---|---|---|---|---|---|
| **Async CLI Engine Core** | Core | Stable | Stable | Stable | Stable |
| **SSRF Network Filter** | Security | Stable | Stable | Stable | Stable |
| **Subprocess Plugin Sandbox**| Security | Stable | Stable | Stable | Stable |
| **BFS Crawler Module** | Core | Stable | Stable | Stable | Stable |
| **Session Auth coordinator**| Core | Stable | Stable | Stable | Stable |
| **Thread Pool CPU offloading**| Core | Stable | Stable | Stable | Stable |
| **8 Built-in Audit Modules** | Core | HTTP-only | Stable (Browser) | Stable | Stable |
| **Console & JSON Reports** | Reports | Stable | Stable | Stable | Stable |
| **Markdown Exporter** | Reports | Stable | Stable | Stable | Stable |
| **Interactive HTML Reports**| Reports | — | Stable | Stable | Stable |
| **PDF Exporter** | Reports | — | — | Stable | Stable |
| **SARIF Output Format** | Reports | — | — | Stable | Stable |
| **Playwright Browser Auditing**| Performance | — | Stable | Stable | Stable |
| **REST API & Worker Daemon** | Platform | — | — | Stable | Stable |
| **Local Dashboard Desktop app**| Platform | — | — | — | Stable |
| **AI Auto-Remediation Agents** | Platform | — | — | Experimental | Stable |

---

## 4. Feature Status Definitions

To clearly delineate feature maturity, the framework labels all APIs and modules under one of the following states:

### 4.1 Stable
Fully tested, secure, and production-ready. Backed by semantic versioning compatibility guarantees.

### 4.2 Experimental
In active testing. Enabled via `--enable-experimental` CLI flags. API structures may change in minor releases.

### 4.3 Deprecated
Scheduled for removal in the next major version. Trigger warnings inside console and logs when utilized.

### 4.4 Removed
No longer present in the codebase. Attempts to invoke trigger exit code 1.

---

## 5. Design Decisions
* **Decision:** We place browser-based checks (Performance Web Vitals and Accessibility audits) under Version 2, rather than forcing them into Version 1.
* **Rationale:** Integrating Playwright dramatically increases container image size and adds system dependency requirements (Chromium drivers). Restricting v1 to HTTP-only ensures the framework remains zero-configuration and runs out-of-the-box in minimal runner environments.

---

## 6. Future Considerations
* We plan to support WebAssembly (Wasm) runtime sandbox engines in Version 3 to enable cross-platform plugin execution (e.g. plugins written in Go/Rust) without requiring Python compilation dependencies.

---

## 7. References
* Semantic Versioning (SemVer) 2.0.0: https://semver.org/
* CNCF Feature Maturity Guidelines: https://github.com/cncf/toc/blob/main/process/graduation_criteria.md

--- 

## 8. Validation Rules
* No module marked as "Experimental" can be set as an active default in the standard configuration profiles.
* Deprecation warnings must run through standard python warnings framework (`warnings.warn()`).

---

## 9. Engineering Notes
* Prior to graduating any feature from "Experimental" to "Stable", it must demonstrate zero memory leaks across a 1000-scan stress execution loop.

---

## 10. AI Notes
* Do not implement features scheduled for v2/v3 inside v1 PRs unless explicitly instructed. Keep pull requests focused on v1 targets.
* Pay attention to the experimental tag boundaries when referencing imports.
