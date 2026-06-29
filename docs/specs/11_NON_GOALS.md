# 11_NON_GOALS.md — Ethical Boundaries & Non-Goals (v2.0)

## 1. Purpose
This document establishes the ethical boundaries, legal constraints, and operational non-goals for the WebPulse framework. It defines the limits of features to ensure the tool remains a defensive website auditing framework, protecting it from modification into offensive tools.

---

## 2. Overview
WebPulse is engineered for diagnostic site analysis, performance monitoring, accessibility validation, and configuration scanning. It is designed to identify problems so they can be fixed. It is not designed to exploit targets.

---

## 3. Explicit Non-Goals
The following categories are explicitly outside the scope of the project. WebPulse will **never** support or implement features in these domains:

```
                  ┌──────────────────────────────┐
                  │      WEBPULSE IS NOT:        │
                  ├──────────────────────────────┤
                  │  ✗ A Malware / Payload Tool  │
                  │  ✗ An Exploitation Framework │
                  │  ✗ A Brute-Force Cracker     │
                  │  ✗ A Phishing Platform       │
                  │  ✗ A Denial of Service Tool  │
                  └──────────────────────────────┘
```

### 3.1 Not a Vulnerability Exploitation Framework
WebPulse scans for the presence of vulnerabilities (e.g. missing CSP, exposed environment files, expired SSL certificates). It will **never** contain exploits to execute shellcode, hijack sessions, modify database states, or bypass access controls.

### 3.2 Not a Brute-Force or Credential-Stuffing Tool
WebPulse will not include modules to perform directory busting (brute forcing millions of paths), password guessing on login forms, or dictionary attacks on administrative endpoints.

### 3.3 Not a Malware or Ransomware Simulator
WebPulse is not a red-team adversary emulation platform. It does not generate malware payloads, test egress firewalls with command-and-control (C2) agents, or simulate ransomware file encryption.

### 3.4 Not a Phishing Toolkit
It will not provide tools to clone websites, track phishing campaigns, generate credential-harvesting landing pages, or send automated email templates.

### 3.5 Not a DDoS / Denial-of-Service Client
While WebPulse includes a Stress Testing Module to assess site capacity limits under load, it is strictly rate-limited and configured for authorized, single-origin testing. It will never include botnet capabilities or asymmetric load generation payloads designed to crash external infrastructure.

### 3.6 Not an Intranet Port Scanner by Default
To prevent abusive port scanning of local area networks or cloud metadata endpoints, WebPulse blocks private network IPs (RFC 1918 / 6890 ranges) by default, requiring explicit user authorization via CLI flags.

---

## 4. Safety Controls & Stress Testing Rules

To enforce compliance with these ethical boundaries, the **Stress Testing Module** is governed by these safety limits:

1. **Authorization Gate:** The stress test module will fail immediately with exit code 1 unless the CLI argument `--yes-i-have-authorization` is explicitly provided.
2. **Strict Rate Limiting Caps:** The engine enforces a hard-coded threshold cap of 200 requests per second (RPS) on outgoing requests to prevent accidental server overloading.
3. **User-Agent Declaration:** The engine appends a distinct identifier (`WebPulse-Audit-Agent/2.0 (Defensive Security Scanner; +https://github.com/webpulse/webpulse)`) to all outbound HTTP headers, allowing firewall administrators to track or block scan traffic easily.

---

## 5. Design Decisions
* **Decision:** We hardcode the maximum rate limit ceiling (200 RPS) directly inside the core `webpulse.core.scheduler` module.
* **Rationale:** Placing this check in the core scheduler prevents any third-party plugin from bypassing rate limit caps by writing custom loops.

---

## 6. Future Considerations
* If a plugin is detected to be doing brute-forcing or active exploitation during manifest analysis, the loader will throw a fatal safety exception and block execution.

---

## 7. References
* OWASP Code of Conduct: https://owasp.org/www-policy/operational/code-of-conduct
* HackerOne Vulnerability Disclosure Guidelines: https://www.hackerone.com/vulnerability-disclosure-guidelines

---

## 8. Validation Rules
* Any PR introducing payload generation, active exploitation, or signature databases for exploitation tools will be rejected by default.
* The `--yes-i-have-authorization` check must be evaluated in the core scheduler before the stress-test plugin is executed.

---

## 9. Engineering Notes
* Always ensure that error codes generated during authorization failure specify instructions on how the user must obtain scan permission from their network team.

---

## 10. AI Notes
* Do not generate code that implements password guessing, payload injection, or database cracking.
* If a user requests a brute-force module, reference this document and refuse to implement it.
