"""Async network client utility for WebPulse.

Implements a secure async HTTP/SSL client supporting outbound SSRF checks
(blocking RFC 1918 and RFC 6890 private IP ranges by default) and async TLS handshakes.
"""

import asyncio
import contextlib
import ipaddress
import logging
import socket
import ssl
from datetime import UTC, datetime
from typing import Any

import httpx
from cryptography import x509
from cryptography.hazmat.backends import default_backend

from webpulse.core.exceptions import SecurityException

logger = logging.getLogger("webpulse.utils.network")


def is_private_ip(ip_str: str) -> bool:
    """Check if the provided IP address is in a private, loopback, or local range.

    Covers RFC 1918, RFC 6890, loopback, link-local, multicast, and reserved ranges.

    Args:
        ip_str: String representation of the IP address.

    Returns:
        True if the IP is private or reserved, False otherwise.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        # Invalid IP formats are blocked as unsafe by default
        return True


class AsyncNetworkClient:
    """SSRF-safe HTTP client wrapper and SSL transaction tool."""

    def __init__(
        self,
        allow_private_ips: bool = False,
        user_agent: str = "WebPulse-Audit-Agent/2.0 (Defensive Website Audit Tool)",
        timeout: float = 10.0,
    ) -> None:
        """Initialize the AsyncNetworkClient.

        Args:
            allow_private_ips: If True, bypasses SSRF filters for private/local networks.
            user_agent: Custom User-Agent string to inject.
            timeout: Global timeout for network connections in seconds.
        """
        self.allow_private_ips = allow_private_ips
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent},
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )
        logger.debug(
            f"Initialized AsyncNetworkClient (allow_private_ips={allow_private_ips}, "
            f"timeout={timeout})"
        )

    async def _resolve_host(self, host: str) -> list[str]:
        """Resolve a host name to its IP addresses asynchronously.

        Args:
            host: Hostname string.

        Returns:
            List of resolved IP address strings.
        """
        # If the input is already a valid IP, bypass DNS lookup
        try:
            ipaddress.ip_address(host)
            return [host]
        except ValueError:
            pass

        loop = asyncio.get_running_loop()
        try:
            addrinfo = await loop.getaddrinfo(host, None)
            ips = list({info[4][0] for info in addrinfo})
            logger.debug(f"Resolved hostname '{host}' to IPs: {ips}")
            return ips
        except socket.gaierror as e:
            logger.warning(f"DNS Resolution failed for host '{host}': {e}")
            return []

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Execute an async HTTP request, validating the target IP.

        Args:
            method: HTTP verb (GET, POST, etc.).
            url: Target URL string.
            kwargs: Extra parameters passed to HTTPX.

        Returns:
            The HTTPX Response object.

        Raises:
            SecurityException: If target URL resolves to blocked IP ranges.
        """
        url_parts = httpx.URL(url)
        host = url_parts.host
        if not host:
            raise ValueError(f"Invalid URL structure: '{url}'")

        ips = await self._resolve_host(host)
        if not ips:
            raise socket.gaierror(f"Could not resolve host '{host}'")

        if not self.allow_private_ips:
            for ip in ips:
                if is_private_ip(ip):
                    logger.error(
                        "SSRF Protection blocked request to private target IP %s for host '%s'",
                        ip,
                        host,
                    )
                    raise SecurityException(
                        f"SSRF Protection: Access to private IP range '{ip}' is blocked."
                    )

        logger.debug(f"Executing secure request: {method} {url}")
        return await self._client.request(method, url, **kwargs)

    async def check_ssl(self, host: str, port: int = 443) -> dict[str, Any]:
        """Execute an async TLS handshake and parse peer certificate metadata.

        Args:
            host: Target hostname.
            port: Port to connect on. Default: 443.

        Returns:
            Dictionary containing TLS and certificate metadata.

        Raises:
            SecurityException: If target host resolves to private IP addresses.
        """
        ips = await self._resolve_host(host)
        if not ips:
            raise socket.gaierror(f"Could not resolve host '{host}'")

        if not self.allow_private_ips:
            for ip in ips:
                if is_private_ip(ip):
                    logger.error(
                        "SSRF Protection blocked SSL check to private target IP %s for host '%s'",
                        ip,
                        host,
                    )
                    raise SecurityException(
                        f"SSRF Protection: Access to private IP range '{ip}' is blocked."
                    )

        context = ssl.create_default_context()

        try:
            # Connect asynchronously using socket connection
            _reader, writer = await asyncio.open_connection(
                host, port, ssl=context, server_hostname=host
            )
        except Exception as e:
            logger.warning(f"SSL Handshake failed on {host}:{port}: {e}")
            return {"error": str(e), "valid": False}

        try:
            transport = writer.transport
            ssl_socket = transport.get_extra_info("ssl_object")
            if not ssl_socket:
                return {"error": "Failed to retrieve SSL context object", "valid": False}

            cert_der = ssl_socket.getpeercert(binary_form=True)
            if not cert_der:
                return {"error": "Failed to retrieve binary peer certificate", "valid": False}

            # Parse DER-formatted certificate
            cert = x509.load_der_x509_certificate(cert_der, default_backend())

            # Map subject and issuer properties
            subject = {name.oid._name: name.value for name in cert.subject}
            issuer = {name.oid._name: name.value for name in cert.issuer}

            # Fallback for old cryptography versions lacking UTC properties
            if hasattr(cert, "not_valid_after_utc"):
                expiry = cert.not_valid_after_utc
                not_before = cert.not_valid_before_utc
            else:
                expiry = cert.not_valid_after.replace(tzinfo=UTC)
                not_before = cert.not_valid_before.replace(tzinfo=UTC)

            valid = expiry > datetime.now(UTC)

            return {
                "subject": subject,
                "issuer": issuer,
                "expiry_date": expiry.isoformat(),
                "not_before": not_before.isoformat(),
                "serial_number": str(cert.serial_number),
                "valid": valid,
                "version": cert.version.name,
            }

        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()

    async def close(self) -> None:
        """Close connection pools and clean up clients."""
        await self._client.aclose()
        logger.debug("Closed AsyncNetworkClient connection pools.")
