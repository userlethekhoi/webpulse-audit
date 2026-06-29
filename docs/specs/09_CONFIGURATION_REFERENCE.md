# 09_CONFIGURATION_REFERENCE.md — Configuration Reference (v2.0)

## 1. Purpose
This document specifies the WebPulse configuration system. It details the hierarchical resolution rules, scanning profile presets, environment variable bindings, and validation schemas, serving as the interface contract for system configurability.

---

## 2. Overview
WebPulse utilizes a hierarchical configuration model where local settings override global settings, and CLI arguments take absolute precedence. Configuration is structured, type-validated at boot time, and supports profiles for different scanning intensities.

---

## 3. Configuration File Formats
WebPulse supports three configuration file formats:
* **YAML (Default):** Parsed via `webpulse.yaml` or `webpulse.yml`.
* **JSON:** Parsed via `webpulse.json`.
* **TOML:** Parsed via `webpulse.toml`.

---

## 4. Priority Resolution Hierarchy
When WebPulse resolves settings, it applies the following priority rules (1 has the highest priority):

```
[1] CLI Arguments overrides
     └── [2] Environment Variables
          └── [3] Workspace Config (webpulse.yaml in CWD)
               └── [4] User Global Config (~/.webpulse/config.yaml)
                    └── [5] Engine Defaults (Defined in Pydantic Schemas)
```

### 4.1 Environment Variable Bindings
Environment variables must be prefixed with `WEBPULSE_` followed by the configuration path using double underscores (`__`) to separate sections:
* `WEBPULSE__CORE__RATE_LIMIT=50` overrides `core.rate_limit`.
* `WEBPULSE__MODULES__PERFORMANCE__USE_BROWSER=true` overrides `modules.performance.use_browser`.

---

## 5. Standard Configuration Schema (YAML Example)

```yaml
# webpulse.yaml - Project Level Configuration (v2.0)

core:
  rate_limit: 15          # Max requests per second
  max_connections: 30     # Max concurrent connections
  timeout: 12             # In seconds
  sandbox_plugins: true   # Run third-party plugins in subprocess workers
  fail_on_health: 80      # Exit code 2 if health score < 80
  fail_on_critical: true  # Exit code 3 if any CRITICAL is found

network:
  allow_private_ips: false # SSRF protection gate. Blocks loopback/local scan ranges if false.
  user_agent: "WebPulse-Audit-Agent/2.0 (Defensive Website Audit Tool)"

profile: "default"        # Active profile preset ("fast", "default", "full")

# Web Crawler Settings
crawler:
  enabled: true
  max_depth: 2
  max_pages: 15
  follow_subdomains: false
  exclude_patterns:
    - "\\.pdf$"
    - "\\.zip$"
    - "/logout"

# Target Authentications configuration
auth:
  enabled: false
  login_url: "https://example.com/api/v1/auth/login"
  method: "post_json"      # Options: post_form, post_json, headers
  credentials:
    username: "${WEBPULSE_AUTH_USER}"
    password: "${WEBPULSE_AUTH_PASS}"
  token_injection:
    type: "cookie"         # Options: cookie, header
    name: "session_id"

modules:
  security:
    enabled: true
    check_paths:
      - "/.git/config"
      - "/.env"
    require_headers:
      - "Content-Security-Policy"
      - "Strict-Transport-Security"
  seo:
    enabled: true
    check_meta_description: true
  waf:
    enabled: true
    confidence_threshold: 40
  performance:
    enabled: true
    use_browser: false
    connection_timeout_ms: 5000
  ssl:
    enabled: true
    verify_expiry_days: 14

reporting:
  formats:
    - "console"
    - "json"
  output_dir: "./webpulse-reports"
  report_name_template: "webpulse-report-{target}-{timestamp}"
```

---

## 6. Scan Profiles

WebPulse ships with three default profiles:

| Profile | Active Modules | Concurrency | Headless Browser | Target Use Case |
|---|---|---|---|---|
| **fast** | HTTP, WAF, SSL | High (50) | No | Fast footprinting of multiple endpoints. |
| **default** | All except Browser checks | Medium (25) | No | Fast, dependency-free local scans. |
| **full** | All | Low (10) | Yes | Comprehensive SEO, accessibility, and Core Web Vitals checks. |

---

## 7. Secrets Management

WebPulse modules (such as PageSpeed API checking or custom webhook reporting plugins) may require secrets.
* **Storage:** Secrets must never be stored inside `webpulse.yaml`. They must be injected via environment variables (e.g. `WEBPULSE_API_TOKEN`) or loaded from files utilizing the `secret_file` property.
* **Validation:** The engine verifies that required secret variables are populated before running any plugin requiring them, aborting early if missing.

---

## 8. Design Decisions
* **Decision:** We use Pydantic models to validate the parsed configuration dictionaries.
* **Rationale:** Pydantic provides type coercion, schema generation, and informative validation error messages natively, eliminating manual dictionary checking.

---

## 9. References
* YAML Spec 1.2: https://yaml.org/spec/1.2.2/
* Pydantic Settings management: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

## 10. Validation Rules
* Any key in a configuration file must match a property in `webpulse.core.config.AppConfig`.
* The `rate_limit` configuration parameter must be an integer between 1 and 200.

---

## 11. Engineering Notes
* When loading configuration files, catch parser errors (such as YAML syntax errors) and present them with line numbers in the terminal error message.

---

## 12. AI Notes
* Do not read configuration values using direct dictionary accesses (`config["core"]["rate_limit"]`); always access them via Pydantic model attributes (`config.core.rate_limit`).
