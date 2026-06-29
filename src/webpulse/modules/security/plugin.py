"""Security analyzer plugin for WebPulse.

Audits security response headers, probes for sensitive file exposures (.git, .env),
and detects SQL injection vulnerabilities via error-based, boolean-blind, and time-based techniques.
"""

import logging
import re
import time
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Evidence, Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient

logger = logging.getLogger("webpulse.modules.security")

# ── SQL Injection Payloads ──────────────────────────────────────────────────

SQLI_PAYLOADS: list[tuple[str, str]] = [
    # (label, payload) — payload is appended to the parameter value
    ("single-quote", "'"),
    ("double-quote", '"'),
    ("tautology-or", "' OR '1'='1"),
    ("comment-or", "' OR 1=1--"),
    ("comment-or-hash", "' OR 1=1#"),
    ("boolean-and-true", "' AND '1'='1"),
    ("boolean-and-false", "' AND '1'='2"),
]

SQLI_TIME_PAYLOADS: list[tuple[str, str, float]] = [
    # (label, payload, min_sleep_seconds) for time-based blind detection
    ("mysql-sleep", "' AND SLEEP(3)--", 2.5),
    ("pgsql-sleep", "'; SELECT pg_sleep(3)--", 2.5),
    ("mssql-waitfor", "'; WAITFOR DELAY '00:00:03'--", 2.5),
]

# ── SQL Error Patterns ──────────────────────────────────────────────────────

SQL_ERROR_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("MySQL", re.compile(
        r"(SQL syntax.*MySQL|MySQL.*syntax|mysql_fetch|mysql_num_rows|"
        r"MySQL server version|Warning.*mysql_|You have an error in your SQL|"
        r"MySQLSyntaxErrorException|com\.mysql\.jdbc)",
        re.IGNORECASE,
    )),
    ("PostgreSQL", re.compile(
        r"(PostgreSQL.*ERROR|psql:|pg_query\(\)|pg_exec\(\)|"
        r"org\.postgresql\.util\.PSQLException)",
        re.IGNORECASE,
    )),
    ("SQL Server", re.compile(
        r"(Microsoft OLE DB.*SQL Server|SQL Server.*Driver|"
        r"Unclosed quotation mark|ODBC SQL Server Driver|"
        r"com\.microsoft\.sqlserver|SqlException|System\.Data\.SqlClient)",
        re.IGNORECASE,
    )),
    ("Oracle", re.compile(
        r"(ORA-\d{4,5}|Oracle.*Driver|java\.sql\.SQLSyntaxErrorException|"
        r"PLS-\d{4}|ORA\d{4,5})",
        re.IGNORECASE,
    )),
    ("SQLite", re.compile(
        r"(SQLite.*error|SQLITE_ERROR|sqlite3\.OperationalError|"
        r"near \".*\": syntax error)",
        re.IGNORECASE,
    )),
    ("Generic SQL", re.compile(
        r"(SQLSTATE\[\d+\]|database error|syntax error.*SQL|"
        r"unclosed quotation|ODBC.*Driver|JDBC.*Exception|"
        r"DB2 SQL Error|SQLCODE|SQLERRM|Sybase.*message)",
        re.IGNORECASE,
    )),
]


class SecurityPlugin(BasePlugin):
    """Built-in Security Auditor Plugin with SQL injection detection."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-security-analyzer",
            category="security",
            version="2.1.0",
        )

    # ── Public API ───────────────────────────────────────────────────────

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        findings: list[Finding] = []

        try:
            # 1. Fetch main target response
            response = await client.request("GET", target.url)
            headers = response.headers

            # 2. Check CSP
            if "Content-Security-Policy" not in headers:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Content-Security-Policy Header",
                        severity=Severity.MEDIUM,
                        confidence=1.0,
                        description=(
                            "The Content-Security-Policy (CSP) header is missing from HTTP responses. "
                            "CSP mitigates cross-site scripting (XSS) and data injection vulnerabilities."
                        ),
                        remediation=(
                            "Configure the web server to append a strict "
                            "Content-Security-Policy response header."
                        ),
                        evidence=[],
                    )
                )

            # 3. Check HSTS
            url_parts = httpx.URL(target.url)
            if url_parts.scheme == "https" and "Strict-Transport-Security" not in headers:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Strict-Transport-Security Header",
                        severity=Severity.HIGH,
                        confidence=1.0,
                        description=(
                            "The Strict-Transport-Security (HSTS) header is missing from "
                            "HTTPS responses. HSTS forces browsers to connect only via HTTPS, "
                            "preventing downgrade attacks."
                        ),
                        remediation=(
                            "Configure the server to return a 'Strict-Transport-Security' "
                            "header with a max-age parameter."
                        ),
                        evidence=[],
                    )
                )

            # 4. Check X-Frame-Options
            if "X-Frame-Options" not in headers and "frame-ancestors" not in headers.get(
                "Content-Security-Policy", ""
            ):
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing Anti-Clickjacking Header",
                        severity=Severity.LOW,
                        confidence=1.0,
                        description=(
                            "Neither the 'X-Frame-Options' header nor CSP 'frame-ancestors' "
                            "directives were found. This leaves the site vulnerable to clickjacking."
                        ),
                        remediation="Configure the server to return 'X-Frame-Options: DENY' or 'SAMEORIGIN'.",
                        evidence=[],
                    )
                )

            # 5. Check X-Content-Type-Options
            x_content_type = headers.get("X-Content-Type-Options", "").lower()
            if x_content_type != "nosniff":
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Missing or Invalid X-Content-Type-Options Header",
                        severity=Severity.LOW,
                        confidence=1.0,
                        description=(
                            "The 'X-Content-Type-Options' header is missing or not set to 'nosniff'. "
                            "This allows browsers to MIME-sniff response types, increasing scripting risks."
                        ),
                        remediation="Configure the server to return 'X-Content-Type-Options: nosniff'.",
                        evidence=[
                            Evidence(
                                type="http_header",
                                data=(
                                    "X-Content-Type-Options header: "
                                    f"'{headers.get('X-Content-Type-Options', 'MISSING')}'"
                                ),
                            )
                        ],
                    )
                )

            # 6. Check Cookie Security Flags
            cookies = response.headers.get_list("Set-Cookie")
            if cookies:
                insecure_cookies = []
                for cookie in cookies:
                    cookie_lower = cookie.lower()
                    missing_flags = []
                    if "httponly" not in cookie_lower:
                        missing_flags.append("HttpOnly")
                    if "secure" not in cookie_lower and url_parts.scheme == "https":
                        missing_flags.append("Secure")

                    if missing_flags:
                        cookie_name = cookie.split("=")[0].strip()
                        insecure_cookies.append(
                            f"{cookie_name} (missing: {', '.join(missing_flags)})"
                        )

                if insecure_cookies:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="Insecure Cookie Flags Detected",
                            severity=Severity.MEDIUM,
                            confidence=1.0,
                            description=(
                                "One or more cookies were set without the 'HttpOnly' or 'Secure' flags. "
                                "Missing HttpOnly allows client-side script token theft; "
                                "missing Secure permits cookie transit over plain text."
                            ),
                            remediation=(
                                "Set the 'Secure' and 'HttpOnly' flags on all "
                                "application session cookies."
                            ),
                            evidence=[
                                Evidence(
                                    type="http_header",
                                    data=f"Insecure cookies: {', '.join(insecure_cookies)}",
                                )
                            ],
                        )
                    )

            # 7. Run SQL Injection Checks
            sqli_enabled = self.config.get("sqli_check", True)
            if sqli_enabled:
                sqli_findings = await self._run_sqli_checks(target, client)
                findings.extend(sqli_findings)

            # 8. Sensitive Directory / File Leaks Checks
            if url_parts.port:
                base_url = f"{url_parts.scheme}://{url_parts.host}:{url_parts.port}/"
            else:
                base_url = f"{url_parts.scheme}://{url_parts.host}/"

            # Check .git exposure
            git_url = f"{base_url}.git/HEAD"
            try:
                git_resp = await client.request("GET", git_url)
                if git_resp.status_code == 200 and "ref:" in git_resp.text:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="Exposed Git Repository Directory Detected",
                            severity=Severity.CRITICAL,
                            confidence=1.0,
                            description=(
                                f"The target Git repository database is exposed publicly at '{git_url}'. "
                                "Attackers can download the entire repository source code and commit history."
                            ),
                            remediation=(
                                "Restrict public access to the '.git/' directory "
                                "in server routing or web configs."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=(
                                        "Exposed Git header contents: "
                                        f"'{git_resp.text[:50].strip()}'"
                                    ),
                                )
                            ],
                        )
                    )
            except Exception as e:
                logger.debug(f"Git exposure check failed: {e}")

            # Check .env exposure
            env_url = f"{base_url}.env"
            try:
                env_resp = await client.request("GET", env_url)
                if env_resp.status_code == 200 and any(
                    k in env_resp.text for k in ("DB_", "API_", "SECRET_", "PASSWORD", "PORT=")
                ):
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="Exposed System Environment File Detected",
                            severity=Severity.CRITICAL,
                            confidence=1.0,
                            description=(
                                f"The system environment configuration file is exposed publicly at '{env_url}'. "
                                "This file contains sensitive cleartext database credentials, API keys, and configurations."
                            ),
                            remediation=(
                                "Delete or move the '.env' file out of the web document root, "
                                "and block access in server configuration rules."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=(
                                        "Exposed .env snippets: " f"'{env_resp.text[:100].strip()}'"
                                    ),
                                )
                            ],
                        )
                    )
            except Exception as e:
                logger.debug(f"Env exposure check failed: {e}")

        except Exception as e:
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="Security Analyzer Scan Failure",
                    severity=Severity.MEDIUM,
                    confidence=1.0,
                    description=f"Security Analyzer failed to process target: {e}",
                    remediation=(
                        "Verify target host is active, online, " "and returning valid HTTP headers."
                    ),
                    evidence=[Evidence(type="http_header", data=str(e))],
                )
            )

        return findings

    # ── SQL Injection Detection ───────────────────────────────────────────

    @staticmethod
    def _extract_query_params(url: str) -> dict[str, str]:
        """Extract query parameters from a URL as a dict."""
        parsed = urlparse(url)
        return dict(parse_qsl(parsed.query))

    @staticmethod
    def _inject_payload(url: str, param: str, payload: str) -> str:
        """Inject a SQLi payload into a specific query parameter of a URL."""
        parsed = urlparse(url)
        params = dict(parse_qsl(parsed.query))
        if param not in params:
            return url
        params[param] = params[param] + payload
        new_query = urlencode(params)
        return urlunparse(parsed._replace(query=new_query))

    async def _fetch_safely(
        self, client: AsyncNetworkClient, url: str
    ) -> tuple[int, str, float]:
        """Fetch a URL and return (status_code, body_text, elapsed_seconds)."""
        start = time.monotonic()
        try:
            resp = await client.request("GET", url)
            elapsed = time.monotonic() - start
            return resp.status_code, resp.text, elapsed
        except Exception:
            elapsed = time.monotonic() - start
            return 0, "", elapsed

    async def _run_sqli_checks(
        self, target: Target, client: AsyncNetworkClient
    ) -> list[Finding]:
        """Orchestrate error-based, boolean-blind, and time-based SQLi checks."""
        findings: list[Finding] = []
        params = self._extract_query_params(target.url)
        if not params:
            return findings

        for param_name in params:
            # ── Error-based detection ──────────────────────────────────
            for label, payload in SQLI_PAYLOADS:
                injected_url = self._inject_payload(target.url, param_name, payload)
                try:
                    status, body, _elapsed = await self._fetch_safely(
                        client, injected_url
                    )
                except Exception:
                    logger.debug(f"Error-based SQLi request failed for {injected_url}", exc_info=True)
                    continue

                matched_db = self._match_sql_error(body)
                if matched_db:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title=f"SQL Injection Vulnerability Detected — Error-Based ({matched_db})",
                            severity=Severity.CRITICAL,
                            confidence=0.95,
                            description=(
                                f"Parameter '{param_name}' at {target.url} appears vulnerable to "
                                f"SQL injection. The server returned a {matched_db} error message "
                                f"when payload '{label}' was injected, indicating the input is "
                                "directly interpolated into SQL queries without sanitization."
                            ),
                            remediation=(
                                f"Use parameterized queries (prepared statements) for all database "
                                f"access involving user input. Sanitize and validate the '{param_name}' "
                                "parameter. Apply a Web Application Firewall (WAF) rule to block SQL "
                                "metacharacters."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=(
                                        f"Injected URL: {injected_url}\n"
                                        f"Payload: {payload}\n"
                                        f"DB Engine: {matched_db}\n"
                                        f"Response status: {status}\n"
                                        f"Error snippet: {body[:300].strip()}"
                                    ),
                                )
                            ],
                        )
                    )
                    break  # Stop checking this param once a confirmed error is found

            # ── Boolean-blind detection ────────────────────────────────
            true_url = self._inject_payload(target.url, param_name, "' AND '1'='1")
            false_url = self._inject_payload(target.url, param_name, "' AND '1'='2")
            try:
                _st_true, body_true, _el_true = await self._fetch_safely(
                    client, true_url
                )
                _st_false, body_false, _el_false = await self._fetch_safely(
                    client, false_url
                )
                len_diff = abs(len(body_true) - len(body_false))
                # Significant length difference suggests boolean-blind SQLi
                if len_diff > 500 and body_true and body_false:
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="SQL Injection Vulnerability Detected — Boolean-Based Blind",
                            severity=Severity.HIGH,
                            confidence=0.80,
                            description=(
                                f"Parameter '{param_name}' at {target.url} shows significantly "
                                f"different response sizes ({len(body_true)} vs {len(body_false)} "
                                f"bytes) when injected with boolean-true vs boolean-false SQL "
                                "payloads. This behavior indicates potential blind SQL injection."
                            ),
                            remediation=(
                                f"Use parameterized queries for the '{param_name}' parameter. "
                                "Implement input validation and apply WAF rules to detect SQL "
                                "injection attempts."
                            ),
                            evidence=[
                                Evidence(
                                    type="html_snippet",
                                    data=(
                                        f"Boolean-true URL: {true_url}\n"
                                        f"Boolean-false URL: {false_url}\n"
                                        f"Response length (true): {len(body_true)} bytes\n"
                                        f"Response length (false): {len(body_false)} bytes\n"
                                        f"Difference: {len_diff} bytes"
                                    ),
                                )
                            ],
                        )
                    )
            except Exception:
                logger.debug("Boolean-blind SQLi check failed", exc_info=True)

            # ── Time-based blind detection ──────────────────────────────
            for label, time_payload, min_sleep in SQLI_TIME_PAYLOADS:
                try:
                    injected_url = self._inject_payload(target.url, param_name, time_payload)
                    _status, _body, elapsed = await self._fetch_safely(
                        client, injected_url
                    )
                    if elapsed >= min_sleep:
                        findings.append(
                            Finding(
                                plugin_name=self.metadata.name,
                                category=self.metadata.category,
                                target_url=target.url,
                                title="SQL Injection Vulnerability Detected — Time-Based Blind",
                                severity=Severity.HIGH,
                                confidence=0.85,
                                description=(
                                    f"Parameter '{param_name}' at {target.url} caused a delayed "
                                    f"response ({elapsed:.1f}s) when the time-based payload "
                                    f"'{label}' was injected, indicating the database executed "
                                    "a SLEEP/WAITFOR command."
                                ),
                                remediation=(
                                    f"Use parameterized queries for the '{param_name}' parameter. "
                                    "Set a query timeout on the database server. Apply WAF rules "
                                    "to detect time-delay injection attempts."
                                ),
                                evidence=[
                                    Evidence(
                                        type="time_ms",
                                        data=(
                                            f"Injected URL: {injected_url}\n"
                                            f"Payload: {time_payload}\n"
                                            f"Response time: {elapsed:.2f}s (threshold: {min_sleep}s)"
                                        ),
                                    )
                                ],
                            )
                        )
                        break
                except TimeoutError:
                    # Timeout itself may indicate time-based SQLi
                    findings.append(
                        Finding(
                            plugin_name=self.metadata.name,
                            category=self.metadata.category,
                            target_url=target.url,
                            title="SQL Injection Vulnerability Detected — Time-Based Blind (Timeout)",
                            severity=Severity.HIGH,
                            confidence=0.75,
                            description=(
                                f"Parameter '{param_name}' at {target.url} caused the request to "
                                f"time out when the time-based payload '{label}' was injected. "
                                "This suggests database-level command execution."
                            ),
                            remediation=(
                                f"Use parameterized queries for the '{param_name}' parameter. "
                                "Set query timeouts and apply WAF rules."
                            ),
                            evidence=[
                                Evidence(
                                    type="time_ms",
                                    data=(
                                        f"Injected URL: {target.url}?{param_name}=[PAYLOAD]\n"
                                        f"Payload: {time_payload}\n"
                                        f"Result: Request timed out"
                                    ),
                                )
                            ],
                        )
                    )
                    break
                except Exception:
                    logger.debug(f"Time-based SQLi request failed for {param_name}", exc_info=True)
                    continue

        return findings

    @staticmethod
    def _match_sql_error(body: str) -> str | None:
        """Check response body for known SQL error patterns. Returns DB engine name or None."""
        if not body:
            return None
        for db_name, pattern in SQL_ERROR_PATTERNS:
            if pattern.search(body):
                return db_name
        return None
