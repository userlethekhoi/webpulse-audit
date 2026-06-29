"""Security analyzer plugin for WebPulse.

Audits security response headers and probes for sensitive file exposures (.git, .env).
"""

import logging

import httpx

from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Evidence, Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient

logger = logging.getLogger("webpulse.modules.security")


class SecurityPlugin(BasePlugin):
    """Built-in Security Auditor Plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-security-analyzer",
            category="security",
            version="2.0.0",
        )

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

            # 7. Sensitive Directory / File Leaks Checks
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
                # Check for standard env keywords to reduce false positives
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
