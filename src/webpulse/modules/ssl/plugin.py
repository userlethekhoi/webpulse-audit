"""SSL/TLS analyzer plugin for WebPulse.

Decodes peer certificate expiry, domain matching parameters, and validity states.
"""

import logging
from datetime import UTC, datetime

import httpx

from webpulse.modules.base import BasePlugin, PluginMetadata
from webpulse.reports.schemas import Evidence, Finding, Severity, Target
from webpulse.utils.network import AsyncNetworkClient

logger = logging.getLogger("webpulse.modules.ssl")


class SslPlugin(BasePlugin):
    """Built-in SSL/TLS Certificate Auditor Plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="webpulse-ssl-analyzer",
            category="ssl",
            version="2.0.0",
        )

    async def execute(self, target: Target, client: AsyncNetworkClient) -> list[Finding]:
        findings: list[Finding] = []

        # Extract hostname and port
        try:
            url_parts = httpx.URL(target.url)
            host = url_parts.host
            if not host:
                raise ValueError(f"Target URL lacks hostname: {target.url}")
            port = url_parts.port or (443 if url_parts.scheme == "https" else 80)
        except Exception as e:
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="SSL Target Parsing Error",
                    severity=Severity.MEDIUM,
                    confidence=1.0,
                    description=f"Failed to extract host parameters from target URL: {e}",
                    remediation="Ensure the target URL conforms to standard RFC URI formatting.",
                    evidence=[Evidence(type="cert_property", data=str(e))],
                )
            )
            return findings

        # Skip SSL validation checks if the target scheme is HTTP
        if url_parts.scheme == "http" and port == 80:
            logger.info(f"Skipping SSL certificate check for HTTP target: {target.url}")
            return findings

        # 1. Initiate TLS check
        cert_info = await client.check_ssl(host, port)

        if "error" in cert_info:
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="SSL Connection Handshake Failure",
                    severity=Severity.HIGH,
                    confidence=1.0,
                    description=(
                        f"Outbound TLS handshake failed with host '{host}': "
                        f"{cert_info['error']}"
                    ),
                    remediation=(
                        "Verify the server supports active TLS connections "
                        "and is bound on the correct port."
                    ),
                    evidence=[Evidence(type="cert_property", data=cert_info["error"])],
                )
            )
            return findings

        # 2. Check Expiry/Validity
        valid = cert_info.get("valid", False)
        expiry_str = cert_info.get("expiry_date", "")

        if not valid:
            findings.append(
                Finding(
                    plugin_name=self.metadata.name,
                    category=self.metadata.category,
                    target_url=target.url,
                    title="SSL Certificate Expired or Invalid",
                    severity=Severity.CRITICAL,
                    confidence=1.0,
                    description=f"The SSL/TLS certificate for host '{host}' is expired or invalid.",
                    remediation=(
                        "Install a valid, non-expired TLS certificate "
                        "from a trusted Certificate Authority (CA)."
                    ),
                    evidence=[
                        Evidence(
                            type="cert_property",
                            data=f"Expiration Date: {expiry_str}",
                        )
                    ],
                )
            )
            return findings

        # 3. Check Near-Expiry Threshold Warning
        # default to 14 days warning threshold limit
        verify_days = self.config.get("verify_expiry_days", 14)
        try:
            expiry_date = datetime.fromisoformat(expiry_str)
            now = datetime.now(UTC)
            delta = expiry_date - now

            if delta.days < verify_days:
                findings.append(
                    Finding(
                        plugin_name=self.metadata.name,
                        category=self.metadata.category,
                        target_url=target.url,
                        title="SSL Certificate Expiring Soon",
                        severity=Severity.HIGH,
                        confidence=1.0,
                        description=(
                            f"The SSL/TLS certificate for '{host}' expires in {delta.days} days, "
                            f"which is below the threshold of {verify_days} days."
                        ),
                        remediation=(
                            "Renew the SSL/TLS certificate immediately "
                            "to prevent service disruptions."
                        ),
                        evidence=[
                            Evidence(
                                type="cert_property",
                                data=f"Expires on: {expiry_str} (Remaining: {delta.days} days)",
                            )
                        ],
                    )
                )
        except Exception as e:
            logger.debug(f"Failed to check certificate expiration threshold: {e}")

        return findings
