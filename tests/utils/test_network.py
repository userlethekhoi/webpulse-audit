"""Unit tests for the AsyncNetworkClient and SSRF blocker."""

from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from webpulse.core.exceptions import SecurityException
from webpulse.utils.network import AsyncNetworkClient, is_private_ip


def test_is_private_ip_detection() -> None:
    """Verify that is_private_ip catches loopback, private, and local addresses."""
    # Loopback
    assert is_private_ip("127.0.0.1") is True
    assert is_private_ip("::1") is True

    # RFC 1918
    assert is_private_ip("10.0.0.1") is True
    assert is_private_ip("172.16.0.25") is True
    assert is_private_ip("192.168.1.100") is True

    # Link-local / reserved
    assert is_private_ip("169.254.169.254") is True
    assert is_private_ip("0.0.0.0") is True  # noqa: S104

    # Public IPv4 / IPv6 (Safe)
    assert is_private_ip("8.8.8.8") is False
    assert is_private_ip("104.244.42.1") is False
    assert is_private_ip("2606:4700:20::681a:2b0") is False

    # Invalid IPs
    assert is_private_ip("invalid-ip") is True


@pytest.mark.asyncio
async def test_request_ssrf_default_blocking() -> None:
    """Verify requests to private IP ranges are blocked by default."""
    client = AsyncNetworkClient(allow_private_ips=False)
    # Mock DNS resolution to return private IP
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    with pytest.raises(SecurityException) as exc_info:
        await client.request("GET", "http://localhost/status")

    assert "SSRF Protection" in str(exc_info.value)
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_request_ssrf_bypass() -> None:
    """Verify requests to private IP ranges are allowed if allow_private_ips=True."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    # Mock local HTTP request using respx
    respx.get("http://localhost/status").mock(return_value=httpx.Response(200, text="local-data"))

    response = await client.request("GET", "http://localhost/status")
    assert response.status_code == 200
    assert response.text == "local-data"
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_request_public_destination() -> None:
    """Verify that requests to public destinations pass without exceptions."""
    client = AsyncNetworkClient(allow_private_ips=False)
    client._resolve_host = AsyncMock(return_value=["8.8.8.8"])  # type: ignore

    respx.get("https://dns.google/resolve").mock(
        return_value=httpx.Response(200, text="dns-response")
    )

    response = await client.request("GET", "https://dns.google/resolve")
    assert response.status_code == 200
    assert response.text == "dns-response"
    await client.close()


@pytest.mark.asyncio
async def test_check_ssl_ssrf_blocking() -> None:
    """Verify SSL checks to private IP addresses are blocked by default."""
    client = AsyncNetworkClient(allow_private_ips=False)
    client._resolve_host = AsyncMock(return_value=["192.168.1.1"])  # type: ignore

    with pytest.raises(SecurityException) as exc_info:
        await client.check_ssl("intranet.local", port=443)

    assert "SSRF Protection" in str(exc_info.value)
    await client.close()


@pytest.mark.asyncio
async def test_check_ssl_connection_failure() -> None:
    """Verify check_ssl returns a valid=False dictionary on connection failure."""
    client = AsyncNetworkClient(allow_private_ips=False)
    client._resolve_host = AsyncMock(return_value=["8.8.8.8"])  # type: ignore

    # Mock asyncio.open_connection to fail
    with patch("asyncio.open_connection", side_effect=ConnectionRefusedError("Refused")):
        result = await client.check_ssl("dns.google", port=443)

    assert result["valid"] is False
    assert "Refused" in result["error"]
    await client.close()
