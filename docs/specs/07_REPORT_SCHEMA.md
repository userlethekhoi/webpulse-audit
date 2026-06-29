# 07_REPORT_SCHEMA.md — WebPulse Report Schema Specification (v2.0)

## 1. Purpose
This document specifies the schema, structural layout, and data formats for WebPulse reports. It defines the JSON Schema interface and details how report outputs are rendered in Console, Markdown, HTML, and future PDF formats.

---

## 2. Overview
WebPulse generates a unified scan report containing target metadata, crawler discovery logs, authentication status audits, detailed findings, recommendations, evidence logs, and calculated scores. The output must be parsable programmatically while remaining readable for humans.

---

## 3. JSON Schema Specification

The following JSON Schema defines the official structure for the WebPulse JSON export (`report.json`):

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WebPulseScanReport",
  "type": "object",
  "required": ["metadata", "crawler_summary", "auth_summary", "scores", "findings"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["target_url", "scan_timestamp", "engine_version", "duration_seconds"],
      "properties": {
        "target_url": { "type": "string", "format": "uri" },
        "scan_timestamp": { "type": "string", "format": "date-time" },
        "engine_version": { "type": "string" },
        "duration_seconds": { "type": "number" }
      }
    },
    "crawler_summary": {
      "type": "object",
      "required": ["max_depth", "max_pages", "pages_discovered", "pages_scanned", "scanned_urls"],
      "properties": {
        "max_depth": { "type": "integer" },
        "max_pages": { "type": "integer" },
        "pages_discovered": { "type": "integer" },
        "pages_scanned": { "type": "integer" },
        "scanned_urls": {
          "type": "array",
          "items": { "type": "string", "format": "uri" }
        }
      }
    },
    "auth_summary": {
      "type": "object",
      "required": ["auth_enabled", "auth_status"],
      "properties": {
        "auth_enabled": { "type": "boolean" },
        "auth_status": { "type": "string", "enum": ["SUCCESS", "FAILED", "DISABLED", "TIMEOUT"] }
      }
    },
    "scores": {
      "type": "object",
      "required": ["overall_health_score", "risk_score", "categories"],
      "properties": {
        "overall_health_score": { "type": "integer", "minimum": 0, "maximum": 100 },
        "risk_score": { "type": "number", "minimum": 0.0, "maximum": 10.0 },
        "categories": {
          "type": "object",
          "properties": {
            "security": { "type": "integer" },
            "seo": { "type": "integer" },
            "performance": { "type": "integer" },
            "accessibility": { "type": "integer" }
          }
        }
      }
    },
    "findings": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/Finding"
      }
    }
  },
  "definitions": {
    "Finding": {
      "type": "object",
      "required": ["id", "plugin_name", "category", "target_url", "title", "severity", "confidence", "description", "remediation"],
      "properties": {
        "id": { "type": "string" },
        "plugin_name": { "type": "string" },
        "category": { "type": "string" },
        "target_url": { "type": "string", "format": "uri" },
        "title": { "type": "string" },
        "severity": { "type": "string", "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] },
        "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
        "description": { "type": "string" },
        "remediation": { "type": "string" },
        "evidence": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type", "data"],
            "properties": {
              "type": { "type": "string", "enum": ["http_header", "html_snippet", "time_ms", "cert_property"] },
              "data": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

---

## 4. Console Output Layout

The Console report prioritizes quick scan visibility. It uses ANSI color coding to denote severity level boundaries:

```
======================================================================
 WEBPULSE WEBSITE AUDIT REPORT
 Target:       https://example.com
 Date:         2026-06-29 16:30:00 UTC
 Crawler:      BFS Scanned 3/20 Pages (Max Depth: 2)
 Auth Status:  SUCCESS (Session Established)
======================================================================

[★] OVERALL HEALTH SCORE: 96 / 100
[!] RISK SCORE:            1.9 / 10

Category Breakdown:
- [Security]      92/100  [PASS]
- [SEO]           100/100 [PASS]
- [Performance]   98/100  [PASS]
- [Accessibility] 100/100 [PASS]

----------------------------------------------------------------------
Discovered Findings:

[CRITICAL] (Confidence: 1.0) - Expiry Alert: SSL Certificate Expiring Soon
  - URL:         https://example.com
  - Description: The target SSL certificate will expire in less than 7 days.
  - Remediation: Renew TLS certificate from Certificate Authority.
  - Evidence: Expiration Date: 2026-07-02T12:00:00Z

[MEDIUM] (Confidence: 1.0) - CSP: Missing Content-Security-Policy Header
  - URL:         https://example.com/login
  - Description: The CSP security header was not detected in HTTP response headers.
  - Remediation: Add "Content-Security-Policy" headers to config.
======================================================================
```

---

## 5. Markdown Report Format

The Markdown writer generates a `report.md` output containing collapsible headings for evidence:

```markdown
# WebPulse Scan Report: `https://example.com`

**Scan Timestamp:** `2026-06-29T16:30:00Z`  
**Crawl Stats:** Discovered 3 pages at maximum depth 2.  
**Auth Status:** `SUCCESS`  
**Overall Health Score:** **96 / 100**  
**Risk Level:** **1.9 / 10 (Low Risk)**

## Category Scores
| Category | Score | Status |
|---|---|---|
| Security | 92 / 100 | Pass |
| Performance | 98 / 100 | Pass |
| Accessibility | 100 / 100 | Pass |
| SEO | 100 / 100 | Pass |

## Discovered Findings

### [CRITICAL] SSL Certificate Expiring Soon
* **URL:** `https://example.com`
* **Module:** `ssl-analyzer`
* **Confidence:** `1.0`
* **Description:** The target SSL certificate expires in less than 7 days.
* **Remediation:** Renew the certificate immediately.
* **Evidence:**
  ```yaml
  expiration_date: "2026-07-02T12:00:00Z"
  issuer: "Let's Encrypt Authority X3"
  ```
```

---

## 6. HTML Report Specification
* **Layout:** Single-page application template with responsive navigation sidebar.
* **Aesthetics:** Sleek dark-mode default styling, utilizing CSS gradients for score displays and interactive tables.
* **Charts:** Built-in charts (radial bar charts for scores) rendered using SVG paths, avoiding external script dependencies.
* **Interactivity:** Support local sorting and filtering of findings tables by category, severity, and page URL.

---

## 7. Future PDF Exporter Specification
In future releases, a headless PDF report will be built using a styling template that converts the HTML structure directly into PDF bytes using `weasyprint` or an equivalent headless generator.

---

## 8. Design Decisions
* **Decision:** We use absolute, self-contained SVG styling inside the HTML report template rather than loading chart libraries (e.g. Chart.js) from external CDNs.
* **Rationale:** Ensures report files remain readable offline and prevents cross-site scripting risks and network failure issues on isolated networks.

---

## 9. References
* JSON Schema Draft 7 Specification: https://json-schema.org/specification-links.html#draft-7
* SARIF OASIS Standard Schema: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html

---

## 10. Validation Rules
* Every finding array element in a generated JSON report must validate against the `$ref: "#/definitions/Finding"` schema definition.
* Finding IDs must be generated using a deterministic SHA-256 hash of the target URL, plugin name, and finding title to support issue tracking over time.

---

## 11. Engineering Notes
* When writing the JSON exporter, ensure floating-point metrics (like Risk Score and duration) are formatted to a maximum of 2 decimal places.

---

## 12. AI Notes
* Do not edit the output structure format. Ensure all new keys added to the Python finding dataclasses are documented and updated in this schema file.
