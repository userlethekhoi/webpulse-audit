"""Unit and integration tests for WebPulse built-in analyzer plugins."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from webpulse.modules.http.plugin import HttpPlugin
from webpulse.modules.security.plugin import SecurityPlugin
from webpulse.modules.seo.plugin import SeoPlugin
from webpulse.modules.ssl.plugin import SslPlugin
from webpulse.reports.schemas import Severity, Target
from webpulse.utils.network import AsyncNetworkClient


@pytest.mark.asyncio
@respx.mock
async def test_http_analyzer_success() -> None:
    """Verify HTTP analyzer handles a perfect compressed HTTP/2 response with no findings."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    respx.get("https://example.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"Content-Encoding": "br"},
            extensions={"http_version": b"HTTP/2"},
        )
    )

    plugin = HttpPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    # 0 findings expected since it has Brotli compression, HTTP/2, and 200 OK status
    assert len(findings) == 0
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_http_analyzer_deficiencies() -> None:
    """Verify HTTP analyzer flags uncompressed HTTP/1.1 connection and server errors."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    # 1. Uncompressed HTTP/1.1 response
    respx.get("https://example.com/uncompressed").mock(
        return_value=httpx.Response(200, extensions={"http_version": b"HTTP/1.1"})
    )

    plugin = HttpPlugin()
    target = Target(url="https://example.com/uncompressed")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "HTTP Compression Disabled" in titles
    assert "HTTP/2 Protocol Not Supported" in titles

    # 2. Server Error status code response
    respx.get("https://example.com/error").mock(
        return_value=httpx.Response(503, extensions={"http_version": b"HTTP/2"})
    )
    target_err = Target(url="https://example.com/error")
    findings_err = await plugin.execute(target_err, client)

    titles_err = [f.title for f in findings_err]
    assert "Server Response Error Code Returned" in titles_err
    await client.close()


@pytest.mark.asyncio
async def test_ssl_analyzer_expiring_soon() -> None:
    """Verify SSL analyzer detects certificates expiring soon."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    expiry = datetime.now(UTC) + timedelta(days=5)
    mock_cert_info = {
        "valid": True,
        "expiry_date": expiry.isoformat(),
        "subject": {"CN": "example.com"},
        "issuer": {"O": "Let's Encrypt"},
        "serial_number": "12345",
    }
    client.check_ssl = AsyncMock(return_value=mock_cert_info)  # type: ignore

    plugin = SslPlugin()
    # Configure custom verification threshold of 10 days
    await plugin.on_load({"verify_expiry_days": 10})

    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    assert len(findings) == 1
    assert findings[0].title == "SSL Certificate Expiring Soon"
    assert findings[0].severity == Severity.HIGH
    await client.close()


@pytest.mark.asyncio
async def test_ssl_analyzer_expired() -> None:
    """Verify SSL analyzer flags invalid/expired certificates."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    mock_cert_info = {
        "valid": False,
        "expiry_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    }
    client.check_ssl = AsyncMock(return_value=mock_cert_info)  # type: ignore

    plugin = SslPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    assert len(findings) == 1
    assert findings[0].title == "SSL Certificate Expired or Invalid"
    assert findings[0].severity == Severity.CRITICAL
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_seo_analyzer_violations() -> None:
    """Verify SEO analyzer spots title, description, h1 headings, and canonical violations."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    html_content = """
    <html>
      <head>
        <title>Short</title>
      </head>
      <body>
        <h1>Heading 1</h1>
        <h1>Duplicate Heading 1</h1>
        <img src="logo.png" />
      </body>
    </html>
    """
    respx.get("https://example.com/seo-fail").mock(
        return_value=httpx.Response(200, html=html_content)
    )

    plugin = SeoPlugin()
    target = Target(url="https://example.com/seo-fail")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "Page Title Length Out of Optimal Bounds" in titles
    assert "Missing Meta Description Header" in titles
    assert "Duplicate H1 Headings Detected" in titles
    assert "Images Missing Alt Attributes" in titles
    assert "Missing Canonical Link Reference" in titles
    await client.close()


@pytest.mark.asyncio
@respx.mock
async def test_security_analyzer_exposed_files() -> None:
    """Verify security analyzer flags missing security headers and exposed configuration files."""
    client = AsyncNetworkClient(allow_private_ips=True)
    client._resolve_host = AsyncMock(return_value=["127.0.0.1"])  # type: ignore

    # 1. Main request: returns index page but lacks CSP, HSTS, X-Frame-Options, nosniff
    respx.get("https://example.com/").mock(
        return_value=httpx.Response(
            200,
            headers={"Set-Cookie": "session=secret"},
        )
    )

    # 2. Exposed Git endpoint probe
    respx.get("https://example.com/.git/HEAD").mock(
        return_value=httpx.Response(200, text="ref: refs/heads/main")
    )

    # 3. Exposed .env file probe
    respx.get("https://example.com/.env").mock(
        return_value=httpx.Response(200, text="DB_PASSWORD=secret_db_pass\nPORT=80")
    )

    plugin = SecurityPlugin()
    target = Target(url="https://example.com/")
    findings = await plugin.execute(target, client)

    titles = [f.title for f in findings]
    assert "Missing Content-Security-Policy Header" in titles
    assert "Missing Strict-Transport-Security Header" in titles
    assert "Missing Anti-Clickjacking Header" in titles
    assert "Missing or Invalid X-Content-Type-Options Header" in titles
    assert "Insecure Cookie Flags Detected" in titles
    assert "Exposed Git Repository Directory Detected" in titles
    assert "Exposed System Environment File Detected" in titles
    await client.close()
