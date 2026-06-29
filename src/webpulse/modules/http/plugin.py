"""HTTP analyzer plugin for WebPulse.

Audits redirection paths, server compression configurations, status codes, and HTTP version compatibility.
"""

from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Evidence, Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient


class HttpPlugin(BasePlugin):
    """Built-in HTTP Auditor Plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-http-analyzer",
            category="http",
            version="2.0.0",
        )

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        findings: list[Finding] = []

        try:
            # 1. Initiate outbound GET request
            response = await client.request("GET", target.url)

            # 2. Check Redirect Hop Limits
            hops = len(response.history)
            if hops > 5:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Excessive HTTP Redirect Hops Detected",
                        severity=Severity.MEDIUM,
                        confidence=1.0,
                        description=(
                            f"The target URL generated a chain of {hops} redirect hops. "
                            "Excessive redirects slow down client load performance."
                        ),
                        remediation=(
                            "Optimize server redirect configurations to redirect clients "
                            "directly to the destination resource."
                        ),
                        evidence=[
                            Evidence(
                                type="http_header",
                                data=f"Redirect chain: {' -> '.join(str(r.url) for r in response.history)}",
                            )
                        ],
                    )
                )

            # 3. Check HTTP Compression (Gzip / Brotli)
            content_encoding = response.headers.get("Content-Encoding", "").lower()
            supported = any(c in content_encoding for c in ("gzip", "br", "deflate"))
            if not supported:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="HTTP Compression Disabled",
                        severity=Severity.LOW,
                        confidence=1.0,
                        description=(
                            "The server did not return a Content-Encoding header containing "
                            "gzip, br, or deflate. Uncompressed content transfers consume "
                            "excess bandwidth."
                        ),
                        remediation=(
                            "Configure the web server (e.g. Nginx, Apache) to enable "
                            "gzip or Brotli compression."
                        ),
                        evidence=[
                            Evidence(
                                type="http_header",
                                data=(
                                    "Content-Encoding header: "
                                    f"'{response.headers.get('Content-Encoding', 'MISSING')}'"
                                ),
                            )
                        ],
                    )
                )

            # 4. Check HTTP/2 Protocol Version Support
            version_bytes = response.extensions.get("http_version", b"HTTP/1.1")
            http_version = version_bytes.decode("ascii")
            if http_version not in ("HTTP/2", "HTTP/3"):
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="HTTP/2 Protocol Not Supported",
                        severity=Severity.INFO,
                        confidence=0.9,
                        description=(
                            f"The target website is serving resources over {http_version}. "
                            "Older protocol versions lack multiplexing benefits, increasing "
                            "page load delays."
                        ),
                        remediation=(
                            "Enable HTTP/2 or HTTP/3 support on the web server or CDN configurations."
                        ),
                        evidence=[
                            Evidence(
                                type="http_header", data=f"Negotiated HTTP Version: {http_version}"
                            )
                        ],
                    )
                )

            # 5. Check Server Errors
            status = response.status_code
            if status >= 500:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="Server Response Error Code Returned",
                        severity=Severity.HIGH,
                        confidence=1.0,
                        description=(
                            f"The server returned a server-side error code (HTTP {status}) "
                            "during auditing."
                        ),
                        remediation="Inspect server-side application exception logs to resolve runtime crashes.",
                        evidence=[Evidence(type="http_header", data=f"HTTP Status: {status}")],
                    )
                )

        except Exception as e:
            # Generate a warning finding for connection errors
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="HTTP Connection Scan Failure",
                    severity=Severity.MEDIUM,
                    confidence=1.0,
                    description=f"HTTP Analyzer failed to connect to target URL: {e}",
                    remediation=(
                        "Verify target host is active, online, and accepts outbound "
                        "HTTP requests."
                    ),
                    evidence=[Evidence(type="http_header", data=str(e))],
                )
            )

        return findings
